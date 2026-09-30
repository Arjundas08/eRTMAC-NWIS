from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class WellBase(BaseModel):
    well_id: str
    uwi: str
    well_name: str
    field_name: str
    operator: str
    latitude: float
    longitude: float
    kb_elevation_m: float
    total_depth_md_m: Optional[float] = None
    total_depth_tvd_m: Optional[float] = None
    spud_date: Optional[str] = None
    completion_date: Optional[str] = None
    well_type: str = "DEVELOPMENT"

class WellCreate(WellBase):
    pass

class WellResponse(WellBase):
    model_config = ConfigDict(from_attributes=True)
    distance_km: Optional[float] = None

class SurveyPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    md_m: float
    inclination_deg: float
    azimuth_deg: float
    tvd_m: float
    tvdss_m: float
    dogleg_severity_deg_30m: float

class FormationTopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    formation_name: str
    top_md_m: float
    top_tvdss_m: float
    base_tvdss_m: Optional[float] = None
    lithology_primary: str
    confidence_level: str

class DrillingEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_id: str
    well_id: str
    event_type: str
    severity: str
    depth_md_m: float
    depth_tvdss_m: float
    formation_name: str
    relative_formation_depth_m: Optional[float] = None
    npt_hours: float
    operational_narrative: str
    mitigation_applied: Optional[str] = None
    source_citation: str
    event_timestamp: Optional[str] = None
