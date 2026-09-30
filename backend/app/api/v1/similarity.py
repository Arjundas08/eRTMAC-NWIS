from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...db.database import get_db
from ...schemas.similarity_schemas import SimilarityRequest, SimilarityResponse
from ...services.similarity_service import similarity_service
from ...core.security import get_current_user

router = APIRouter(prefix="/similarity", tags=["Offset Similarity Engine"])

@router.post("/rank", response_model=SimilarityResponse)
def rank_offset_wells_endpoint(
    request: SimilarityRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Ranks relevant offset wells using the explainable multi-criteria formulation.
    """
    try:
        ranked = similarity_service.rank_offset_wells(
            db=db,
            active_well_id=request.active_well_id,
            target_formation=request.target_formation,
            current_depth_tvdss=request.current_depth_tvdss_m,
            search_radius_km=request.search_radius_km
        )
        return SimilarityResponse(
            active_well_id=request.active_well_id,
            target_formation=request.target_formation,
            current_depth_tvdss_m=request.current_depth_tvdss_m,
            search_radius_km=request.search_radius_km,
            ranked_offsets=ranked
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
