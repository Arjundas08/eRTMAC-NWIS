"""
NWIS PULSE — Automated Verification & Regression Suite (Phase 06)
Verifies:
1. WITSML 1.4.1.1 and 2.1 XML/JSON Parsing
2. ETP 1.2 Protocol Capability Negotiation
3. Petroleum Unit Conversions & Canonical Schema Normalization
4. Data Quality Engine (Duplicates, Out-of-Order, Staleness, Physical Gating)
5. GeoCore Live Geological Context Enrichment
6. Operational Anomaly Rules & Two-Layer Evidence Passport
7. Human-in-the-Loop Advisory Lifecycle & Audit Events
8. Strict Source-Mode Segregation (Live, Replay, Synthetic)
9. Read-Only Invariant Enforcement
10. End-to-End FastAPI REST API Endpoints
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.telemetry_adapters import (
    WITSML1411Adapter, WITSML21Adapter, ETP12Adapter,
    HistoricalReplayAdapter, SyntheticDemoAdapter
)
from backend.app.services.telemetry_normalizer import (
    convert_unit, normalize_mnemonic, canonicalize_packet
)
from backend.app.services.telemetry_quality_service import TelemetryQualityEngine
from backend.app.services.pulse_engine import PulseEngine
from backend.app.db.database import SessionLocal
from backend.app.db.models import OperationalAdvisory, AdvisoryReviewEvent

client = TestClient(app)


# =============================================================================
# 1. ADAPTER TESTS (WITSML 1.4.1.1, 2.1, ETP 1.2)
# =============================================================================

def test_witsml_1411_adapter_parsing():
    adapter = WITSML1411Adapter(source_id="SRC_TEST_WITSML", source_mode="GENUINE_RECORDED_REPLAY")
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <logs xmlns="http://www.witsml.org/schemas/1series" version="1.4.1.1">
      <log uidWell="VOLVE" uidWellbore="NO 15/9-F-12" uid="LOG01">
        <nameWellbore>NO 15/9-F-12</nameWellbore>
        <logCurveInfo uid="c1">
          <mnemonic>MD</mnemonic>
          <unit>m</unit>
        </logCurveInfo>
        <logCurveInfo uid="c2">
          <mnemonic>ROPA</mnemonic>
          <unit>m/h</unit>
        </logCurveInfo>
        <logCurveInfo uid="c3">
          <mnemonic>SPPA</mnemonic>
          <unit>psi</unit>
        </logCurveInfo>
        <logData>
          <data>2505.5, 18.4, 3600.0</data>
          <data>2506.0, 19.1, 3620.0</data>
        </logData>
      </log>
    </logs>
    """
    records = adapter.parse_payload(sample_xml)
    assert len(records) == 2
    assert records[0]["wellbore_id"] == "NO 15/9-F-12"
    assert records[0]["source_mode"] == "GENUINE_RECORDED_REPLAY"
    assert records[0]["channels"]["MD"]["value"] == 2505.5
    assert records[0]["channels"]["ROPA"]["value"] == 18.4
    assert records[0]["channels"]["SPPA"]["unit"] == "psi"


def test_witsml_21_adapter_json():
    adapter = WITSML21Adapter(source_id="SRC_TEST_WITSML21", source_mode="AUTHORIZED_LIVE")
    payload = json.dumps({
        "wellbore_id": "NO 15/9-F-14",
        "timestamp": "2026-09-30T04:00:00Z",
        "channels": {
            "MD": {"value": 2410.0, "unit": "m"},
            "WOB": {"value": 115.0, "unit": "kN"},
            "STOR": {"value": 21.5, "unit": "kN.m"}
        }
    })
    records = adapter.parse_payload(payload)
    assert len(records) == 1
    assert records[0]["wellbore_id"] == "NO 15/9-F-14"
    assert records[0]["source_mode"] == "AUTHORIZED_LIVE"
    assert records[0]["channels"]["WOB"]["value"] == 115.0


def test_etp_12_adapter_capabilities_negotiation():
    adapter = ETP12Adapter(source_id="SRC_TEST_ETP", source_mode="AUTHORIZED_LIVE")
    caps = adapter.negotiate_capabilities()
    assert caps["etp_version"] == "1.2.0"
    assert caps["is_read_only"] is True
    assert "ChannelStreaming" in caps["supported_protocols"]
    assert caps["status"] == "NEGOTIATED"


# =============================================================================
# 2. UNIT CONVERSIONS & CANONICAL SCHEMA
# =============================================================================

def test_unit_conversions():
    # Pressure: psi -> kPa
    kpa, u = convert_unit(100.0, "psi", "kPa")
    assert round(kpa, 2) == 689.48
    assert u == "kPa"

    # Force: klbs -> kN
    kn, u = convert_unit(10.0, "klbs", "kN")
    assert round(kn, 2) == 44.48
    assert u == "kN"

    # Depth: ft -> m
    m, u = convert_unit(1000.0, "ft", "m")
    assert round(m, 2) == 304.80
    assert u == "m"

    # Mud weight: ppg -> sg
    sg, u = convert_unit(10.0, "ppg", "sg")
    assert round(sg, 3) == 1.198


def test_canonicalize_packet():
    raw_packet = {
        "DMEA": {"value": 8200.0, "unit": "ft"},
        "ROPA": {"value": 45.0, "unit": "ft/h"},
        "WOBA": {"value": 25.0, "unit": "klbs"},
        "SPPA": {"value": 3500.0, "unit": "psi"}
    }
    result = canonicalize_packet(raw_packet)
    canonical = result["canonical_channels"]
    meta = result["channel_metadata"]

    assert "MD" in canonical
    assert round(canonical["MD"], 1) == 2499.4 # 8200 ft * 0.3048
    assert "ROP" in canonical
    assert round(canonical["ROP"], 1) == 13.7  # 45 ft/h * 0.3048
    assert "WOB" in canonical
    assert round(canonical["WOB"], 1) == 111.2 # 25 klbs * 4.44822
    assert "SPP" in canonical
    assert round(canonical["SPP"], 0) == 24132.0 # 3500 psi * 6.89476


# =============================================================================
# 3. DATA QUALITY & STALENESS ENGINE
# =============================================================================

def test_data_quality_duplicate_and_out_of_order():
    engine = TelemetryQualityEngine(stale_threshold_s=5.0)

    # First packet: Valid
    state, issues = engine.assess_packet(
        packet_id="PKT_1",
        raw_payload='{"test": 1}',
        timestamp_str="2026-09-30T04:10:00Z",
        canonical_channels={"MD": 2500.0, "BIT_DEPTH": 2500.0}
    )
    assert state == "HEALTHY"
    assert len(issues) == 0

    # Second packet: Exact Duplicate
    state, issues = engine.assess_packet(
        packet_id="PKT_2",
        raw_payload='{"test": 1}', # Identical payload
        timestamp_str="2026-09-30T04:10:02Z",
        canonical_channels={"MD": 2500.0, "BIT_DEPTH": 2500.0}
    )
    assert "DUPLICATE_PACKET_SUPPRESSED" in issues
    assert state == "DEGRADED"

    # Third packet: Out of Order (timestamp earlier than high watermark)
    state, issues = engine.assess_packet(
        packet_id="PKT_3",
        raw_payload='{"test": 2}',
        timestamp_str="2026-09-30T04:05:00Z", # In the past
        canonical_channels={"MD": 2501.0, "BIT_DEPTH": 2501.0}
    )
    assert "OUT_OF_ORDER_PACKET" in issues


def test_data_quality_physical_bounds_check():
    engine = TelemetryQualityEngine()
    state, issues = engine.assess_packet(
        packet_id="PKT_IMPLAUSIBLE",
        raw_payload='{"test": 3}',
        timestamp_str="2026-09-30T04:12:00Z",
        canonical_channels={
            "MD": 2500.0,
            "BIT_DEPTH": 2500.0,
            "MUD_WEIGHT": 4.5, # Physically implausible drilling mud weight (max 2.5)
            "RPM": 850.0       # Implausible rig rotary speed
        }
    )
    assert state == "DEGRADED"
    assert any("SENSOR_OUT_OF_BOUNDS_MUD_WEIGHT" in i for i in issues)
    assert any("SENSOR_OUT_OF_BOUNDS_RPM" in i for i in issues)


# =============================================================================
# 4. PULSE ENGINE & TWO-LAYER EVIDENCE PASSPORT
# =============================================================================

def test_pulse_engine_ingest_and_two_layer_evidence():
    import uuid
    test_well_id = f"NO 15/9-F-12-TEST-{uuid.uuid4().hex[:6]}"
    db = SessionLocal()
    try:
        engine = PulseEngine(db)

        # Ingest a kick-signature packet (flow out = 118%)
        kick_packet = {
            "timestamp": "2026-09-30T04:15:00Z",
            "channels": {
                "MD": {"value": 2515.0, "unit": "m"},
                "BIT_DEPTH": {"value": 2515.0, "unit": "m"},
                "TVD": {"value": 2340.0, "unit": "m"},
                "FLOW_IN": {"value": 2600.0, "unit": "L/min"},
                "FLOW_OUT": {"value": 118.0, "unit": "%"}, # Anomaly trigger
                "PIT_VOLUME": {"value": 145.2, "unit": "m³"},
                "SPP": {"value": 24500.0, "unit": "kPa"}
            }
        }

        res = engine.ingest_packet(
            source_id="SRC_VOLVE_HISTORICAL",
            wellbore_id=test_well_id,
            raw_payload=json.dumps(kick_packet),
            source_mode="GENUINE_RECORDED_REPLAY"
        )

        assert res["quality_state"] == "HEALTHY"
        assert res["depth_md"] == 2515.0
        assert res["formation"] != ""

        # Verify advisory generation and Two-Layer Evidence Passport
        adv = db.query(OperationalAdvisory).filter(
            OperationalAdvisory.wellbore_id == test_well_id,
            OperationalAdvisory.hazard_type == "KICK_GAS"
        ).order_by(OperationalAdvisory.created_at.desc()).first()

        assert adv is not None
        assert adv.severity == "CRITICAL"
        assert adv.advisory_state == "NEW"

        # Layer A check: Telemetry Evidence
        layer_a = json.loads(adv.telemetry_evidence_json)
        assert layer_a["layer"] == "LAYER_A_CURRENT_TELEMETRY"
        assert layer_a["channel_triggered"] == "FLOW_OUT"
        assert layer_a["measured_value"] == 118.0

        # Layer B check: Verified Historical Evidence
        layer_b = json.loads(adv.historical_evidence_json)
        assert layer_b["layer"] == "LAYER_B_VERIFIED_HISTORICAL"
        assert "offset_well" in layer_b
        assert "verified_passage" in layer_b

        # Driller Action & Audit Logging
        ack_res = engine.acknowledge_advisory(
            advisory_id=adv.advisory_id,
            actor_id="DRILLER_TEST_01",
            comments="Confirmed flow increase on paddle. Shutting down mud pumps for flow check.",
            action="ACKNOWLEDGE"
        )
        assert ack_res["new_state"] == "ACKNOWLEDGED"

        audit_rec = db.query(AdvisoryReviewEvent).filter(
            AdvisoryReviewEvent.advisory_id == adv.advisory_id
        ).first()
        assert audit_rec is not None
        assert audit_rec.actor_id == "DRILLER_TEST_01"

    finally:
        db.close()


# =============================================================================
# 5. REST API ENDPOINTS INTEGRATION
# =============================================================================

def test_api_pulse_sources():
    response = client.get("/api/v1/pulse/sources")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 3
    # Check source modes are strictly classified
    modes = {s["source_mode"] for s in data["sources"]}
    assert "GENUINE_RECORDED_REPLAY" in modes
    assert "AUTHORIZED_LIVE" in modes
    assert "SYNTHETIC_DEMO" in modes


def test_api_pulse_live_and_inspector():
    # Live endpoint
    live_resp = client.get("/api/v1/pulse/live/NO%2015%2F9-F-12")
    assert live_resp.status_code == 200
    live_data = live_resp.json()
    assert live_data["wellbore_id"] == "NO 15/9-F-12"
    assert "md_m" in live_data
    assert "current_formation" in live_data
    assert "quality_state" in live_data

    # Inspector endpoint
    insp_resp = client.get("/api/v1/pulse/quality-inspector/NO%2015%2F9-F-12")
    assert insp_resp.status_code == 200
    insp_data = insp_resp.json()
    assert len(insp_data["channels"]) >= 10
    assert "freshness_lag_seconds" in insp_data


def test_api_pulse_advisories_and_action():
    adv_resp = client.get("/api/v1/pulse/advisories/NO%2015%2F9-F-12")
    assert adv_resp.status_code == 200
    adv_data = adv_resp.json()
    assert adv_data["count"] >= 1
    first_adv = adv_data["advisories"][0]
    assert "telemetry_evidence" in first_adv
    assert "historical_evidence" in first_adv

    # Post action
    act_resp = client.post(
        f"/api/v1/pulse/advisories/{first_adv['advisory_id']}/action",
        json={
            "actor_id": "SUPERINTENDENT_OIL",
            "actor_role": "DRILLING_SUPERINTENDENT",
            "action": "RESOLVE",
            "comments": "LCM pill placed across loss interval; flow balanced."
        }
    )
    assert act_resp.status_code == 200
    assert act_resp.json()["result"]["new_state"] == "RESOLVED"


def test_api_pulse_replay_step():
    step_resp = client.post(
        "/api/v1/pulse/replay/step",
        json={
            "wellbore_id": "NO 15/9-F-12",
            "source_mode": "GENUINE_RECORDED_REPLAY",
            "speed_factor": 1.0
        }
    )
    assert step_resp.status_code == 200
    data = step_resp.json()
    assert data["status"] == "SUCCESS"
    assert "stepped_measurement" in data
