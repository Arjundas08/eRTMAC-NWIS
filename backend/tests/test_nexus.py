"""
NWIS NEXUS — Phase 07 Comprehensive Test Suite

Tests for:
1. System health aggregation across all modules
2. Cross-module intelligence fusion per well
3. Risk scoring (deterministic, explainable)
4. Operations log aggregation
5. KPI metrics computation
6. Multi-well comparison matrix
7. Alert severity timeline
8. API endpoint integration tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json

from backend.app.main import app
from backend.app.db.database import get_db, engine, Base
from backend.app.db.models import (
    Well, WellboreSurvey, FormationTop, DrillingEvent,
    KnowledgeChunk, OperationalAdvisory, TelemetrySource,
    NormalizedTelemetry, TelemetryQualityEvent, ReplaySession,
    GenerationAudit, Document
)
from backend.app.services.nexus_engine import NexusEngine

client = TestClient(app)


def get_test_db():
    """Get a fresh test database session."""
    db = next(get_db())
    return db


# =============================================================================
# 1. SYSTEM HEALTH AGGREGATION
# =============================================================================

class TestSystemHealth:
    def test_system_health_returns_all_modules(self):
        """System health must include status for all 5 NWIS modules."""
        db = get_test_db()
        result = NexusEngine.get_system_health(db)

        assert "overall_status" in result
        assert "modules" in result
        assert "geocore" in result["modules"]
        assert "chronos" in result["modules"]
        assert "sentinel" in result["modules"]
        assert "pulse" in result["modules"]
        assert "document_ai" in result["modules"]

        # Each module must have a status field
        for module_name, module_data in result["modules"].items():
            assert "status" in module_data, f"Module '{module_name}' missing status field"

    def test_system_health_data_summary(self):
        """System health must include data summary counts."""
        db = get_test_db()
        result = NexusEngine.get_system_health(db)

        assert "data_summary" in result
        summary = result["data_summary"]
        assert "total_wells" in summary
        assert "total_drilling_events" in summary
        assert "total_documents" in summary
        assert isinstance(summary["total_wells"], int)

    def test_system_health_safety_disclaimer(self):
        """System health must always include the safety disclaimer."""
        db = get_test_db()
        result = NexusEngine.get_system_health(db)

        assert "safety_disclaimer" in result
        assert "read-only advisory" in result["safety_disclaimer"].lower()

    def test_overall_status_classification(self):
        """Overall status should be one of the defined states."""
        db = get_test_db()
        result = NexusEngine.get_system_health(db)

        valid_statuses = [
            "ALL_SYSTEMS_OPERATIONAL", "DEGRADED",
            "STANDBY", "PARTIALLY_OPERATIONAL"
        ]
        assert result["overall_status"] in valid_statuses


# =============================================================================
# 2. CROSS-MODULE INTELLIGENCE FUSION
# =============================================================================

class TestIntelligenceFusion:
    def test_fusion_with_existing_well(self):
        """Fusion should produce all layers for a known well."""
        db = get_test_db()
        well = db.query(Well).first()
        if not well:
            pytest.skip("No wells in test database")

        result = NexusEngine.fuse_well_intelligence(db, well.well_id)

        assert result["status"] == "FUSED"
        assert result["well_id"] == well.well_id
        assert "geocore_layer" in result
        assert "historical_events_layer" in result
        assert "advisory_layer" in result
        assert "sentinel_layer" in result
        assert "risk_assessment" in result
        assert "fusion_integrity_sha256" in result

    def test_fusion_with_nonexistent_well(self):
        """Fusion should abstain gracefully for unknown wells."""
        db = get_test_db()
        result = NexusEngine.fuse_well_intelligence(db, "NONEXISTENT_WELL_XYZ")

        assert result["status"] == "WELL_NOT_FOUND"
        assert result["fused_intelligence"] is None
        assert "abstention_reason" in result

    def test_fusion_geocore_layer_structure(self):
        """GeoCore layer must contain well metadata and formation information."""
        db = get_test_db()
        well = db.query(Well).first()
        if not well:
            pytest.skip("No wells in test database")

        result = NexusEngine.fuse_well_intelligence(db, well.well_id)
        geocore = result["geocore_layer"]

        assert "well_name" in geocore
        assert "field" in geocore
        assert "formation_tops" in geocore
        assert isinstance(geocore["formation_tops"], list)

    def test_fusion_evidence_contract(self):
        """Fusion must declare the Evidence-or-Silence contract."""
        db = get_test_db()
        well = db.query(Well).first()
        if not well:
            pytest.skip("No wells in test database")

        result = NexusEngine.fuse_well_intelligence(db, well.well_id)
        assert result["evidence_contract"] == "STRICT_EVIDENCE_OR_SILENCE"

    def test_fusion_integrity_hash(self):
        """Fusion results must include a SHA-256 integrity hash."""
        db = get_test_db()
        well = db.query(Well).first()
        if not well:
            pytest.skip("No wells in test database")

        result = NexusEngine.fuse_well_intelligence(db, well.well_id)
        assert len(result["fusion_integrity_sha256"]) == 64  # SHA-256 hex length


# =============================================================================
# 3. RISK SCORING
# =============================================================================

class TestRiskScoring:
    def test_risk_score_structure(self):
        """Risk score must have composite score, tier, and component breakdown."""
        events_layer = {
            "total_events": 5,
            "events_by_severity": {"CRITICAL": 1, "MODERATE": 3, "MINOR": 1},
            "total_npt_hours": 24.5
        }
        advisory_layer = {"active": 2}
        telemetry_layer = {"quality_state": "HEALTHY"}

        result = NexusEngine._calculate_risk_score(events_layer, telemetry_layer, advisory_layer)

        assert "composite_score" in result
        assert "risk_tier" in result
        assert "components" in result
        assert "explanation" in result

    def test_risk_score_deterministic(self):
        """Same inputs must always produce same risk score."""
        events_layer = {
            "total_events": 3,
            "events_by_severity": {"SEVERE": 2, "MINOR": 1},
            "total_npt_hours": 16.0
        }
        advisory_layer = {"active": 1}
        telemetry_layer = {"quality_state": "DEGRADED"}

        result1 = NexusEngine._calculate_risk_score(events_layer, telemetry_layer, advisory_layer)
        result2 = NexusEngine._calculate_risk_score(events_layer, telemetry_layer, advisory_layer)

        assert result1["composite_score"] == result2["composite_score"]
        assert result1["risk_tier"] == result2["risk_tier"]

    def test_critical_events_produce_high_risk(self):
        """Multiple critical events should produce elevated or critical risk tier."""
        events_layer = {
            "total_events": 6,
            "events_by_severity": {"CRITICAL": 3, "SEVERE": 2, "MODERATE": 1},
            "total_npt_hours": 100.0
        }
        advisory_layer = {"active": 3}
        telemetry_layer = {"quality_state": "STALE"}

        result = NexusEngine._calculate_risk_score(events_layer, telemetry_layer, advisory_layer)

        assert result["risk_tier"] in ("ELEVATED", "CRITICAL")
        assert result["composite_score"] >= 50.0

    def test_no_events_produces_low_risk(self):
        """Zero events with healthy telemetry should produce low risk."""
        events_layer = {
            "total_events": 0,
            "events_by_severity": {},
            "total_npt_hours": 0.0
        }
        advisory_layer = {"active": 0}
        telemetry_layer = {"quality_state": "HEALTHY"}

        result = NexusEngine._calculate_risk_score(events_layer, telemetry_layer, advisory_layer)

        assert result["risk_tier"] == "LOW"
        assert result["composite_score"] < 25.0

    def test_risk_score_without_telemetry(self):
        """Risk scoring should handle None telemetry gracefully."""
        events_layer = {
            "total_events": 2,
            "events_by_severity": {"MODERATE": 2},
            "total_npt_hours": 5.0
        }
        advisory_layer = {"active": 0}

        result = NexusEngine._calculate_risk_score(events_layer, None, advisory_layer)

        assert "composite_score" in result
        assert result["components"]["telemetry_quality_risk"]["quality_state"] == "NO_TELEMETRY"


# =============================================================================
# 4. OPERATIONS LOG
# =============================================================================

class TestOperationsLog:
    def test_operations_log_structure(self):
        """Operations log must return structured entries with timestamps."""
        db = get_test_db()
        result = NexusEngine.get_operations_log(db, limit=10)

        assert "operations_log" in result
        assert "total_entries" in result
        assert "generated_at" in result
        assert isinstance(result["operations_log"], list)

    def test_operations_log_limit_respected(self):
        """Operations log should respect the limit parameter."""
        db = get_test_db()
        result = NexusEngine.get_operations_log(db, limit=5)

        assert len(result["operations_log"]) <= 5


# =============================================================================
# 5. KPI METRICS
# =============================================================================

class TestKPIMetrics:
    def test_kpi_structure(self):
        """KPIs must include all 5 metric categories."""
        db = get_test_db()
        result = NexusEngine.get_kpi_metrics(db)

        assert "kpis" in result
        kpis = result["kpis"]
        assert "evidence_quality" in kpis
        assert "advisory_resolution" in kpis
        assert "telemetry_uptime" in kpis
        assert "sentinel_performance" in kpis
        assert "npt_exposure" in kpis

    def test_kpi_values_are_numeric(self):
        """All KPI percentages should be numeric and in range [0, 100]."""
        db = get_test_db()
        result = NexusEngine.get_kpi_metrics(db)

        kpis = result["kpis"]
        for category in ["evidence_quality", "advisory_resolution", "telemetry_uptime", "sentinel_performance"]:
            for key, value in kpis[category].items():
                if key.endswith("_pct"):
                    assert isinstance(value, (int, float))
                    assert 0 <= value <= 100, f"KPI {category}.{key} = {value} is out of range"


# =============================================================================
# 6. MULTI-WELL COMPARISON
# =============================================================================

class TestMultiWellComparison:
    def test_comparison_with_existing_wells(self):
        """Comparison should produce matrix entries for known wells."""
        db = get_test_db()
        wells = db.query(Well).limit(3).all()
        if len(wells) < 2:
            pytest.skip("Need at least 2 wells for comparison")

        well_ids = [w.well_id for w in wells]
        result = NexusEngine.compare_wells(db, well_ids)

        assert "comparison_matrix" in result
        assert result["well_count"] == len(well_ids)
        assert "integrity_sha256" in result
        assert len(result["integrity_sha256"]) == 64

    def test_comparison_with_unknown_well(self):
        """Comparison should handle unknown wells gracefully."""
        db = get_test_db()
        result = NexusEngine.compare_wells(db, ["UNKNOWN_WELL_1", "UNKNOWN_WELL_2"])

        assert len(result["comparison_matrix"]) == 2
        for entry in result["comparison_matrix"]:
            assert entry["status"] == "NOT_FOUND"


# =============================================================================
# 7. ALERT TIMELINE
# =============================================================================

class TestAlertTimeline:
    def test_timeline_returns_sorted_entries(self):
        """Timeline entries should be sorted by depth ascending."""
        db = get_test_db()
        result = NexusEngine.get_alert_timeline(db)

        assert "timeline" in result
        entries = result["timeline"]
        if len(entries) > 1:
            for i in range(len(entries) - 1):
                assert entries[i]["depth_md_m"] <= entries[i + 1]["depth_md_m"]

    def test_timeline_well_filter(self):
        """Timeline should filter by well_id when provided."""
        db = get_test_db()
        well = db.query(Well).first()
        if not well:
            pytest.skip("No wells in test database")

        result = NexusEngine.get_alert_timeline(db, well_id=well.well_id)

        assert result["well_filter"] == well.well_id
        for entry in result["timeline"]:
            assert entry["well_id"] == well.well_id


# =============================================================================
# 8. API ENDPOINT INTEGRATION TESTS
# =============================================================================

class TestNexusAPI:
    def test_api_nexus_health(self):
        """GET /api/v1/nexus/health should return system health."""
        response = client.get("/api/v1/nexus/health")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "modules" in data

    def test_api_nexus_kpis(self):
        """GET /api/v1/nexus/kpis should return KPI metrics."""
        response = client.get("/api/v1/nexus/kpis")
        assert response.status_code == 200
        data = response.json()
        assert "kpis" in data

    def test_api_nexus_operations_log(self):
        """GET /api/v1/nexus/operations-log should return structured log."""
        response = client.get("/api/v1/nexus/operations-log?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "operations_log" in data

    def test_api_nexus_fuse_well(self):
        """GET /api/v1/nexus/fuse/{well_id} should return fused intelligence."""
        # Get a well from the database directly
        db = get_test_db()
        well = db.query(Well).first()
        if well:
            response = client.get(f"/api/v1/nexus/fuse/{well.well_id}")
        else:
            response = client.get("/api/v1/nexus/fuse/NO-15_9-F-14")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_api_nexus_fuse_nonexistent(self):
        """GET /api/v1/nexus/fuse/FAKE_WELL should abstain gracefully."""
        response = client.get("/api/v1/nexus/fuse/FAKE_WELL_XYZ_999")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "WELL_NOT_FOUND"

    def test_api_nexus_compare_wells(self):
        """POST /api/v1/nexus/compare should return comparison matrix."""
        response = client.post(
            "/api/v1/nexus/compare",
            json={"well_ids": ["NO-15/9-F-11A", "NO-15/9-F-12"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert "comparison_matrix" in data

    def test_api_nexus_compare_too_few_wells(self):
        """POST /api/v1/nexus/compare with 1 well should return 400."""
        response = client.post(
            "/api/v1/nexus/compare",
            json={"well_ids": ["ONLY_ONE"]}
        )
        assert response.status_code == 400

    def test_api_nexus_timeline(self):
        """GET /api/v1/nexus/timeline should return alert timeline."""
        response = client.get("/api/v1/nexus/timeline")
        assert response.status_code == 200
        data = response.json()
        assert "timeline" in data
        assert "total_entries" in data

    def test_api_nexus_summary(self):
        """GET /api/v1/nexus/summary should return lightweight summary."""
        response = client.get("/api/v1/nexus/summary")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "modules" in data
        assert "wells_loaded" in data

    def test_api_nexus_redirect(self):
        """GET /app/nexus should redirect to nexus.html."""
        response = client.get("/app/nexus", follow_redirects=False)
        assert response.status_code in (301, 302, 303, 307)
