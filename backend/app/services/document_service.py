"""
Production Document Intelligence and Ingestion Pipeline Service.
Implements:
- Magic bytes and malicious PDF validation
- SHA-256 hashing and idempotent deduplication
- PyMuPDF text & layout processing
- Event extraction and evidence linking
- Human-in-the-loop review routing
- Audit event logging
"""

import os
import hashlib
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.db.models import (
    Document, DocumentPage, DocumentVersion, ExtractionJob,
    ExtractedEntity, DrillingEvent, EventEvidence, ReviewTask, AuditEvent
)
from backend.app.services.ocr_service import ocr_service
from backend.app.services.event_extractor_service import event_extractor_service

STORAGE_RAW_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "documents" / "raw"
STORAGE_QUARANTINE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "documents" / "quarantine"
STORAGE_RAW_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

class DocumentSecurityError(Exception):
    pass

class DocumentService:
    def __init__(self):
        self.raw_dir = STORAGE_RAW_DIR
        self.quarantine_dir = STORAGE_QUARANTINE_DIR
        self.max_file_size = 50 * 1024 * 1024  # 50 MB limit

    def ingest_document_file(
        self,
        file_bytes: bytes,
        original_filename: str,
        db: Session,
        well_id: Optional[str] = None,
        source_id: Optional[str] = "SRC-VOLVE-001",
        user_id: str = "SYS-INGESTION-DAEMON"
    ) -> Dict[str, Any]:
        """
        Executes end-to-end ingestion pipeline:
        Validate -> Checksum -> Deduplicate -> OCR -> Extract -> Link Evidence -> Route Review
        """
        # 1. Security & File Validation
        if len(file_bytes) > self.max_file_size:
            raise DocumentSecurityError(f"File size exceeds safety limit of 50MB ({len(file_bytes)} bytes)")

        # Magic bytes check for PDF
        if not file_bytes.startswith(b"%PDF-"):
            raise DocumentSecurityError("File signature verification failed: Missing valid %PDF- magic bytes")

        # Scan for potentially malicious PDF exploit structures
        lower_bytes = file_bytes.lower()
        malicious_tokens = [b"/javascript", b"/launch", b"/embeddedfiles"]
        for token in malicious_tokens:
            if token in lower_bytes:
                # Quarantine malicious file
                q_path = self.quarantine_dir / f"MALICIOUS_{uuid.uuid4()}_{original_filename}"
                with open(q_path, "wb") as f:
                    f.write(file_bytes)
                raise DocumentSecurityError(f"Security Alert: Document contains restricted active token '{token.decode()}'. Quarantined to {q_path.name}.")

        # 2. Checksum generation & Deduplication (Idempotency)
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()
        existing_doc = db.query(Document).filter(Document.sha256_hash == sha256_hash).first()

        if existing_doc:
            return {
                "doc_id": existing_doc.doc_id,
                "original_filename": existing_doc.original_filename,
                "sha256_hash": sha256_hash,
                "file_size_bytes": existing_doc.file_size_bytes,
                "mime_type": existing_doc.mime_type,
                "well_id": existing_doc.well_id,
                "document_type": existing_doc.document_type,
                "source_date": existing_doc.source_date,
                "total_pages": existing_doc.total_pages,
                "is_scanned": existing_doc.is_scanned,
                "status": existing_doc.status,
                "is_duplicate": True,
                "message": f"Document already ingested on {existing_doc.created_at.strftime('%Y-%m-%d')}. Idempotent duplicate safely preserved."
            }

        # 3. Secure Document Storage
        doc_id = str(uuid.uuid4())
        safe_filename = f"{sha256_hash[:12]}_{original_filename.replace(' ', '_')}"
        saved_file_path = self.raw_dir / safe_filename
        with open(saved_file_path, "wb") as f:
            f.write(file_bytes)

        # 4. Create Document and ExtractionJob Records
        doc_record = Document(
            doc_id=doc_id,
            original_filename=original_filename,
            file_path=str(saved_file_path),
            sha256_hash=sha256_hash,
            file_size_bytes=len(file_bytes),
            mime_type="application/pdf",
            document_type="DAILY_DRILLING_REPORT",
            well_id=well_id,
            source_id=source_id,
            status="PROCESSING"
        )
        db.add(doc_record)

        job = ExtractionJob(
            job_id=str(uuid.uuid4()),
            doc_id=doc_id,
            status="RUNNING",
            started_at=datetime.now(timezone.utc)
        )
        db.add(job)
        db.commit()

        # 5. Execute OCR and Layout Understanding
        try:
            extraction_result = ocr_service.inspect_and_extract_pdf(str(saved_file_path))
            total_pages = extraction_result["total_pages"]
            is_scanned = extraction_result["is_scanned"]

            doc_record.total_pages = total_pages
            doc_record.is_scanned = is_scanned

            detected_well_id = well_id
            detected_source_date = None
            total_incidents_created = 0

            for p in extraction_result["pages"]:
                page_record = DocumentPage(
                    doc_id=doc_id,
                    page_number=p["page_number"],
                    raw_text=p["raw_text"],
                    is_scanned=p["is_scanned"],
                    ocr_applied=p["ocr_applied"],
                    ocr_confidence=p["ocr_confidence"],
                    image_path=p["image_path"],
                    layout_json=json.dumps(p["layout_blocks"])
                )
                db.add(page_record)

                # 6. Structured Engineering Extraction
                extracted = event_extractor_service.extract_from_page(
                    page_text=p["raw_text"],
                    page_number=p["page_number"],
                    layout_blocks=p["layout_blocks"]
                )

                if extracted["well_id"] and not detected_well_id:
                    detected_well_id = extracted["well_id"]
                if extracted["report_date"] and not detected_source_date:
                    detected_source_date = extracted["report_date"]

                # Save extracted entities
                for ent in extracted["entities"]:
                    db.add(ExtractedEntity(
                        doc_id=doc_id,
                        page_number=p["page_number"],
                        entity_type=ent["entity_type"],
                        entity_key=ent["entity_key"],
                        extracted_value=str(ent["extracted_value"]),
                        normalized_value=ent.get("normalized_value"),
                        unit=ent.get("unit"),
                        confidence=ent.get("confidence", 1.0),
                        text_passage=ent.get("text_passage")
                    ))

                # 7. Create Historical Events & Event Evidence
                for inc in extracted["incidents"]:
                    event_id = f"EVT-DOC-{uuid.uuid4().hex[:8].upper()}"
                    eff_well = detected_well_id or well_id or "NO-15/9-F-14"
                    conf = inc["confidence_score"]
                    is_confident = (conf >= 0.85 and len(inc["missing_fields"]) == 0)
                    verification_status = "VERIFIED" if is_confident else "PENDING_REVIEW"

                    drilling_event = DrillingEvent(
                        event_id=event_id,
                        well_id=eff_well,
                        event_type=inc["event_type"],
                        severity=inc["severity"],
                        depth_md_m=inc["depth_md_m"],
                        depth_tvdss_m=inc["depth_tvdss_m"],
                        formation_name=inc["formation_name"],
                        relative_formation_depth_m=4.0,
                        npt_hours=inc["npt_hours"],
                        operational_narrative=inc["operational_narrative"],
                        mitigation_applied=inc["mitigation_applied"],
                        source_citation=f"{original_filename}, Page {p['page_number']}",
                        event_timestamp=f"{detected_source_date}T06:00:00Z" if detected_source_date else None,
                        verification_status=verification_status,
                        doc_id=doc_id,
                        page_number=p["page_number"],
                        extraction_method="OCR_LAYOUT_EXTRACT" if is_scanned else "NATIVE_PDF_EXTRACT",
                        confidence_score=conf
                    )
                    db.add(drilling_event)

                    evidence = EventEvidence(
                        evidence_id=str(uuid.uuid4()),
                        event_id=event_id,
                        doc_id=doc_id,
                        page_number=p["page_number"],
                        quoted_passage=inc["operational_narrative"],
                        bbox_json=json.dumps(inc["bounding_box"]) if inc["bounding_box"] else None,
                        extraction_method="OCR_LAYOUT_EXTRACT" if is_scanned else "NATIVE_PDF_EXTRACT",
                        confidence_score=conf,
                        evidence_status=verification_status,
                        missing_fields_json=json.dumps(inc["missing_fields"])
                    )
                    db.add(evidence)
                    total_incidents_created += 1

                    # 8. Human Review Routing if not fully confident
                    if not is_confident:
                        db.add(ReviewTask(
                            task_id=str(uuid.uuid4()),
                            doc_id=doc_id,
                            event_id=event_id,
                            evidence_id=evidence.evidence_id,
                            status="PENDING",
                            flag_reason="LOW_CONFIDENCE_OR_MISSING_DEPTH" if inc["missing_fields"] else "UNPRECEDENTED_HAZARD",
                            original_payload_json=json.dumps(inc)
                        ))

            # Finalize Document and Job Status
            doc_record.well_id = detected_well_id or well_id
            doc_record.source_date = detected_source_date
            doc_record.status = "EXTRACTED"
            job.status = "COMPLETED"
            job.completed_at = datetime.now(timezone.utc)

            # Audit event
            db.add(AuditEvent(
                user_id=user_id,
                action="DOCUMENT_INGESTION_COMPLETED",
                resource_type="document",
                resource_id=doc_id,
                details_json=json.dumps({
                    "filename": original_filename,
                    "sha256": sha256_hash,
                    "total_pages": total_pages,
                    "events_extracted": total_incidents_created,
                    "well_id": doc_record.well_id
                })
            ))
            db.commit()

            return {
                "doc_id": doc_id,
                "original_filename": original_filename,
                "sha256_hash": sha256_hash,
                "file_size_bytes": len(file_bytes),
                "mime_type": "application/pdf",
                "well_id": doc_record.well_id,
                "document_type": doc_record.document_type,
                "source_date": detected_source_date,
                "total_pages": total_pages,
                "is_scanned": is_scanned,
                "status": "EXTRACTED",
                "is_duplicate": False,
                "message": f"Successfully ingested {original_filename} ({total_pages} pages, {total_incidents_created} incidents extracted)."
            }

        except Exception as e:
            db.rollback()
            job.status = "FAILED"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            doc_record.status = "FAILED"
            db.commit()
            raise e

    def get_document_details(self, doc_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """Retrieves comprehensive details for a document including pages and extracted entities."""
        doc = db.query(Document).filter(Document.doc_id == doc_id).first()
        if not doc:
            return None

        pages = db.query(DocumentPage).filter(DocumentPage.doc_id == doc_id).order_by(DocumentPage.page_number).all()
        entities = db.query(ExtractedEntity).filter(ExtractedEntity.doc_id == doc_id).all()

        return {
            "doc_id": doc.doc_id,
            "original_filename": doc.original_filename,
            "sha256_hash": doc.sha256_hash,
            "file_size_bytes": doc.file_size_bytes,
            "document_type": doc.document_type,
            "well_id": doc.well_id,
            "source_id": doc.source_id,
            "source_date": doc.source_date,
            "source_url": doc.source_url,
            "total_pages": doc.total_pages,
            "is_scanned": doc.is_scanned,
            "status": doc.status,
            "created_at": doc.created_at,
            "pages": [
                {
                    "page_number": p.page_number,
                    "is_scanned": p.is_scanned,
                    "ocr_applied": p.ocr_applied,
                    "ocr_confidence": p.ocr_confidence,
                    "text_preview": p.raw_text[:200] + "..." if len(p.raw_text) > 200 else p.raw_text,
                    "entity_count": len([e for e in entities if e.page_number == p.page_number])
                }
                for p in pages
            ],
            "entities": [
                {
                    "entity_type": e.entity_type,
                    "entity_key": e.entity_key,
                    "extracted_value": e.extracted_value,
                    "normalized_value": e.normalized_value,
                    "unit": e.unit,
                    "confidence": e.confidence,
                    "bbox": json.loads(e.bbox_json) if e.bbox_json else None,
                    "text_passage": e.text_passage
                }
                for e in entities
            ]
        }

document_service = DocumentService()
