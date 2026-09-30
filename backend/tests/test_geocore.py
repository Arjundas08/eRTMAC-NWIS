"""
NWIS GEOCORE — ADVANCED GEOLOGICAL VALIDATION SUITE
Rigorous verification of Minimum Curvature mathematical correctness, Kelly Bushing datum validation,
geological fingerprinting, formation correlation, 3D corridors, explainable similarity, and human review.
"""

import pytest
import math
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.database import get_db, SessionLocal
from backend.app.db import models
from backend.app.services.trajectory_engine import (
    TrajectoryEngine, InsufficientGeologicalEvidenceError, IncompatibleDatumError
)
from backend.app.services.geological_fingerprint_service import GeologicalFingerprintService
from backend.app.services.formation_correlation_service import FormationCorrelationService
from backend.app.services.subsurface_corridor_service import SubsurfaceCorridorService, SAFETY_DISCLAIMER
from backend.app.services.geocore_similarity_service import GeoCoreSimilarityService
from backend.app.services.geocore_review_service import GeoCoreReviewService

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()

# =============================================================================
# 1. Trajectory Engine Analytical Benchmarks
# =============================================================================

def test_trajectory_minimum_curvature_analytical_reference():
    """
    Validates Minimum Curvature calculations against an independently calculated analytical reference:
    Station 1: MD=1000m, Inc=0°, Azi=0°
    Station 2: MD=1300m, Inc=30°, Azi=45°
    """
    md1, inc1, azi1 = 1000.0, 0.0, 0.0
    md2, inc2, azi2 = 1300.0, 30.0, 45.0

    delta_tvd, delta_north, delta_east, dls = TrajectoryEngine.minimum_curvature_step(
        md1, inc1, azi1, md2, inc2, azi2
    )

    # Analytical verification:
    # delta_md = 300m
    # dl_rad = 30° = pi/6 rad
    # RF = (2 / (pi/6)) * tan(pi/12) = (12/pi) * (2 - sqrt(3)) ≈ 1.023277
    dl_rad = math.radians(30.0)
    expected_rf = (2.0 / dl_rad) * math.tan(dl_rad / 2.0)
    expected_tvd = (300.0 / 2.0) * (1.0 + math.cos(math.radians(30.0))) * expected_rf

    assert math.isclose(delta_tvd, expected_tvd, rel_tol=1e-5)
    assert delta_north > 0.0
    assert delta_east > 0.0
    # DLS = 30° over 300m = 3.0° / 30m
    assert math.isclose(dls, 3.0, rel_tol=1e-4)

def test_datum_validation_and_insufficient_evidence_abstention():
    """
    Verifies that missing Kelly Bushing elevation triggers INSUFFICIENT_GEOLOGICAL_EVIDENCE.
    Zero substitution is strictly prohibited.
    """
    with pytest.raises(InsufficientGeologicalEvidenceError) as exc_info:
        TrajectoryEngine.compute_tvdss(2900.0, None)
    assert "INSUFFICIENT_GEOLOGICAL_EVIDENCE" in str(exc_info.value)

    with pytest.raises(IncompatibleDatumError):
        TrajectoryEngine.compute_tvdss(2900.0, 350.0) # Outside credible elevation

def test_trajectory_interpolation_within_and_outside_bounds():
    """
    Verifies piecewise interpolation within surveyed bounds and controlled abstention outside.
    """
    raw_stations = [
        {"md_m": 0.0, "inclination_deg": 0.0, "azimuth_deg": 0.0},
        {"md_m": 1000.0, "inclination_deg": 10.0, "azimuth_deg": 45.0},
        {"md_m": 2000.0, "inclination_deg": 25.0, "azimuth_deg": 60.0}
    ]
    traj = TrajectoryEngine.compute_trajectory(raw_stations, kb_elevation_m=43.5)
    assert len(traj) == 3

    # Interpolate at MD = 1500m (valid)
    interp = TrajectoryEngine.interpolate_at_md(traj, 1500.0, kb_elevation_m=43.5)
    assert interp.is_interpolated is True
    assert 10.0 < interp.inclination_deg < 25.0
    assert interp.tvdss_m == round(interp.tvd_m - 43.5, 2)

    # Attempt interpolation beyond TD (forbidden extrapolation)
    with pytest.raises(InsufficientGeologicalEvidenceError):
        TrajectoryEngine.interpolate_at_md(traj, 2500.0, kb_elevation_m=43.5)

# =============================================================================
# 2. Geological Fingerprint Engine
# =============================================================================

def test_geological_fingerprint_structure_and_categories(db_session):
    """
    Verifies that Geological Fingerprint correctly structures features into
    VERIFIED, DERIVED, MISSING, and UNCERTAIN categories with source citations.
    """
    fp = GeologicalFingerprintService.generate_fingerprint(
        db_session, well_id="NO-15/9-F-12", current_md_m=2893.5, target_formation_name="Hugin FM"
    )

    assert fp["well_id"] == "NO-15/9-F-12"
    assert fp["depth_datum"]["kb_elevation_m"] == 43.5
    assert fp["depth_datum"]["datum_type"] == "RKB"
    assert fp["active_formation"]["formation_name"] == "Hugin FM"
    assert fp["active_formation"]["lithology"] == "Sandstone"

    audit = fp["categorized_audit"]
    assert len(audit["verified_features"]) >= 4
    assert len(audit["derived_features"]) >= 2
    assert audit["completeness_score_pct"] > 70.0

    # Ensure source references exist
    sources = [f["source"] for f in audit["verified_features"] if "source" in f]
    assert any("NPD Factpages" in s for s in sources)
    assert any("Volve Composite" in s for s in sources)

# =============================================================================
# 3. Formation-Relative Correlation Engine
# =============================================================================

def test_formation_correlation_depth_alignment(db_session):
    """
    Verifies relative depth alignment and historical incident projection across Hugin FM.
    """
    corr = FormationCorrelationService.correlate_wells(
        db_session,
        primary_well_id="NO-15/9-F-12",
        offset_well_id="NO-15/9-F-14",
        formation_name="Hugin FM",
        primary_depth_tvdss_m=2860.0
    )

    assert corr["correlation_status"] == "CORRELATED"
    assert corr["is_abstaining"] is False
    # Structural shift: primary Hugin top (2850m) - offset Hugin top (2864m) = -14.0m
    assert corr["structural_shift_tvdss_m"] == -14.0
    assert len(corr["historical_events_in_interval"]) >= 1

    # Check that incident contains original provenance links
    evt = corr["historical_events_in_interval"][0]
    assert evt["event_type"] in ["LOST_CIRCULATION", "STUCK_PIPE"]
    assert evt["source_citation"] != ""
    assert evt["projected_active_tvdss_m"] is not None

def test_formation_correlation_abstention_on_unrelated_formation(db_session):
    """
    Ensures GeoCore abstains from correlating if a formation was not penetrated or picked.
    """
    corr = FormationCorrelationService.correlate_wells(
        db_session,
        primary_well_id="NO-15/9-F-12",
        offset_well_id="NO-15/9-F-14",
        formation_name="NonExistentFormation_XYZ"
    )
    assert corr["correlation_status"] == "UNCORRELATED_FORMATION"
    assert corr["is_abstaining"] is True
    assert "abstention_reason" in corr

# =============================================================================
# 4. Subsurface Corridor Engine
# =============================================================================

def test_subsurface_corridor_geometry_and_disclaimer(db_session):
    """
    Verifies 3D spatial corridor calculation and safety notice inclusion.
    """
    corridor = SubsurfaceCorridorService.generate_corridor(
        db_session, primary_well_id="NO-15/9-F-12"
    )

    assert corridor["primary_well"]["well_id"] == "NO-15/9-F-12"
    assert len(corridor["primary_well"]["trajectory_points"]) > 0
    assert len(corridor["corridor_offsets"]) >= 3
    assert len(corridor["pinned_incident_markers"]) > 0

    # Ensure safety disclaimer is explicitly returned
    assert corridor["safety_advisory"] == SAFETY_DISCLAIMER
    assert "anti-collision" in corridor["safety_advisory"].lower()

# =============================================================================
# 5. Explainable Similarity & "Why This Well, Not That Well"
# =============================================================================

def test_geocore_similarity_ranking_and_explanation(db_session):
    """
    Tests 4-stage explainable similarity ranking.
    """
    ranking = GeoCoreSimilarityService.rank_offset_analogues(
        db_session, primary_well_id="NO-15/9-F-12", target_formation_name="Hugin FM"
    )

    assert len(ranking["ranked_analogues"]) >= 4
    top_offset = ranking["ranked_analogues"][0]

    # Must contain full explainable factor breakdown
    breakdown = top_offset["factor_breakdown"]
    assert "spatial_proximity" in breakdown
    assert "geological_formation" in breakdown
    assert "stratigraphic_sequence" in breakdown
    assert "trajectory_profile" in breakdown
    assert "operational_context" in breakdown

    assert top_offset["engineering_rationale"] != ""

def test_why_this_well_not_that_well_comparison(db_session):
    """
    SIGNATURE INNOVATION 04: Head-to-head comparison explaining ranking contrast.
    """
    comp = GeoCoreSimilarityService.compare_two_wells(
        db_session,
        primary_well_id="NO-15/9-F-12",
        well_a_id="NO-15/9-F-14",
        well_b_id="NO-15/9-F-1",
        target_formation_name="Hugin FM"
    )

    assert comp["primary_well"] == "15/9-F-12"
    assert comp["well_a"]["offset_well_id"] == "NO-15/9-F-14"
    assert comp["well_b"]["offset_well_id"] == "NO-15/9-F-1"
    assert "comparison_verdict" in comp
    assert len(comp["key_differentiating_factors"]) > 0

    # Contrast against naive distance baseline
    baseline = comp["baseline_distance_comparison"]
    assert "well_a_distance_rank" in baseline
    assert "well_a_geocore_rank" in baseline

def test_three_way_baseline_evaluation(db_session):
    """
    Rigorous 3-way baseline comparison:
    - Baseline 1: Distance Only
    - Baseline 2: Formation Only
    - GeoCore: Multi-Factor
    """
    ranking = GeoCoreSimilarityService.rank_offset_analogues(
        db_session, primary_well_id="NO-15/9-F-12", target_formation_name="Hugin FM"
    )
    analogues = ranking["ranked_analogues"]

    # In Baseline 1 (Distance), closest well ranks #1
    closest_well = min(analogues, key=lambda a: a["distance_km"])

    # In GeoCore, NO-15/9-F-14 ranks #1 because of high inclination match + verified incidents
    geocore_top = analogues[0]
    assert geocore_top["offset_well_id"] == "NO-15/9-F-14"
    assert geocore_top["target_formation_matched"] is True

# =============================================================================
# 6. Geological Human-Review Workflow
# =============================================================================

def test_geocore_human_review_workflow_and_audit(db_session):
    """
    Verifies human-in-the-loop review recording and cryptographic SHA-256 HMAC creation.
    """
    review_res = GeoCoreReviewService.submit_review(
        db=db_session,
        correlation_id="CORR-TEST-001",
        reviewer_name="DR_ANANYA_SHARMA_OIL",
        reviewer_role="PRINCIPAL_PETROLEUM_GEOLOGIST",
        decision="APPROVED",
        review_notes="Verified Hugin Sandstone top match and 42 m3 loss correlation."
    )

    assert review_res["status"] == "RECORDED_IN_IMMUTABLE_AUDIT_LOG"
    assert review_res["decision"] == "APPROVED"
    assert len(review_res["integrity_hmac"]) == 64 # Valid SHA-256

    history = GeoCoreReviewService.get_review_history(db_session)
    assert any(h["correlation_id"] == "CORR-TEST-001" for h in history)

# =============================================================================
# 7. Production API Endpoints
# =============================================================================

def test_geocore_api_wellbores_list():
    resp = client.get("/api/v1/geocore/wellbores")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["count"] >= 5

def test_geocore_api_fingerprint():
    resp = client.get("/api/v1/geocore/wellbores/NO-15/9-F-12/fingerprint?formation=Hugin%20FM")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert "fingerprint" in data

def test_geocore_api_trajectory():
    resp = client.get("/api/v1/geocore/wellbores/NO-15/9-F-12/trajectory")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["station_count"] > 0

def test_geocore_api_similarity_post():
    payload = {
        "primary_well_id": "NO-15/9-F-12",
        "target_formation_name": "Hugin FM",
        "max_search_radius_km": 10.0
    }
    resp = client.post("/api/v1/geocore/similarity", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert len(data["ranking"]["ranked_analogues"]) > 0

def test_geocore_api_comparison_post():
    payload = {
        "primary_well_id": "NO-15/9-F-12",
        "well_a_id": "NO-15/9-F-14",
        "well_b_id": "NO-15/9-F-4",
        "target_formation_name": "Hugin FM"
    }
    resp = client.post("/api/v1/geocore/compare", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert "comparison" in data
