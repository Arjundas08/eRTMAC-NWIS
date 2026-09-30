from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ...db.database import get_db
from ...db.models import Well, WellboreSurvey, FormationTop, DrillingEvent
from ...schemas.well_schemas import (
    WellResponse, SurveyPoint, FormationTopResponse, DrillingEventResponse
)
from ...services.stratigraphic_service import stratigraphic_service
from ...core.security import get_current_user

router = APIRouter(prefix="/wells", tags=["Wells & Geospatial"])

@router.get("", response_model=List[WellResponse])
@router.get("/", response_model=List[WellResponse], include_in_schema=False)
def list_wells(
    radius_km: Optional[float] = Query(None, description="Optional filter radius from reference point"),
    ref_lat: Optional[float] = Query(None),
    ref_lon: Optional[float] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all registered wells with optional geospatial radius filtering.
    """
    wells = db.query(Well).all()
    results = []

    for w in wells:
        dist = None
        if ref_lat is not None and ref_lon is not None:
            dist = stratigraphic_service.haversine_distance_km(ref_lat, ref_lon, w.latitude, w.longitude)
            if radius_km is not None and dist > radius_km:
                continue

        resp_item = WellResponse.model_validate(w)
        resp_item.distance_km = dist
        results.append(resp_item)

    return results

@router.get("/trajectory", response_model=List[SurveyPoint])
def get_well_trajectory_by_query(
    well_id: str = Query(..., description="Well Identifier (e.g. NO-15/9-F-12)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get directional survey stations for a well (supports well names with slashes).
    """
    surveys = db.query(WellboreSurvey).filter(
        WellboreSurvey.well_id == well_id
    ).order_by(WellboreSurvey.md_m.asc()).all()
    return [SurveyPoint.model_validate(s) for s in surveys]

@router.get("/formations", response_model=List[FormationTopResponse])
def get_formation_tops_by_query(
    well_id: str = Query(..., description="Well Identifier (e.g. NO-15/9-F-12)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get stratigraphic formation picks for a well.
    """
    tops = db.query(FormationTop).filter(
        FormationTop.well_id == well_id
    ).order_by(FormationTop.top_tvdss_m.asc()).all()
    return [FormationTopResponse.model_validate(t) for t in tops]

@router.get("/events", response_model=List[DrillingEventResponse])
def get_drilling_events_by_query(
    well_id: str = Query(..., description="Well Identifier (e.g. NO-15/9-F-12)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get documented drilling incidents for a well.
    """
    events = db.query(DrillingEvent).filter(
        DrillingEvent.well_id == well_id
    ).order_by(DrillingEvent.depth_tvdss_m.asc()).all()
    return [DrillingEventResponse.model_validate(e) for e in events]

@router.get("/detail", response_model=WellResponse)
def get_well_details_by_query(
    well_id: str = Query(..., description="Well Identifier"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    well = db.query(Well).filter(Well.well_id == well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail=f"Well {well_id} not found.")
    return WellResponse.model_validate(well)
