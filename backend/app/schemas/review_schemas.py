from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ReviewTaskItem(BaseModel):
    task_id: str
    doc_id: str
    original_filename: str
    event_id: Optional[str] = None
    status: str # PENDING, IN_REVIEW, RESOLVED, REJECTED
    flag_reason: str
    page_number: Optional[int] = None
    original_payload: Dict[str, Any]
    created_at: datetime

class ReviewDecisionRequest(BaseModel):
    task_id: str
    reviewer_id: str = "OIL-CHIEF-DRILLER-01"
    reviewer_role: str = "DRILLING_SUPERINTENDENT"
    decision: str # APPROVED, REJECTED, MODIFIED
    corrections: Optional[Dict[str, Any]] = None
    comments: Optional[str] = None

class ReviewDecisionResponse(BaseModel):
    decision_id: str
    task_id: str
    decision: str
    verification_status: str
    message: str
    audit_logged: bool
