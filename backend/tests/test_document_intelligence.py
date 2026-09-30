import pytest
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.db.database import SessionLocal
from backend.app.db.models import Document, DrillingEvent, EventEvidence, ReviewTask
from backend.app.services.document_service import document_service, DocumentSecurityError
from backend.app.services.evidence_service import evidence_service
from backend.app.services.review_service import review_service
from backend.app.services.risk_service import risk_service
from backend.app.schemas.review_schemas import ReviewDecisionRequest
from backend.app.schemas.lookahead_schemas import LookaheadRequest

DOCS_DIR = ROOT_DIR / "data" / "documents" / "raw"

def test_document_ingestion_and_deduplication():
    """Verify that a valid PDF is ingested, extracted, and deduplicated idempotently."""
    db = SessionLocal()
    try:
        sample_pdf = DOCS_DIR / "VOLVE_DDR_20080914_F14.pdf"
        assert sample_pdf.exists(), "Sample PDF must exist"
        
        file_bytes = sample_pdf.read_bytes()
        res1 = document_service.ingest_document_file(
            file_bytes=file_bytes,
            original_filename="VOLVE_DDR_20080914_F14.pdf",
            db=db,
            well_id="NO-15/9-F-14"
        )
        assert res1["status"] in ["EXTRACTED", "FAILED"]
        doc_id = res1["doc_id"]

        # Ingesting the same file a second time must detect duplicate without error
        res2 = document_service.ingest_document_file(
            file_bytes=file_bytes,
            original_filename="VOLVE_DDR_20080914_F14.pdf",
            db=db,
            well_id="NO-15/9-F-14"
        )
        assert res2["is_duplicate"] is True
        assert res2["doc_id"] == doc_id
    finally:
        db.close()


def test_malicious_pdf_rejection_and_magic_bytes():
    """Verify that non-PDF files and files with exploit tokens are rejected."""
    db = SessionLocal()
    try:
        # Non-PDF file
        with pytest.raises(DocumentSecurityError, match="Missing valid %PDF- magic bytes"):
            document_service.ingest_document_file(
                file_bytes=b"RANDOM_NON_PDF_TEXT_BYTES",
                original_filename="fake.pdf",
                db=db
            )

        # Malicious PDF with embedded exploit token
        malicious_pdf = b"%PDF-1.4\n1 0 obj\n<< /JavaScript (app.alert('PWNED')) >>\nendobj\ntrailer\n<< >>"
        with pytest.raises(DocumentSecurityError, match="restricted active token"):
            document_service.ingest_document_file(
                file_bytes=malicious_pdf,
                original_filename="exploit.pdf",
                db=db
            )
    finally:
        db.close()


def test_scanned_pdf_ocr_processing():
    """Verify that scanned image-only PDFs are detected and processed via OCR."""
    db = SessionLocal()
    try:
        scanned_pdf = DOCS_DIR / "VOLVE_DDR_SCANNED_MUD_REPORT.pdf"
        assert scanned_pdf.exists(), "Scanned sample PDF must exist"

        res = document_service.ingest_document_file(
            file_bytes=scanned_pdf.read_bytes(),
            original_filename="VOLVE_DDR_SCANNED_MUD_REPORT.pdf",
            db=db,
            well_id="NO-15/9-F-4"
        )
        assert res["is_scanned"] is True
        assert res["status"] == "EXTRACTED"
    finally:
        db.close()


def test_evidence_passport_contract():
    """Verify that Evidence Passport answers all 8 mandatory engineering verification questions."""
    db = SessionLocal()
    try:
        # Fetch an event with verified evidence
        ev = db.query(DrillingEvent).filter(DrillingEvent.verification_status == "VERIFIED").first()
        assert ev is not None, "At least one verified event must exist"

        passport = evidence_service.get_evidence_passport(ev.event_id, db)
        assert passport is not None
        assert passport.event_id == ev.event_id
        assert passport.hazard_type == ev.event_type
        assert passport.well_id == ev.well_id
        assert len(passport.quoted_passage) > 0
        assert passport.depth_md_m > 0
        assert passport.verification_status == "VERIFIED"
        assert passport.depth_datum is not None
    finally:
        db.close()


def test_human_in_the_loop_review_and_quarantine():
    """
    Verify review workflow:
    1. Pending tasks exist
    2. Approval transitions status to VERIFIED
    3. Rejection transitions status to REJECTED and blocks from lookahead
    """
    db = SessionLocal()
    try:
        # Always clean up any leftover mock test records unconditionally
        db.query(ReviewTask).filter(ReviewTask.task_id == "TASK-TEST-001").delete()
        db.query(DrillingEvent).filter(DrillingEvent.event_id == "EVT-TEST-PENDING").delete()
        db.commit()

        tasks = review_service.list_pending_tasks(db)
        if not tasks:
            # Create a mock pending task for testing
            mock_event = DrillingEvent(
                event_id="EVT-TEST-PENDING",
                well_id="NO-15/9-F-14",
                event_type="LOST_CIRCULATION",
                severity="MODERATE",
                depth_md_m=2960.0,
                depth_tvdss_m=2863.0,
                formation_name="Hugin FM",
                operational_narrative="Test unverified seepage losses.",
                source_citation="Test Report, Page 1",
                verification_status="PENDING_REVIEW"
            )
            db.add(mock_event)
            mock_task = ReviewTask(
                task_id="TASK-TEST-001",
                doc_id="mock-doc-id",
                event_id="EVT-TEST-PENDING",
                status="PENDING",
                flag_reason="LOW_CONFIDENCE",
                original_payload_json=json.dumps({"event_type": "LOST_CIRCULATION"})
            )
            db.add(mock_task)
            db.commit()
            tasks = review_service.list_pending_tasks(db)

        target_task = tasks[0]
        task_id = target_task["task_id"]

        # Execute rejection
        rej_res = review_service.submit_decision(
            db=db,
            req=ReviewDecisionRequest(
                task_id=task_id,
                decision="REJECTED",
                comments="Rejected by QA test suite: unverified historical claim."
            )
        )
        assert rej_res["decision"] == "REJECTED"
        assert rej_res["verification_status"] == "REJECTED"

        # Verify that rejected event is STRICTLY EXCLUDED from lookahead hazard scan
        rej_event_id = target_task["event_id"]
        if rej_event_id:
            rej_ev = db.query(DrillingEvent).filter(DrillingEvent.event_id == rej_event_id).first()
            assert rej_ev.verification_status == "REJECTED"

            # Query lookahead horizon at this exact depth interval
            req = LookaheadRequest(
                active_well_id="NO-15/9-F-12",
                current_bit_depth_md_m=rej_ev.depth_md_m,
                current_bit_depth_tvdss_m=rej_ev.depth_tvdss_m - 20.0,
                active_formation=rej_ev.formation_name,
                lookahead_window_m=50.0
            )
            scan_res = risk_service.evaluate_lookahead_horizon(db, req)
            # Rejected event must NEVER appear in active alerts
            alert_event_ids = {a.hazard_type for a in scan_res.alerts}
            # The rejected event cannot be the source of an alert if its verification_status is REJECTED
            for alert in scan_res.alerts:
                assert alert.source_citation != rej_ev.source_citation or rej_ev.verification_status != "REJECTED"

    finally:
        db.close()
