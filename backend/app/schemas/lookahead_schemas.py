from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

class RealTimeTelemetryInput(BaseModel):
    rop_mhr: Optional[float] = None
    wob_klbs: Optional[float] = None
    rpm: Optional[float] = None
    torque_kftlbs: Optional[float] = None
    spp_psi: Optional[float] = None
    flow_in_gpm: Optional[float] = None
    flow_out_pct: Optional[float] = None
    pit_volume_m3: Optional[float] = None
    ecd_sg: Optional[float] = None

class LookaheadRequest(BaseModel):
    active_well_id: str
    current_bit_depth_md_m: float
    current_bit_depth_tvdss_m: float
    active_formation: str
    lookahead_window_m: float = Field(default=75.0, ge=10.0, le=300.0)
    as_of_timestamp: Optional[str] = Field(
        default=None,
        description="ISO-8601 timestamp cutoff. Historical memory is strictly limited to events occurring BEFORE this date."
    )
    recent_telemetry: Optional[RealTimeTelemetryInput] = None

class LookaheadAlertItem(BaseModel):
    hazard_type: str
    severity: str
    projected_tvdss_m: float
    lead_distance_m: float
    source_offset_well: str
    source_citation: str
    historical_narrative: str
    recommended_mitigation: str
    risk_score: float # 0.0 to 1.0

class LookaheadResponse(BaseModel):
    active_well_id: str
    current_bit_tvdss_m: float
    active_formation: str
    lookahead_window_m: float
    hazard_level: str # CLEAR, ADVISORY, WARNING, CRITICAL
    alert_count: int
    alerts: List[LookaheadAlertItem]
    telemetry_anomaly_flag: bool
    evidence_status: str # "VERIFIED_OFFSET_EVIDENCE", "NO_HISTORICAL_PRECEDENT", "INSUFFICIENT_GEOLOGICAL_EVIDENCE"
    evaluation_cutoff_timestamp: Optional[str] = None

class DrillerFeedbackRequest(BaseModel):
    alert_id: str
    driller_response: str = Field(..., description="ACTION_TAKEN, NUISANCE_ALARM, NOTED")
    driller_comments: Optional[str] = None
