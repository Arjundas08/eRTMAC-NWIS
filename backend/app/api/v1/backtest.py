from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
from ...db.database import get_db
from ...services.backtest_service import backtest_service
from ...core.security import get_current_user

router = APIRouter(prefix="/backtest", tags=["Empirical Back-Testing Engine"])

@router.post("/run")
def run_backtest_endpoint(
    held_out_well_id: str = Query("NO-15/9-F-14", description="Held out well for chronological Leave-One-Well-Out validation"),
    lookahead_window_m: float = Query(75.0, description="Look-ahead window in meters"),
    enforce_temporal_cutoff: bool = Query(True, description="Strictly forbid future-information leakage"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Executes a strict chronological Leave-One-Well-Out (LOWO) back-test against the historical database.
    Benchmarks NWIS against a Geographic-Distance-Only Baseline.
    """
    return backtest_service.run_chronological_backtest(
        db=db,
        held_out_well_id=held_out_well_id,
        lookahead_window_m=lookahead_window_m,
        enforce_temporal_cutoff=enforce_temporal_cutoff
    )
