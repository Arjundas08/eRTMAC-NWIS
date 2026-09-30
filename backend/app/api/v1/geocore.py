"""
NWIS GEOCORE — PRODUCTION API ROUTER
RESTful endpoints for geological fingerprints, directional trajectories,
formation-relative correlations, 3D corridors, explainable offset ranking, and human review.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from backend.app.db.database import get_db
from backend.app.db import models
from backend.app.services.trajectory_engine import TrajectoryEngine, InsufficientGeologicalEvidenceError
from backend.app.services.geological_fingerprint_service import GeologicalFingerprintService
from backend.app.services.formation_correlation_service import FormationCorrelationService
from backend.app.services.subsurface_corridor_service import SubsurfaceCorridorService
from backend.app.services.geocore_similarity_service import GeoCoreSimilarityService
from backend.app.services.geocore_review_service import GeoCoreReviewService

router = APIRouter(prefix="/geocore", tags=["NWIS GeoCore Engine"])

# =============================================================================
# PYDANTIC REQUEST & RESPONSE SCHEMAS
# =============================================================================

class OffsetSearchRequest(BaseModel):
    primary_well_id: str
    target_formation: Optional[str] = "Hugin FM"
    radius_km: Optional[float] = 10.0

class CorrelationRequest(BaseModel):
    primary_well_id: str
    offset_well_id: str
    formation_name: str
    primary_depth_tvdss_m: Optional[float] = None

class SimilarityRequest(BaseModel):
    primary_well_id: str
    target_formation_name: Optional[str] = "Hugin FM"
    max_search_radius_km: Optional[float] = 10.0
    custom_weights: Optional[Dict[str, float]] = None

class ComparisonRequest(BaseModel):
    primary_well_id: str
    well_a_id: str
    well_b_id: str
    target_formation_name: Optional[str] = "Hugin FM"

class CorridorRequest(BaseModel):
    primary_well_id: str
    offset_well_ids: Optional[List[str]] = None
    max_corridor_radius_m: Optional[float] = 6000.0

class ReviewRequest(BaseModel):
    correlation_id: str
    reviewer_name: str
    reviewer_role: Optional[str] = "PRINCIPAL_GEOLOGIST"
    decision: str = "APPROVED" # APPROVED, REJECTED, MODIFIED, UNCERTAIN
    review_notes: Optional[str] = None

# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/wellbores", summary="List all verified wellbores in the registry")
def list_wellbores(db: Session = Depends(get_db)):
    wells = db.query(models.Well).all()
    result = []
    for w in wells:
        surveys_count = db.query(models.WellboreSurvey).filter(models.WellboreSurvey.well_id == w.well_id).count()
        tops_count = db.query(models.FormationTop).filter(models.FormationTop.well_id == w.well_id).count()
        events_count = db.query(models.DrillingEvent).filter(models.DrillingEvent.well_id == w.well_id).count()
        result.append({
            "well_id": w.well_id,
            "uwi": w.uwi,
            "well_name": w.well_name,
            "field_name": w.field_name,
            "operator": w.operator,
            "latitude": w.latitude,
            "longitude": w.longitude,
            "kb_elevation_m": w.kb_elevation_m,
            "total_depth_md_m": w.total_depth_md_m,
            "total_depth_tvd_m": w.total_depth_tvd_m,
            "well_type": w.well_type,
            "surveys_count": surveys_count,
            "tops_count": tops_count,
            "historical_events_count": events_count
        })
    return {"status": "SUCCESS", "count": len(result), "wellbores": result}

@router.get("/wellbores/{well_id:path}/fingerprint", summary="Generate structured Geological Fingerprint")
@router.get("/fingerprint", summary="Generate structured Geological Fingerprint (Query Param)")
def get_fingerprint(
    well_id: str,
    depth_md: Optional[float] = Query(None, description="Optional current measured depth"),
    formation: Optional[str] = Query(None, description="Optional target formation name"),
    db: Session = Depends(get_db)
):
    try:
        fp = GeologicalFingerprintService.generate_fingerprint(
            db, well_id, current_md_m=depth_md, target_formation_name=formation
        )
        return {"status": "SUCCESS", "fingerprint": fp}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientGeologicalEvidenceError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/wellbores/{well_id:path}/trajectory", summary="Compute full Minimum Curvature trajectory")
@router.get("/trajectory", summary="Compute full Minimum Curvature trajectory (Query Param)")
def get_trajectory(well_id: str, db: Session = Depends(get_db)):
    well = db.query(models.Well).filter(models.Well.well_id == well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail=f"Wellbore {well_id} not found.")

    surveys = db.query(models.WellboreSurvey).filter(
        models.WellboreSurvey.well_id == well_id
    ).order_by(models.WellboreSurvey.md_m.asc()).all()

    raw_stations = [
        {"md_m": s.md_m, "inclination_deg": s.inclination_deg, "azimuth_deg": s.azimuth_deg}
        for s in surveys
    ]

    try:
        traj = TrajectoryEngine.compute_trajectory(raw_stations, well.kb_elevation_m)
        return {
            "status": "SUCCESS",
            "well_id": well_id,
            "kb_elevation_m": well.kb_elevation_m,
            "station_count": len(traj),
            "stations": [s.to_dict() for s in traj]
        }
    except InsufficientGeologicalEvidenceError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/wellbores/{well_id:path}", summary="Get individual wellbore details")
def get_wellbore(well_id: str, db: Session = Depends(get_db)):
    well = db.query(models.Well).filter(models.Well.well_id == well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail=f"Wellbore {well_id} not found.")
    
    tops = db.query(models.FormationTop).filter(models.FormationTop.well_id == well_id).order_by(models.FormationTop.top_md_m.asc()).all()
    surveys = db.query(models.WellboreSurvey).filter(models.WellboreSurvey.well_id == well_id).order_by(models.WellboreSurvey.md_m.asc()).all()
    events = db.query(models.DrillingEvent).filter(models.DrillingEvent.well_id == well_id).all()

    return {
        "well_id": well.well_id,
        "uwi": well.uwi,
        "well_name": well.well_name,
        "field_name": well.field_name,
        "operator": well.operator,
        "latitude": well.latitude,
        "longitude": well.longitude,
        "kb_elevation_m": well.kb_elevation_m,
        "formations": [
            {
                "formation_name": t.formation_name,
                "top_md_m": t.top_md_m,
                "top_tvdss_m": t.top_tvdss_m,
                "base_tvdss_m": t.base_tvdss_m,
                "lithology": t.lithology_primary,
                "confidence": t.confidence_level
            }
            for t in tops
        ],
        "survey_stations_count": len(surveys),
        "historical_events_count": len(events)
    }

@router.post("/correlations", summary="Formation-relative depth correlation between two wells")
def correlate_formation(req: CorrelationRequest, db: Session = Depends(get_db)):
    corr = FormationCorrelationService.correlate_wells(
        db,
        primary_well_id=req.primary_well_id,
        offset_well_id=req.offset_well_id,
        formation_name=req.formation_name,
        primary_depth_tvdss_m=req.primary_depth_tvdss_m
    )
    return {"status": "SUCCESS", "correlation": corr}

@router.post("/similarity", summary="Multi-stage explainable offset analogue ranking")
def rank_offsets(req: SimilarityRequest, db: Session = Depends(get_db)):
    try:
        result = GeoCoreSimilarityService.rank_offset_analogues(
            db,
            primary_well_id=req.primary_well_id,
            target_formation_name=req.target_formation_name,
            max_search_radius_km=req.max_search_radius_km or 10.0,
            custom_weights=req.custom_weights
        )
        return {"status": "SUCCESS", "ranking": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/compare", summary="Signature Innovation 04: 'Why This Well, Not That Well?' comparison")
def compare_wells(req: ComparisonRequest, db: Session = Depends(get_db)):
    try:
        result = GeoCoreSimilarityService.compare_two_wells(
            db,
            primary_well_id=req.primary_well_id,
            well_a_id=req.well_a_id,
            well_b_id=req.well_b_id,
            target_formation_name=req.target_formation_name
        )
        return {"status": "SUCCESS", "comparison": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/corridor", summary="3D Subsurface Corridor calculation with incident markers")
def get_corridor(req: CorridorRequest, db: Session = Depends(get_db)):
    try:
        corridor = SubsurfaceCorridorService.generate_corridor(
            db,
            primary_well_id=req.primary_well_id,
            offset_well_ids=req.offset_well_ids,
            max_corridor_radius_m=req.max_corridor_radius_m or 6000.0
        )
        return {"status": "SUCCESS", "corridor": corridor}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/correlations/review", summary="Submit geological specialist review decision")
def review_correlation(req: ReviewRequest, db: Session = Depends(get_db)):
    try:
        res = GeoCoreReviewService.submit_review(
            db,
            correlation_id=req.correlation_id,
            reviewer_name=req.reviewer_name,
            reviewer_role=req.reviewer_role or "PRINCIPAL_GEOLOGIST",
            decision=req.decision,
            review_notes=req.review_notes
        )
        return {"status": "SUCCESS", "review": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/audit", summary="Get geological correlation review audit trail")
def get_audit(limit: int = 50, db: Session = Depends(get_db)):
    reviews = GeoCoreReviewService.get_review_history(db, limit=limit)
    return {"status": "SUCCESS", "count": len(reviews), "audit_trail": reviews}
