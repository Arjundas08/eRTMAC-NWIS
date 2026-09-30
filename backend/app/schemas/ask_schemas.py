from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class AskNWISRequest(BaseModel):
    query: str
    active_well_id: Optional[str] = None
    target_formation: Optional[str] = None
    depth_tvdss_m: Optional[float] = None
    search_radius_km: float = 10.0

class EvidenceCitation(BaseModel):
    source_document: str
    well_id: str
    depth_interval: str
    formation_name: str
    excerpt: str
    confidence_score: float

class AskNWISResponse(BaseModel):
    query: str
    grounded_answer: str
    confidence_level: str # HIGH, MEDIUM, LOW, INSUFFICIENT_DATA
    citations: List[EvidenceCitation]
    missing_data_warnings: List[str]
    has_sufficient_evidence: bool
