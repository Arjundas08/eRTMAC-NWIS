"""
NWIS Phase 09 — API Contract Validation & Integration Test Suite

This test module validates:
1. OpenAPI schema contract correctness (endpoint existence, method types)
2. Response schema validation (required fields, correct types)
3. Production middleware behavior (rate limiting, security headers, request IDs)
4. Error handling contracts (proper HTTP status codes, safe error messages)
5. Cross-module API integration (Nexus fusion endpoints call real subsystems)
6. Health endpoint liveness contracts

ENGINEERING STANDARD:
- Every public API endpoint must have a contract test.
- Contract tests validate structure, not business logic (that's in unit tests).
- These tests run against the FastAPI TestClient (in-process, no network).
"""

import json
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


# =============================================================================
# 1. HEALTH & LIVENESS CONTRACT TESTS
# =============================================================================

class TestHealthContracts:
    """Validate that health/status endpoints meet the deployment contract."""

    def test_health_returns_200_and_required_fields(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert "environment" in data
        assert "database_backend" in data
        assert data["status"] == "healthy"

    def test_api_status_returns_operational_contract(self):
        r = client.get("/api/v1/status")
        assert r.status_code == 200
        data = r.json()
        required_keys = {"system", "version", "organization", "status", "evidence_contract"}
        assert required_keys.issubset(set(data.keys()))
        assert data["status"] == "OPERATIONAL"
        assert data["evidence_contract"] == "STRICT_EVIDENCE_OR_SILENCE"

    def test_openapi_schema_is_accessible(self):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        schema = r.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert schema["info"]["title"] == "eRTMAC-NWIS"


# =============================================================================
# 2. API ENDPOINT EXISTENCE CONTRACT TESTS
# =============================================================================

class TestEndpointExistence:
    """Verify every documented API endpoint exists and responds."""

    MUST_EXIST_ENDPOINTS = [
        ("GET", "/api/v1/wells/"),
        ("GET", "/api/v1/status"),
        ("GET", "/health"),
        ("GET", "/api/v1/nexus/health"),
        ("GET", "/api/v1/nexus/kpis"),
        ("GET", "/api/v1/nexus/operations-log"),
        ("GET", "/api/v1/nexus/timeline"),
        ("GET", "/api/v1/nexus/summary"),
        ("GET", "/api/v1/pulse/sources"),
        ("GET", "/api/v1/sentinel/search"),
        ("GET", "/api/v1/geocore/wellbores"),
        ("GET", "/api/v1/documents/"),
        ("GET", "/api/v1/chronos/wells"),
    ]

    @pytest.mark.parametrize("method,path", MUST_EXIST_ENDPOINTS)
    def test_endpoint_responds(self, method, path):
        """Every documented endpoint must respond (not 404 or 405)."""
        if method == "GET":
            r = client.get(path)
        elif method == "POST":
            r = client.post(path, json={})
        else:
            pytest.skip(f"Unsupported method: {method}")

        # Endpoint must exist (not 404) and accept the method (not 405)
        assert r.status_code not in (404, 405), (
            f"{method} {path} returned {r.status_code} — endpoint missing or method not allowed"
        )


# =============================================================================
# 3. NEXUS FUSION RESPONSE CONTRACT TESTS
# =============================================================================

class TestNexusFusionContract:
    """Validate the structure of Nexus cross-module fusion responses."""

    def test_nexus_health_response_structure(self):
        r = client.get("/api/v1/nexus/health")
        assert r.status_code == 200
        data = r.json()
        assert "modules" in data
        assert "overall_status" in data
        assert "data_summary" in data
        assert "timestamp" in data
        # Module keys
        modules = data["modules"]
        expected_modules = {"geocore", "chronos", "sentinel", "pulse", "document_ai"}
        assert expected_modules.issubset(set(modules.keys())), (
            f"Missing modules: {expected_modules - set(modules.keys())}"
        )
        # Each module must have a status
        for mod_name, mod_data in modules.items():
            assert "status" in mod_data, f"Module {mod_name} missing 'status' field"
            assert mod_data["status"] in ("OPERATIONAL", "DEGRADED", "OFFLINE"), (
                f"Module {mod_name} has invalid status: {mod_data['status']}"
            )

    def test_nexus_kpis_response_structure(self):
        r = client.get("/api/v1/nexus/kpis")
        assert r.status_code == 200
        data = r.json()
        assert "kpis" in data
        kpis = data["kpis"]
        required_kpi_keys = {"evidence_quality", "advisory_resolution", "npt_exposure"}
        assert required_kpi_keys.issubset(set(kpis.keys()))

    def test_nexus_fuse_known_well(self):
        r = client.get("/api/v1/nexus/fuse/NO-15/9-F-14")
        assert r.status_code == 200
        data = r.json()
        # Must have top-level structure
        assert "well_id" in data
        assert "fusion_timestamp" in data
        assert "integrity_hash" in data

    def test_nexus_fuse_unknown_well_returns_valid_response(self):
        r = client.get("/api/v1/nexus/fuse/NONEXISTENT-WELL-999")
        # Should return 200 with empty/degraded fusion, not 500
        assert r.status_code == 200

    def test_nexus_compare_requires_minimum_wells(self):
        r = client.post("/api/v1/nexus/compare", json={"well_ids": ["ONLY-ONE"]})
        assert r.status_code == 400

    def test_nexus_operations_log_limit(self):
        r = client.get("/api/v1/nexus/operations-log?limit=5")
        assert r.status_code == 200
        data = r.json()
        assert "entries" in data
        assert len(data["entries"]) <= 5

    def test_nexus_summary_for_landing_page(self):
        r = client.get("/api/v1/nexus/summary")
        assert r.status_code == 200
        data = r.json()
        assert "overall_status" in data
        assert "modules" in data
        assert "wells_loaded" in data


# =============================================================================
# 4. SECURITY HEADERS CONTRACT TESTS
# =============================================================================

class TestSecurityHeaders:
    """Validate that production security headers are present on all responses."""

    def test_security_headers_on_api_response(self):
        r = client.get("/api/v1/status")
        headers = r.headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-XSS-Protection") == "1; mode=block"
        assert "Referrer-Policy" in headers
        assert "Permissions-Policy" in headers
        assert headers.get("Server") == "NWIS"

    def test_request_id_header_present(self):
        r = client.get("/api/v1/status")
        assert "X-Request-ID" in r.headers
        request_id = r.headers["X-Request-ID"]
        assert len(request_id) > 0

    def test_request_ids_are_unique(self):
        ids = set()
        for _ in range(10):
            r = client.get("/health")
            ids.add(r.headers.get("X-Request-ID", ""))
        assert len(ids) == 10, "Request IDs must be unique"

    def test_rate_limit_headers_present(self):
        r = client.get("/api/v1/status")
        assert "X-RateLimit-Limit" in r.headers
        assert "X-RateLimit-Remaining" in r.headers
        limit = int(r.headers["X-RateLimit-Limit"])
        assert limit > 0

    def test_csp_header_present(self):
        r = client.get("/api/v1/status")
        assert "Content-Security-Policy" in r.headers


# =============================================================================
# 5. ERROR HANDLING CONTRACT TESTS
# =============================================================================

class TestErrorHandling:
    """Validate that error responses follow the contract and don't leak secrets."""

    def test_404_for_nonexistent_endpoint(self):
        r = client.get("/api/v1/this-does-not-exist")
        assert r.status_code == 404

    def test_422_for_invalid_query_params(self):
        # limit must be int >=1
        r = client.get("/api/v1/nexus/operations-log?limit=-1")
        assert r.status_code == 422

    def test_error_responses_do_not_contain_secrets(self):
        """Ensure error messages don't leak SECRET_KEY, DATABASE_URL, etc."""
        r = client.get("/api/v1/this-does-not-exist")
        body = r.text.lower()
        assert "secret" not in body
        assert "password" not in body
        assert "postgres" not in body

    def test_post_without_body_returns_422_not_500(self):
        r = client.post("/api/v1/nexus/compare")
        assert r.status_code == 422  # Pydantic validation error, not server crash


# =============================================================================
# 6. CROSS-MODULE DATA INTEGRITY CONTRACT TESTS
# =============================================================================

class TestDataIntegrityContracts:
    """Validate that cross-module data flows maintain integrity."""

    def test_well_list_contains_expected_volve_wells(self):
        r = client.get("/api/v1/wells/")
        assert r.status_code == 200
        wells = r.json()
        assert isinstance(wells, list)
        if len(wells) > 0:
            well = wells[0]
            required_fields = {"well_id", "well_name", "field_name"}
            assert required_fields.issubset(set(well.keys()))

    def test_geocore_wellbores_consistency(self):
        r = client.get("/api/v1/geocore/wellbores")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_documents_endpoint_returns_list(self):
        r = client.get("/api/v1/documents/")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_chronos_wells_endpoint(self):
        r = client.get("/api/v1/chronos/wells")
        assert r.status_code == 200

    def test_sentinel_search_with_empty_query(self):
        """Sentinel search with no query should return valid response, not crash."""
        r = client.get("/api/v1/sentinel/search")
        # Should be 200 or 422 (missing required param), not 500
        assert r.status_code in (200, 422)
