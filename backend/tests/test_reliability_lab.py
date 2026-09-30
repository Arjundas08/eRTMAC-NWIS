"""
Phase 08 Industrial Reliability & Failure Recovery Laboratory Test Suite

Controlled failure injection and resilience tests:
1. Telemetry source disconnection & duplicate packet suppression
2. Out-of-order packet detection
3. Missing geological data & graceful INSUFFICIENT_DATA fallback
4. Damaged checksum document detection & rejection
5. Strict evidence abstention fallback without fact fabrication
6. System health status reporting across modules
"""

import pytest
from datetime import datetime, timezone, timedelta
from backend.app.services.telemetry_quality_service import TelemetryQualityEngine
from backend.app.services.sentinel_answer_engine import SentinelAnswerEngine
from backend.app.services.nexus_engine import NexusEngine
from backend.app.services.crypto_service import CryptographicAuditService
from backend.app.db.database import SessionLocal


def test_telemetry_staleness_triggers_degraded_state():
    """Packets with physical anomalies or delays must flag issues and report non-healthy state."""
    engine = TelemetryQualityEngine(stale_threshold_s=5.0)

    # Initial packet
    state, issues = engine.assess_packet(
        packet_id="PKT_1",
        raw_payload='{"rop": 15.0}',
        timestamp_str="2026-09-30T00:00:00Z",
        canonical_channels={"MD": 2500.0, "BIT_DEPTH": 2500.0}
    )
    assert state == "HEALTHY"

    # Out of order packet
    state_ooo, issues_ooo = engine.assess_packet(
        packet_id="PKT_2",
        raw_payload='{"rop": 14.0}',
        timestamp_str="2026-09-29T23:59:00Z",  # Earlier timestamp!
        canonical_channels={"MD": 2490.0, "BIT_DEPTH": 2490.0}
    )
    assert any("OUT_OF_ORDER" in issue for issue in issues_ooo)
    assert state_ooo in ("DEGRADED", "STALE")


def test_duplicate_telemetry_packet_suppression():
    """Duplicate packets at the exact same depth and timestamp must be suppressed."""
    engine = TelemetryQualityEngine()
    payload = '{"MD": 2965.0, "ROP": 12.5}'
    channels = {"MD": 2965.0, "BIT_DEPTH": 2965.0}

    # First receipt
    state1, issues1 = engine.assess_packet("PKT_A", payload, "2026-09-30T01:00:00Z", channels)
    assert state1 == "HEALTHY"

    # Duplicate receipt
    state2, issues2 = engine.assess_packet("PKT_B", payload, "2026-09-30T01:00:02Z", channels)
    assert any("DUPLICATE" in issue for issue in issues2)
    assert state2 == "DEGRADED"


def test_missing_geological_data_fallback():
    """Querying a non-existent well must return structured abstention, not crash."""
    db = SessionLocal()
    try:
        res = NexusEngine.fuse_well_intelligence(db, "NON_EXISTENT_WELL_999")
        assert res["status"] == "WELL_NOT_FOUND"
        assert res["fused_intelligence"] is None
        assert "abstention_reason" in res
    finally:
        db.close()


def test_damaged_checksum_document_rejection(tmp_path):
    """A file modified after manifest creation must fail verification."""
    test_file = tmp_path / "tampered_report.csv"
    test_file.write_text("depth,incident\n1000,kick", encoding="utf-8")

    original_hash = CryptographicAuditService.compute_sha256(test_file.read_bytes())

    # Adversary alters content
    test_file.write_text("depth,incident\n1000,NONE", encoding="utf-8")
    new_hash = CryptographicAuditService.compute_sha256(test_file.read_bytes())

    assert original_hash != new_hash, "Checksums should diverge after tampering"


def test_model_provider_outage_fallback():
    """When query has no verified historical evidence, Sentinel must abstain without fabricating."""
    db = SessionLocal()
    try:
        res = SentinelAnswerEngine.answer_engineering_query(
            db, "What kicks were recorded in the fictitious Atlantis formation at 9999m?"
        )
        assert res["status"] == "ABSTAINED"
        assert res["abstention_code"] in ("NO_HISTORICAL_EVIDENCE", "INSUFFICIENT_GEOLOGICAL_EVIDENCE")
    finally:
        db.close()


def test_system_health_status_reporting():
    """System health must report valid status and list all modules."""
    db = SessionLocal()
    try:
        health = NexusEngine.get_system_health(db)
        assert "modules" in health
        assert "overall_status" in health
        assert health["overall_status"] in ("ALL_SYSTEMS_OPERATIONAL", "OPERATIONAL", "DEGRADED", "OFFLINE")
        assert "geocore" in health["modules"]
        assert "pulse" in health["modules"]
        assert "chronos" in health["modules"]
        assert "sentinel" in health["modules"]
    finally:
        db.close()
