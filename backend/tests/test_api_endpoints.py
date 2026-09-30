import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app

client = TestClient(app)

def test_root_endpoint_serves_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "eRTMAC-NWIS" in response.text
    assert "Nearby Wells Intelligence" in response.text

def test_api_status_endpoint():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert data["evidence_contract"] == "STRICT_EVIDENCE_OR_SILENCE"

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_wells_api():
    response = client.get("/api/v1/wells")
    assert response.status_code == 200
    wells = response.json()
    assert len(wells) >= 5

def test_well_trajectory_api():
    response = client.get("/api/v1/wells/trajectory?well_id=NO-15/9-F-12")
    assert response.status_code == 200
    surveys = response.json()
    assert len(surveys) > 0

def test_well_formations_api():
    response = client.get("/api/v1/wells/formations?well_id=NO-15/9-F-12")
    assert response.status_code == 200
    tops = response.json()
    assert len(tops) > 0

def test_similarity_rank_api():
    payload = {
        "active_well_id": "NO-15/9-F-12",
        "target_formation": "Hugin FM",
        "current_depth_tvdss_m": 2850.0,
        "search_radius_km": 5.0
    }
    response = client.post("/api/v1/similarity/rank", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["ranked_offsets"]) > 0

def test_lookahead_scan_api():
    payload = {
        "active_well_id": "NO-15/9-F-12",
        "current_bit_depth_md_m": 2893.5,
        "current_bit_depth_tvdss_m": 2850.0,
        "active_formation": "Hugin FM",
        "lookahead_window_m": 75.0
    }
    response = client.post("/api/v1/lookahead/scan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "hazard_level" in data
    assert "alerts" in data

def test_ask_nwis_api():
    payload = {
        "query": "What lost circulation incidents occurred in Hugin formation?",
        "target_formation": "Hugin FM"
    }
    response = client.post("/api/v1/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["has_sufficient_evidence"] is True
    assert len(data["citations"]) > 0

def test_backtest_run_api():
    response = client.post("/api/v1/backtest/run?held_out_well_id=NO-15/9-F-12&lookahead_window_m=75.0")
    assert response.status_code == 200
    data = response.json()
    assert data["held_out_well_id"] == "NO-15/9-F-12"
    assert data["proactively_flagged_true_positives"] > 0
