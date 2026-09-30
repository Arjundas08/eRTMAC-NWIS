from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.app.db.database import get_db
from backend.app.services.review_service import review_service
from backend.app.schemas.review_schemas import (
    ReviewTaskItem, ReviewDecisionRequest, ReviewDecisionResponse
)

router = APIRouter(prefix="/review", tags=["Human-in-the-Loop Document Review"])

@router.get("/tasks")
def list_review_tasks(
    status: str = Query("PENDING", description="Task review status filter: PENDING, RESOLVED, REJECTED"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Lists pending extraction review tasks for human petroleum engineer validation."""
    return review_service.list_pending_tasks(db=db, status=status)

@router.post("/decision", response_model=ReviewDecisionResponse)
def submit_review_decision(
    req: ReviewDecisionRequest,
    db: Session = Depends(get_db)
):
    """
    Submits a human review decision (APPROVED, REJECTED, MODIFIED).
    Updates verification status in the database and logs a tamper-evident audit record.
    """
    try:
        return review_service.submit_decision(db=db, req=req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record review decision: {str(e)}")
