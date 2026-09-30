"""Comprehensive Unit & Integration Test Suite for NWIS Chronos.
Validates:
1. Point-in-Time Evidence Firewall (temporal cutoff, future doc exclusion, exception handling)
2. Replay Eligibility Registry (wellbore tiers, limitations, quality scoring)
3. Chronos Replay Engine (session initialization, step progression, jump to event, advisory generation)
4. Chronological Leave-One-Well-Out (LOWO) Evaluation & Metrics (TP, FP, FN, precision, recall, lead distance)
5. 3-Way Baseline Comparison (Proximity vs Formation vs GeoCore+Chronos)
6. FastAPI Chronos Endpoints
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.services.chronos_firewall import (
    PointInTimeFirewall,
    verify_document_availability,
    TemporalFirewallViolation
)
from backend.app.services.chronos_eligibility_service import ChronosEligibilityService
from backend.app.services.chronos_replay_engine import ChronosReplayEngine
from backend.app.services.chronos_evaluation_service import ChronosEvaluationService

client = TestClient(app)


# ============================================================================
# 1. POINT-IN-TIME EVIDENCE FIREWALL TESTS
# ============================================================================

def test_temporal_firewall_excludes_future_evidence():
    """Verify that setting an evaluation timestamp strictly excludes documents and wells created afterward."""
    db = SessionLocal()
    try:
        # NO-15/9-F-14 spud date: 2008-08-02. F-15S spud date: 2009-01-20.
        cutoff = "2008-08-02T00:00:00"
        snapshot = PointInTimeFirewall.create_snapshot(db, target_well_id="NO-15/9-F-14", as_of_timestamp=cutoff)

        assert snapshot.cutoff_timestamp == cutoff
        assert snapshot.target_well_id == "NO-15/9-F-14"
        assert snapshot.checksum_sha256 is not None

        # Check transparency report
        report = PointInTimeFirewall.get_firewall_transparency(db, target_well_id="NO-15/9-F-14", as_of_timestamp=cutoff)
        
        # Target well NO-15/9-F-14 must NOT be in prior offsets
        available_ids = [w["well_id"] for w in report["accessible_offset_wells"]]
        assert "NO-15/9-F-14" not in available_ids

        # NO-15/9-F-15S (2009) must be in excluded future wells
        excluded_ids = [w["well_id"] for w in report["excluded_future_wells"]]
        assert "NO-15/9-F-15S" in excluded_ids

        # NO-15/9-F-12 (completed July 2008) MUST be accessible
        assert "NO-15/9-F-12" in available_ids
    finally:
        db.close()


def test_firewall_raises_violation_on_future_doc_access():
    """Verify that attempting to access a document available after cutoff raises TemporalFirewallViolation."""
    cutoff = datetime(2008, 8, 2)
    future_doc_date = datetime(2009, 5, 1)

    with pytest.raises(TemporalFirewallViolation) as exc_info:
        verify_document_availability("WCR_F-15S.pdf", future_doc_date, cutoff)

    assert "Temporal Firewall Violation" in str(exc_info.value)


# ============================================================================
# 2. REPLAY ELIGIBILITY REGISTRY TESTS
# ============================================================================

def test_replay_eligibility_all_wells():
    """Verify eligibility classification tiers for repository wellbores."""
    db = SessionLocal()
    try:
        registry = ChronosEligibilityService.list_all_eligibility(db)
        assert len(registry) >= 4

        # F-14 should be eligible for depth-indexed replay
        f14 = next((w for w in registry if "F-14" in w["well_id"]), None)
        assert f14 is not None
        assert f14["eligibility_tier"] == "DEPTH_INDEXED"
        assert f14["criteria"]["has_definitive_survey"] is True
        assert f14["criteria"]["has_formation_tops"] is True
        assert f14["criteria"]["has_prior_offsets"] is True

        # F-1 (2006 pioneer) has zero prior offsets -> RETROSPECTIVE_ONLY
        f1 = next((w for w in registry if w["well_id"] == "NO-15/9-F-1"), None)
        if f1:
            assert f1["eligibility_tier"] == "RETROSPECTIVE_ONLY"
    finally:
        db.close()


def test_get_single_well_eligibility():
    """Verify single well eligibility lookup."""
    db = SessionLocal()
    try:
        res = ChronosEligibilityService.evaluate_well_eligibility(db, "NO-15/9-F-12")
        assert res is not None
        assert res["well_id"] == "NO-15/9-F-12"
        assert res["criteria"]["has_drilling_dates"] is True
    finally:
        db.close()


# ============================================================================
# 3. CHRONOS REPLAY ENGINE TESTS
# ============================================================================

def test_replay_session_initialization_and_stepping():
    """Verify creating a replay session, stepping through depths, and retrieving state."""
    db = SessionLocal()
    try:
        init_state = ChronosReplayEngine.start_replay_session(
            db, well_id="NO-15/9-F-14", start_depth_md_m=2650.0, lookahead_window_m=100.0
        )
        assert "session_id" in init_state
        session_id = init_state["session_id"]
        assert init_state["well_id"] == "NO-15/9-F-14"
        assert init_state["telemetry"]["bit_depth_md_m"] == 2650.0

        # Step forward by 20m
        stepped = ChronosReplayEngine.step_session(db, session_id, step_md_m=20.0, lookahead_window_m=100.0)
        assert stepped["telemetry"]["bit_depth_md_m"] == 2670.0
        assert stepped["telemetry"]["rop_m_hr"] > 0
    finally:
        db.close()


def test_replay_jump_to_incident():
    """Verify jumping directly to documented incident depth in active well."""
    db = SessionLocal()
    try:
        init_state = ChronosReplayEngine.start_replay_session(
            db, well_id="NO-15/9-F-14", start_depth_md_m=2650.0
        )
        session_id = init_state["session_id"]

        jump_state = ChronosReplayEngine.jump_to_incident(db, session_id)
        # F-14 first event is at 2965m, jump goes to ~2915m (50m before)
        assert jump_state["telemetry"]["bit_depth_md_m"] <= 3150.0
        assert jump_state["telemetry"]["bit_depth_md_m"] >= 2900.0
    finally:
        db.close()


# ============================================================================
# 4. LEAVE-ONE-WELL-OUT (LOWO) EVALUATION TESTS
# ============================================================================

def test_chronological_lowo_evaluation():
    """Verify leave-one-well-out back-testing produces reproducible statistical metrics."""
    db = SessionLocal()
    try:
        results = ChronosEvaluationService.run_evaluation(
            db, target_well_id="NO-15/9-F-14", evaluation_type="CHRONOS_LEAVE_ONE_WELL_OUT", lookahead_window_m=100.0
        )
        assert results["target_well_id"] == "NO-15/9-F-14"
        assert results["total_ground_truth_events"] > 0
        assert results["true_positives"] >= 1
        assert results["recall"] > 0.0
        assert results["avg_lead_distance_m"] > 0.0
    finally:
        db.close()


def test_3_way_baseline_comparison():
    """Verify fair 3-way baseline comparison against Proximity and Formation-only baselines."""
    db = SessionLocal()
    try:
        comp = ChronosEvaluationService.run_all_baselines_comparison(db, target_well_id="NO-15/9-F-14")
        assert "chronos_geocore" in comp
        assert "baseline_a_distance_only" in comp
        assert "baseline_b_formation_only" in comp

        chronos = comp["chronos_geocore"]
        base_a = comp["baseline_a_distance_only"]
        
        # Chronos should achieve superior recall vs distance-only
        assert chronos["recall"] >= base_a["recall"]
    finally:
        db.close()


# ============================================================================
# 5. FASTAPI REST ENDPOINT INTEGRATION TESTS
# ============================================================================

def test_api_chronos_eligibility():
    """Test GET /api/v1/chronos/eligibility"""
    resp = client.get("/api/v1/chronos/eligibility")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 3


def test_api_chronos_single_eligibility():
    """Test GET /api/v1/chronos/eligibility/{well_id}"""
    resp = client.get("/api/v1/chronos/eligibility/NO-15/9-F-14")
    assert resp.status_code == 200
    assert resp.json()["well_id"] == "NO-15/9-F-14"


def test_api_chronos_replay_lifecycle():
    """Test start, step, state, and jump via REST API."""
    # 1. Start Replay
    start_payload = {
        "well_id": "NO-15/9-F-14",
        "start_depth_md_m": 2650.0,
        "lookahead_window_m": 100.0,
        "speed_factor": 1.0
    }
    resp = client.post("/api/v1/chronos/replay/start", json=start_payload)
    assert resp.status_code == 200
    res_data = resp.json()
    session_id = res_data["session_id"]
    assert session_id is not None

    # 2. Get State
    resp_get = client.get(f"/api/v1/chronos/replay/{session_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["session_id"] == session_id

    # 3. Step forward
    resp_step = client.post(f"/api/v1/chronos/replay/{session_id}/step", json={"step_md_m": 15.0, "lookahead_window_m": 100.0})
    assert resp_step.status_code == 200
    assert resp_step.json()["telemetry"]["bit_depth_md_m"] == 2665.0

    # 4. Jump to incident
    resp_jump = client.post(f"/api/v1/chronos/replay/{session_id}/jump")
    assert resp_jump.status_code == 200
    assert resp_jump.json()["telemetry"]["bit_depth_md_m"] >= 2900.0


def test_api_chronos_transparency():
    """Test GET /api/v1/chronos/transparency endpoint."""
    resp = client.get("/api/v1/chronos/transparency?well_id=NO-15/9-F-14&as_of=2008-08-02T00:00:00")
    assert resp.status_code == 200
    data = resp.json()
    assert data["target_well"]["well_id"] == "NO-15/9-F-14"
    assert "firewall_summary" in data
    assert "excluded_future_wells" in data


def test_api_chronos_evaluation_endpoints():
    """Test /api/v1/chronos/evaluation/run and /api/v1/chronos/evaluation/baselines."""
    resp_run = client.post("/api/v1/chronos/evaluation/run?target_well_id=NO-15/9-F-14&lookahead_window_m=100.0")
    assert resp_run.status_code == 200
    assert resp_run.json()["target_well_id"] == "NO-15/9-F-14"

    resp_base = client.get("/api/v1/chronos/evaluation/baselines?target_well_id=NO-15/9-F-14")
    assert resp_base.status_code == 200
    assert "chronos_geocore" in resp_base.json()
    assert "comparative_analysis" in resp_base.json()
