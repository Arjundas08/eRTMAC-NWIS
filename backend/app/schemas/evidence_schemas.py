from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class EvidencePassport(BaseModel):
    # WHAT HAPPENED?
    event_id: str
    hazard_type: str
    severity: str
    operational_narrative: str
    mitigation_applied: Optional[str] = None
    npt_hours: float = 0.0

    # WHICH WELLBORE EXPERIENCED IT?
    well_id: str
    well_name: str
    field_name: str
    operator: str

    # WHEN DID IT HAPPEN?
    event_timestamp: Optional[str] = None
    source_availability_timestamp: Optional[str] = None

    # AT WHAT DEPTH?
    depth_md_m: float
    depth_tvdss_m: float
    depth_datum: str = "TVDSS (MSL)"

    # WHICH GEOLOGICAL INTERVAL?
    formation_name: str
    relative_formation_depth_m: Optional[float] = None

    # WHAT DOES THE ORIGINAL REPORT SAY?
    source_document_name: str
    doc_id: Optional[str] = None
    source_page_number: int
    quoted_passage: str
    bounding_box: Optional[List[float]] = None
    source_citation: str

    # WHAT INFORMATION IS MISSING?
    missing_fields: List[str] = []

    # HAS THE RECORD BEEN VERIFIED?
    verification_status: str # VERIFIED, PENDING_REVIEW, CONFLICTING_EVIDENCE, INSUFFICIENT_SOURCE, REJECTED
    extraction_method: str
    confidence_score: float
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    # DIRECT LINK/PREVIEW
    direct_pdf_page_url: Optional[str] = None
