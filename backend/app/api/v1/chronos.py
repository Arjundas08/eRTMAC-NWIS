"""NWIS Chronos REST API Router
Endpoints for Historical Replay, Evidence Firewall Transparency, Replay Eligibility, and LOWO Evaluation.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.services.chronos_firewall import (
    PointInTimeFirewall,
    freeze_historical_memory,
    get_what_the_engineer_could_have_known,
    verify_document_availability,
    TemporalFirewallViolation
)
from backend.app.services.chronos_eligibility_service import ChronosEligibilityService
from backend.app.services.chronos_replay_engine import ChronosReplayEngine
from backend.app.services.chronos_evaluation_service import ChronosEvaluationService

router = APIRouter(prefix="/chronos", tags=["NWIS Chronos Replay"])


# --- Request/Response Models ---

class ReplayStartRequest(BaseModel):
    well_id: str = Field(..., description="Target historical wellbore identifier, e.g. NO-15/9-F-14")
    start_depth_md_m: float = Field(2650.0, description="Starting measured depth in meters")
    end_depth_md_m: Optional[float] = Field(None, description="Optional ending measured depth in meters")
    lookahead_window_m: float = Field(100.0, description="Formation look-ahead distance in meters")
    speed_factor: float = Field(1.0, description="Replay visual playback rate multiplier")


class ReplayStepRequest(BaseModel):
    step_md_m: float = Field(10.0, description="Step increment along wellbore trajectory in meters")
    lookahead_window_m: float = Field(100.0, description="Formation look-ahead window in meters")


# --- Endpoints ---

@router.get("/eligibility")
@router.get("/wells")
def list_replay_eligibility(db: Session = Depends(get_db)):
    """Returns replay eligibility tier, survey resolution, and prior offset availability for all wells."""
    try:
        return ChronosEligibilityService.list_all_eligibility(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eligibility retrieval failed: {str(e)}")


@router.get("/eligibility/{well_id:path}")
def get_single_well_eligibility(well_id: str, db: Session = Depends(get_db)):
    """Returns eligibility classification and limitations for a specific wellbore."""
    try:
        return ChronosEligibilityService.evaluate_well_eligibility(db, well_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eligibility check failed: {str(e)}")


@router.post("/replay/start")
def start_replay(req: ReplayStartRequest, db: Session = Depends(get_db)):
    """Initializes a new reproducible historical replay session with frozen point-in-time memory."""
    try:
        return ChronosReplayEngine.start_replay_session(
            db=db,
            well_id=req.well_id,
            start_depth_md_m=req.start_depth_md_m,
            end_depth_md_m=req.end_depth_md_m,
            lookahead_window_m=req.lookahead_window_m,
            speed_factor=req.speed_factor
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start replay: {str(e)}")


@router.get("/replay/{session_id}")
def get_replay_state(session_id: str, lookahead_window_m: float = Query(100.0), db: Session = Depends(get_db)):
    """Retrieves current replay telemetry, advisories, trajectory, and progress for an active session."""
    try:
        return ChronosReplayEngine.get_session_state(db=db, session_id=session_id, lookahead_window_m=lookahead_window_m)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch session state: {str(e)}")


@router.post("/replay/{session_id}/step")
def step_replay(session_id: str, req: Optional[ReplayStepRequest] = None, db: Session = Depends(get_db)):
    """Advances replay forward by step increment, scanning for formation transitions and offset hazards."""
    step_md = req.step_md_m if req else 10.0
    lookahead = req.lookahead_window_m if req else 100.0
    try:
        return ChronosReplayEngine.step_session(db=db, session_id=session_id, step_md_m=step_md, lookahead_window_m=lookahead)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replay step failed: {str(e)}")


@router.post("/replay/{session_id}/jump")
def jump_replay_to_incident(session_id: str, lookahead_window_m: float = Query(100.0), db: Session = Depends(get_db)):
    """Jumps replay state directly to 50m prior to the first documented geological incident in active well."""
    try:
        return ChronosReplayEngine.jump_to_incident(db=db, session_id=session_id, lookahead_window_m=lookahead_window_m)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replay jump failed: {str(e)}")


@router.get("/transparency")
def inspect_evidence_transparency(
    well_id: str = Query(..., description="Target well identifier"),
    as_of: str = Query(..., description="Historical evaluation timestamp ISO string"),
    db: Session = Depends(get_db)
):
    """Signature Innovation 01: 'What the Engineer Could Have Known'

    Returns the exact snapshot of available offsets, documents, geological interpretations,
    and explicitly lists future documents/incidents excluded by the Point-in-Time Firewall.
    """
    try:
        return PointInTimeFirewall.get_firewall_transparency(db=db, target_well_id=well_id, as_of_timestamp=as_of)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transparency query failed: {str(e)}")


@router.post("/evaluation/run")
def execute_lowo_evaluation(
    target_well_id: str = Query("NO-15/9-F-14"),
    lookahead_window_m: float = Query(100.0),
    cooldown_window_m: float = Query(50.0),
    db: Session = Depends(get_db)
):
    """Executes rigorous Chronological Leave-One-Well-Out (LOWO) Evaluation for target well.
    Calculates empirical TP, FP, FN, precision, recall, and lead-distance metrics.
    """
    try:
        return ChronosEvaluationService.run_evaluation(
            db=db,
            target_well_id=target_well_id,
            evaluation_type="CHRONOS_LEAVE_ONE_WELL_OUT",
            lookahead_window_m=lookahead_window_m,
            cooldown_window_m=cooldown_window_m
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LOWO Evaluation failed: {str(e)}")


@router.get("/evaluation/baselines")
def get_evaluation_baselines(
    target_well_id: str = Query("NO-15/9-F-14"),
    db: Session = Depends(get_db)
):
    """Signature Requirement 13: Fair 3-Way Baseline Comparison.
    Compares Baseline A (Proximity Only), Baseline B (Formation Only), and Proposed GeoCore + Chronos.
    """
    try:
        return ChronosEvaluationService.run_all_baselines_comparison(db=db, target_well_id=target_well_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Baseline comparison failed: {str(e)}")
