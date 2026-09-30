"""
NWIS NEXUS — Unified Operations Dashboard & Decision Command Center API Router (Phase 07)
Provides typed endpoints for:
- System-wide health monitoring and module status aggregation
- Cross-module intelligence fusion per well
- Operations log for shift handover and audit
- KPI dashboard metrics
- Multi-well comparison matrix
- Alert severity timeline
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.services.nexus_engine import NexusEngine

router = APIRouter(prefix="/nexus", tags=["NWIS NEXUS — Unified Operations Command Center"])


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class WellComparisonRequest(BaseModel):
    well_ids: List[str] = Field(
        ...,
        description="List of well IDs to compare",
        json_schema_extra={"example": ["NO-15/9-F-11A", "NO-15/9-F-12", "NO-15/9-F-14"]}
    )


# =============================================================================
# SYSTEM HEALTH & STATUS
# =============================================================================

@router.get("/health", summary="Unified system health across all NWIS modules")
def nexus_system_health(db: Session = Depends(get_db)):
    """
    Aggregates health status from GeoCore, Chronos, Sentinel, Pulse, and Document AI
    into a single unified operational picture.
    """
    try:
        return NexusEngine.get_system_health(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NEXUS health aggregation failed: {str(e)}")


# =============================================================================
# CROSS-MODULE INTELLIGENCE FUSION
# =============================================================================

@router.get("/fuse/{well_id:path}", summary="Fuse intelligence from all modules for a well")
def fuse_well_intelligence(well_id: str, db: Session = Depends(get_db)):
    """
    Combines geological context, historical events, telemetry state, operational advisories,
    and Sentinel knowledge into a single evidence-backed assessment with deterministic
    risk scoring.
    """
    try:
        return NexusEngine.fuse_well_intelligence(db, well_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intelligence fusion failed: {str(e)}")


# =============================================================================
# OPERATIONS LOG
# =============================================================================

@router.get("/operations-log", summary="Cross-module operations log for shift handover")
def get_operations_log(
    limit: int = Query(50, ge=1, le=500, description="Maximum log entries to return"),
    db: Session = Depends(get_db)
):
    """
    Aggregates significant events from Pulse advisories, Sentinel queries,
    Chronos replays, and telemetry quality events into a unified time-ordered
    operations journal.
    """
    try:
        return NexusEngine.get_operations_log(db, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Operations log retrieval failed: {str(e)}")


# =============================================================================
# KPI DASHBOARD
# =============================================================================

@router.get("/kpis", summary="System-wide KPI metrics for executive dashboard")
def get_kpi_metrics(db: Session = Depends(get_db)):
    """
    Computes evidence quality, advisory resolution rate, telemetry uptime,
    Sentinel query performance, and NPT exposure metrics.
    """
    try:
        return NexusEngine.get_kpi_metrics(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI computation failed: {str(e)}")


# =============================================================================
# MULTI-WELL COMPARISON
# =============================================================================

@router.post("/compare", summary="Multi-well cross-module comparison matrix")
def compare_wells(req: WellComparisonRequest, db: Session = Depends(get_db)):
    """
    Builds a side-by-side comparison matrix of multiple wells across all NWIS
    dimensions: geological profile, event history, telemetry status, and risk score.
    """
    if len(req.well_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 well IDs required for comparison")
    if len(req.well_ids) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 wells per comparison")
    try:
        return NexusEngine.compare_wells(db, req.well_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Well comparison failed: {str(e)}")


# =============================================================================
# ALERT SEVERITY TIMELINE
# =============================================================================

@router.get("/timeline", summary="Depth-indexed alert severity timeline")
def get_alert_timeline(
    well_id: Optional[str] = Query(None, description="Filter to specific well ID"),
    db: Session = Depends(get_db)
):
    """
    Builds a depth-indexed timeline of all historical events and operational advisories
    for visualization on the NEXUS command center dashboard.
    """
    try:
        return NexusEngine.get_alert_timeline(db, well_id=well_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timeline generation failed: {str(e)}")


# =============================================================================
# NEXUS SUMMARY (Landing API)
# =============================================================================

@router.get("/summary", summary="Quick NEXUS summary for landing page integration")
def nexus_summary(db: Session = Depends(get_db)):
    """
    Lightweight summary of system status for integration into the landing page
    and other module dashboards.
    """
    try:
        health = NexusEngine.get_system_health(db)
        kpis = NexusEngine.get_kpi_metrics(db)
        return {
            "overall_status": health["overall_status"],
            "modules": {k: v["status"] for k, v in health["modules"].items()},
            "wells_loaded": health["data_summary"]["total_wells"],
            "total_events": health["data_summary"]["total_drilling_events"],
            "evidence_quality_pct": kpis["kpis"]["evidence_quality"]["verified_events_pct"],
            "advisory_resolution_pct": kpis["kpis"]["advisory_resolution"]["resolution_rate_pct"],
            "npt_hours": kpis["kpis"]["npt_exposure"]["total_npt_hours"],
            "generated_at": health["timestamp"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NEXUS summary failed: {str(e)}")
