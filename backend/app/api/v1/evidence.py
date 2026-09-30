from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from backend.app.db.database import get_db
from backend.app.services.evidence_service import evidence_service
from backend.app.schemas.evidence_schemas import EvidencePassport

router = APIRouter(prefix="/evidence", tags=["Evidence Passport & Provenance Verification"])

@router.get("/{event_id}", response_model=EvidencePassport)
def get_event_evidence_passport(event_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the complete Evidence Passport for an event, answering the 8 mandatory
    engineering questions: What happened? Which wellbore? When? Depth? Formation?
    Original report passage? Missing information? Verification status?
    """
    passport = evidence_service.get_evidence_passport(event_id, db)
    if not passport:
        raise HTTPException(status_code=404, detail=f"Evidence Passport for event {event_id} not found.")
    return passport

@router.get("/{event_id}/snippet")
def get_evidence_snippet(event_id: str, db: Session = Depends(get_db)):
    """Returns the rendered supporting page image with the exact highlighted bounding box."""
    passport = evidence_service.get_evidence_passport(event_id, db)
    if not passport or not passport.doc_id:
        raise HTTPException(status_code=404, detail=f"No document evidence linked to event {event_id}.")

    img_path = evidence_service.render_highlighted_passage_image(
        passport.doc_id, passport.source_page_number, db
    )
    if img_path and Path(img_path).exists():
        return FileResponse(img_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Evidence page render unavailable.")
