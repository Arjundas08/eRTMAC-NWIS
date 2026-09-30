from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class SimilarityRequest(BaseModel):
    active_well_id: str
    target_formation: str
    current_depth_tvdss_m: float
    search_radius_km: float = Field(default=5.0, ge=0.5, le=25.0)

class SimilarityExplanation(BaseModel):
    geospatial_distance_km: float
    stratigraphic_match: bool
    formation_top_delta_m: float
    trajectory_deviation_diff_deg: float
    historical_event_count: int
    primary_reasons: List[str]

class RankedOffsetWell(BaseModel):
    offset_well_id: str
    well_name: str
    composite_similarity_score: float
    rank: int
    confidence_level: str # HIGH, MEDIUM, LOW
    explanation: SimilarityExplanation
    relevant_events_summary: List[Dict[str, Any]]

class SimilarityResponse(BaseModel):
    active_well_id: str
    target_formation: str
    current_depth_tvdss_m: float
    search_radius_km: float
    ranked_offsets: List[RankedOffsetWell]
