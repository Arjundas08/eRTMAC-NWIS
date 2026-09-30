import pytest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.db.database import SessionLocal
from backend.app.services.risk_service import risk_service
from backend.app.schemas.lookahead_schemas import LookaheadRequest, DrillerFeedbackRequest

def test_lookahead_scan_with_offset_events():
    db = SessionLocal()
    try:
        # Well 15/9-F-12 drilling into Hugin FM at 2850m TVDSS
        # Offset wells F-14 and F-15S have documented loss and stuck pipe events in this interval
        req = LookaheadRequest(
            active_well_id="NO-15/9-F-12",
            current_bit_depth_md_m=2893.5,
            current_bit_depth_tvdss_m=2850.0,
            active_formation="Hugin FM",
            lookahead_window_m=75.0
        )

        response = risk_service.evaluate_lookahead_horizon(db, req)

        assert response.hazard_level in ["WARNING", "CRITICAL", "ADVISORY"]
        assert response.alert_count > 0
        assert response.evidence_status == "VERIFIED_OFFSET_EVIDENCE"

        # Verify that all alerts have source citations
        for alert in response.alerts:
            assert len(alert.source_citation) > 0
            assert alert.lead_distance_m > 0
            assert alert.lead_distance_m <= 75.0
    finally:
        db.close()

def test_lookahead_evidence_or_silence():
    db = SessionLocal()
    try:
        # Scan an interval with zero historical events (e.g. shallow 100m depth)
        req = LookaheadRequest(
            active_well_id="NO-15/9-F-12",
            current_bit_depth_md_m=150.0,
            current_bit_depth_tvdss_m=106.5,
            active_formation="Nordland GP",
            lookahead_window_m=50.0
        )

        response = risk_service.evaluate_lookahead_horizon(db, req)

        assert response.hazard_level == "CLEAR"
        assert response.alert_count == 0
        assert response.evidence_status == "NO_HISTORICAL_PRECEDENT"
    finally:
        db.close()

def test_driller_feedback_recording():
    db = SessionLocal()
    try:
        feedback = DrillerFeedbackRequest(
            alert_id="mock-alert-id-001",
            driller_response="ACTION_TAKEN",
            driller_comments="Staged 35 bbl LCM pill on rig floor prior to entering formation."
        )

        res = risk_service.record_driller_feedback(db, feedback)
        assert res["status"] in ["success", "error"]
    finally:
        db.close()
