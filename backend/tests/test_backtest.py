import pytest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.db.database import SessionLocal
from backend.app.services.backtest_service import backtest_service

def test_leave_one_well_out_backtest():
    db = SessionLocal()
    try:
        report = backtest_service.run_leave_one_well_out(
            db=db,
            held_out_well_id="NO-15/9-F-12",
            lookahead_window_m=75.0
        )

        assert report["held_out_well_id"] == "NO-15/9-F-12"
        assert report["total_real_documented_events"] > 0
        assert report["proactively_flagged_true_positives"] > 0
        assert report["average_advance_warning_lead_meters"] > 0
        assert "sensitivity_recall_pct" in report
        assert "precision_pct" in report
        assert len(report["event_breakdown"]) == report["total_real_documented_events"]
    finally:
        db.close()
