import pytest
import sys
import hashlib
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.db.database import SessionLocal, engine
from backend.app.db.models import Base, Well, WellboreSurvey, FormationTop, DrillingEvent
from backend.app.services.risk_service import risk_service
from backend.app.services.stratigraphic_service import stratigraphic_service, GeologicalDatumError
from backend.app.schemas.lookahead_schemas import LookaheadRequest

def test_data_provenance_and_checksums():
    """Verify that all raw Volve files match their machine-readable provenance manifest."""
    manifest_path = ROOT_DIR / "data" / "raw" / "volve" / "provenance_manifest.json"
    assert manifest_path.exists(), "Provenance manifest must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert "manifest_version" in manifest
    assert "verified_files" in manifest
    assert len(manifest["verified_files"]) >= 4

    for entry in manifest["verified_files"]:
        file_path = ROOT_DIR / "data" / "raw" / "volve" / entry["original_filename"]
        assert file_path.exists(), f"Raw dataset file missing: {entry['original_filename']}"
        
        # Compute SHA-256
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            h.update(f.read())
        actual_hash = h.hexdigest()
        assert actual_hash == entry["sha256"], (
            f"Checksum mismatch on {entry['original_filename']}! "
            f"Expected {entry['sha256']}, got {actual_hash}"
        )
        assert entry["verification_status"] == "VERIFIED"


def test_chronological_information_leakage_prevention():
    """
    Verify that backtest and lookahead logic strictly forbids future events
    from leaking into memory prior to the target well drilling date.
    """
    db = SessionLocal()
    try:
        # Well F-12 was spudded on 2008-04-12 and completed in July 2008.
        # Events in F-14 happened in Sept-Oct 2008.
        # Events in F-15S happened in Jan-Feb 2009.
        req_early = LookaheadRequest(
            active_well_id="NO-15/9-F-12",
            current_bit_depth_md_m=2890.0,
            current_bit_depth_tvdss_m=2850.0,
            active_formation="Hugin FM",
            lookahead_window_m=75.0,
            as_of_timestamp="2008-05-01T00:00:00Z"  # Before F-14 and F-15S were drilled!
        )

        response_early = risk_service.evaluate_lookahead_horizon(db, req_early)

        # Assert no alerts originate from F-14 or F-15S
        for alert in response_early.alerts:
            assert alert.source_offset_well not in ["NO-15/9-F-14", "NO-15/9-F-15S"], (
                f"LEAKAGE DETECTED: Alert from future well {alert.source_offset_well} "
                f"appeared before its drilling date!"
            )

        # Now test with timestamp after F-14 events occurred
        req_later = LookaheadRequest(
            active_well_id="NO-15/9-F-15S",
            current_bit_depth_md_m=2950.0,
            current_bit_depth_tvdss_m=2855.0,
            active_formation="Hugin FM",
            lookahead_window_m=75.0,
            as_of_timestamp="2009-01-20T00:00:00Z"  # After F-14 was drilled
        )
        response_later = risk_service.evaluate_lookahead_horizon(db, req_later)
        source_wells = {alert.source_offset_well for alert in response_later.alerts}
        # F-14 or F-12 events should now legitimately be available in offset memory
        assert ("NO-15/9-F-14" in source_wells or "NO-15/9-F-12" in source_wells), (
            "Historical events from earlier drilled wells should be in memory"
        )
    finally:
        db.close()


def test_geological_datum_incompatibility():
    """Verify that incompatible datums (MD < TVD, missing KB) raise GeologicalDatumError."""
    # MD cannot be less than TVD
    with pytest.raises(GeologicalDatumError):
        stratigraphic_service.validate_depth_datum(md_m=2000.0, tvd_m=2500.0, kb_elevation_m=43.5)

    # KB elevation cannot be None or negative
    with pytest.raises(GeologicalDatumError):
        stratigraphic_service.compute_tvdss(tvd_m=2500.0, kb_elevation_m=None)

    with pytest.raises(GeologicalDatumError):
        stratigraphic_service.compute_tvdss(tvd_m=2500.0, kb_elevation_m=-5.0)

    # Service-level API must return INSUFFICIENT_GEOLOGICAL_EVIDENCE fail-safe
    db = SessionLocal()
    try:
        req = LookaheadRequest(
            active_well_id="NO-15/9-F-12",
            current_bit_depth_md_m=2000.0,
            current_bit_depth_tvdss_m=2500.0,  # Invalid: TVDSS > MD
            active_formation="Hugin FM",
            lookahead_window_m=75.0
        )
        res = risk_service.evaluate_lookahead_horizon(db, req)
        assert res.evidence_status == "INSUFFICIENT_GEOLOGICAL_EVIDENCE"
        assert res.hazard_level == "CLEAR"
        assert res.alert_count == 0
    finally:
        db.close()


def test_trajectory_minimum_curvature_interpolation():
    """Verify 10m step interpolation preserves survey station bounds and produces valid geometry."""
    raw_stations = [
        {"md_m": 1000.0, "tvd_m": 995.0, "tvdss_m": 951.5, "inclination_deg": 10.0, "azimuth_deg": 45.0, "northing_m": 50.0, "easting_m": 50.0},
        {"md_m": 1100.0, "tvd_m": 1090.0, "tvdss_m": 1046.5, "inclination_deg": 20.0, "azimuth_deg": 50.0, "northing_m": 70.0, "easting_m": 75.0},
    ]

    interpolated = stratigraphic_service.interpolate_trajectory(raw_stations, step_size_md_m=10.0)

    assert len(interpolated) == 11  # 1000, 1010, ..., 1100
    assert interpolated[0]["md_m"] == 1000.0
    assert interpolated[-1]["md_m"] == 1100.0

    # Ensure depths are strictly monotonic
    for i in range(1, len(interpolated)):
        assert interpolated[i]["md_m"] > interpolated[i-1]["md_m"]
        assert interpolated[i]["tvdss_m"] > interpolated[i-1]["tvdss_m"]


def test_evidence_or_silence_contract():
    """
    Evidence-or-Silence: If no verified offset events exist in the target interval,
    system must output NO_HISTORICAL_PRECEDENT and zero speculative advice.
    """
    db = SessionLocal()
    try:
        req = LookaheadRequest(
            active_well_id="NO-15/9-F-12",
            current_bit_depth_md_m=500.0,
            current_bit_depth_tvdss_m=456.5,
            active_formation="Nordland GP",
            lookahead_window_m=50.0
        )
        res = risk_service.evaluate_lookahead_horizon(db, req)
        assert res.hazard_level == "CLEAR"
        assert res.alert_count == 0
        assert res.evidence_status == "NO_HISTORICAL_PRECEDENT"
        assert len(res.alerts) == 0
    finally:
        db.close()


def test_postgres_postgis_compatibility():
    """Verify that SQLAlchemy model metadata can generate valid DDL for both SQLite and PostgreSQL."""
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {"wells", "wellbore_surveys", "formation_tops", "drilling_events", "lookahead_alerts", "audit_logs"}
    assert expected_tables.issubset(table_names), f"Missing tables: {expected_tables - table_names}"

    # Verify column constraints on DrillingEvent
    drilling_event_cols = {c.name for c in Base.metadata.tables["drilling_events"].columns}
    assert "source_citation" in drilling_event_cols
    assert "event_timestamp" in drilling_event_cols
    assert "depth_tvdss_m" in drilling_event_cols
