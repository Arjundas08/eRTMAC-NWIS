"""
Evidence Passport Service.
Constructs source-verifiable evidence dossiers answering the 8 mandatory engineering verification questions.
Provides deterministic citation linking and page highlight rendering.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from backend.app.db.models import DrillingEvent, EventEvidence, Document, DocumentPage, Well
from backend.app.schemas.evidence_schemas import EvidencePassport
from backend.app.services.ocr_service import ocr_service

PROCESSED_PAGES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "documents" / "processed"

class EvidenceService:
    def get_evidence_passport(self, event_id: str, db: Session) -> Optional[EvidencePassport]:
        """
        Builds a comprehensive Evidence Passport answering the 8 mandatory engineering questions.
        """
        event = db.query(DrillingEvent).filter(DrillingEvent.event_id == event_id).first()
        if not event:
            return None

        # Fetch associated evidence record if available
        evidence = db.query(EventEvidence).filter(EventEvidence.event_id == event_id).first()
        well = db.query(Well).filter(Well.well_id == event.well_id).first()
        doc = db.query(Document).filter(Document.doc_id == event.doc_id).first() if event.doc_id else None

        # Determine supporting passage and bounding box
        quoted_passage = evidence.quoted_passage if evidence else event.operational_narrative
        source_doc_name = doc.original_filename if doc else event.source_citation.split(",")[0].strip()
        source_page_num = evidence.page_number if evidence else (event.page_number or 1)
        bbox = json.loads(evidence.bbox_json) if (evidence and evidence.bbox_json) else None

        # Identify missing fields
        missing_fields = []
        if not event.depth_md_m or event.depth_md_m <= 0:
            missing_fields.append("Measured Depth (MD)")
        if not event.formation_name or event.formation_name == "Unknown":
            missing_fields.append("Stratigraphic Formation Pick")
        if not event.mitigation_applied:
            missing_fields.append("Recorded Mitigation Action")
        if not event.event_timestamp:
            missing_fields.append("Precise Event Timestamp")

        # Direct link or API endpoint to preview the highlighted page
        direct_pdf_url = f"/api/v1/documents/{event.doc_id}/pages/{source_page_num}/preview" if event.doc_id else None

        return EvidencePassport(
            event_id=event.event_id,
            hazard_type=event.event_type,
            severity=event.severity,
            operational_narrative=event.operational_narrative,
            mitigation_applied=event.mitigation_applied,
            npt_hours=event.npt_hours,
            well_id=event.well_id,
            well_name=well.well_name if well else event.well_id,
            field_name=well.field_name if well else "Volve (PL 046)",
            operator=well.operator if well else "Equinor",
            event_timestamp=event.event_timestamp,
            source_availability_timestamp=event.source_availability_timestamp or event.event_timestamp,
            depth_md_m=event.depth_md_m,
            depth_tvdss_m=event.depth_tvdss_m,
            depth_datum="TVDSS (MSL, RKB 43.5m)",
            formation_name=event.formation_name,
            relative_formation_depth_m=event.relative_formation_depth_m,
            source_document_name=source_doc_name,
            doc_id=event.doc_id,
            source_page_number=source_page_num,
            quoted_passage=quoted_passage,
            bounding_box=bbox,
            source_citation=event.source_citation,
            missing_fields=missing_fields,
            verification_status=event.verification_status,
            extraction_method=event.extraction_method,
            confidence_score=event.confidence_score,
            reviewed_by=event.reviewed_by,
            reviewed_at=event.reviewed_at,
            direct_pdf_page_url=direct_pdf_url
        )

    def render_highlighted_passage_image(self, doc_id: str, page_number: int, db: Session) -> Optional[str]:
        """
        Renders the document page with the highlighted bounding box over the evidence passage.
        """
        doc = db.query(Document).filter(Document.doc_id == doc_id).first()
        if not doc or not Path(doc.file_path).exists():
            return None

        # Look for evidence on this page
        evidence = db.query(EventEvidence).filter(
            EventEvidence.doc_id == doc_id,
            EventEvidence.page_number == page_number
        ).first()

        bbox = json.loads(evidence.bbox_json) if (evidence and evidence.bbox_json) else None

        target_render_path = PROCESSED_PAGES_DIR / f"highlight_{doc_id}_p{page_number}.png"
        return ocr_service.render_page_with_highlight(
            pdf_path=doc.file_path,
            page_number=page_number,
            bbox=bbox,
            target_image_path=str(target_render_path)
        )

evidence_service = EvidenceService()
