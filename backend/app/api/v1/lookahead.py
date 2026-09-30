from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...db.database import get_db
from ...schemas.lookahead_schemas import (
    LookaheadRequest, LookaheadResponse, DrillerFeedbackRequest
)
from ...services.risk_service import risk_service
from ...core.security import get_current_user

router = APIRouter(prefix="/lookahead", tags=["Pre-Bit Look-Ahead Horizon Engine"])

@router.post("/scan", response_model=LookaheadResponse)
def scan_lookahead_horizon_endpoint(
    request: LookaheadRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Evaluates historical offset hazards in the upcoming 50-100m stratigraphic interval.
    """
    return risk_service.evaluate_lookahead_horizon(db, request)

@router.post("/feedback")
def submit_driller_feedback_endpoint(
    feedback: DrillerFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Records human-in-the-loop driller feedback on a displayed look-ahead warning.
    """
    result = risk_service.record_driller_feedback(db, feedback)
    return result
