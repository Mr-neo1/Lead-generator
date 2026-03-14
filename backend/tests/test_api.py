"""
Integration tests for the FastAPI endpoints.
All tests use the in-memory SQLite database provided by conftest.py.
No Redis, no Playwright — Redis is disabled via USE_REDIS=false.
"""

import pytest
from fastapi.testclient import TestClient


# ── Health ────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_200(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["database"] == "healthy"

    def test_readiness_returns_200(self, client: TestClient):
        resp = client.get("/ready")
        assert resp.status_code == 200


# ── Stats ─────────────────────────────────────────────────────────────────────

class TestStats:
    def test_stats_empty_db(self, client: TestClient):
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["totalBusinesses"] == 0
        assert data["qualifiedLeads"] == 0
        assert data["activeJobs"] == 0

    def test_advanced_stats_empty_db(self, client: TestClient):
        resp = client.get("/api/stats/advanced")
        assert resp.status_code == 200
        data = resp.json()
        assert "leadTypeDistribution" in data
        assert "scoreDistribution" in data
        assert "topCategories" in data


# ── Jobs ──────────────────────────────────────────────────────────────────────

class TestJobs:
    def _valid_job_payload(self):
        return {
            "keyword": "dentist",
            "location": "London",
            "radius": 5,
            "grid_size": "2x2",
        }

    def test_list_jobs_empty(self, client: TestClient):
        resp = client.get("/api/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_create_job_without_redis(self, client: TestClient, monkeypatch):
        """When Redis is disabled, job is created with status=pending."""
        from unittest.mock import MagicMock, patch

        mock_coords = [(51.5, -0.1), (51.6, -0.2), (51.5, -0.2), (51.6, -0.1)]
        with patch("main.generate_grid", return_value=mock_coords):
            resp = client.post("/api/jobs", json=self._valid_job_payload())

        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    def test_get_job_not_found(self, client: TestClient):
        resp = client.get("/api/jobs/NONEXISTENT")
        assert resp.status_code == 404

    def test_delete_job_not_found(self, client: TestClient):
        resp = client.delete("/api/jobs/NONEXISTENT")
        assert resp.status_code == 404

    def test_cancel_job_not_found(self, client: TestClient):
        resp = client.post("/api/jobs/NONEXISTENT/cancel")
        assert resp.status_code == 404

    def test_job_pagination(self, client: TestClient):
        resp = client.get("/api/jobs?page=1&page_size=5")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_pages" in data
        assert "items" in data

    def test_create_job_invalid_grid(self, client: TestClient):
        payload = self._valid_job_payload()
        payload["grid_size"] = "invalid"
        resp = client.post("/api/jobs", json=payload)
        assert resp.status_code == 422  # validation error

    def test_create_job_radius_too_large(self, client: TestClient):
        payload = self._valid_job_payload()
        payload["radius"] = 9999
        resp = client.post("/api/jobs", json=payload)
        assert resp.status_code == 422


# ── Leads ─────────────────────────────────────────────────────────────────────

class TestLeads:
    def test_list_leads_empty(self, client: TestClient):
        resp = client.get("/api/leads")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_get_lead_not_found(self, client: TestClient):
        resp = client.get("/api/leads/99999")
        assert resp.status_code == 404

    def test_delete_lead_not_found(self, client: TestClient):
        resp = client.delete("/api/leads/99999")
        assert resp.status_code == 404

    def test_leads_with_filters(self, client: TestClient):
        resp = client.get("/api/leads?lead_type=NO_WEBSITE&min_score=5")
        assert resp.status_code == 200

    def test_leads_search_param(self, client: TestClient):
        resp = client.get("/api/leads?search=test")
        assert resp.status_code == 200

    def test_export_leads_returns_csv(self, client: TestClient):
        resp = client.get("/api/leads/export")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")


# ── Blacklist ─────────────────────────────────────────────────────────────────

class TestBlacklist:
    def test_list_blacklist_empty(self, client: TestClient):
        resp = client.get("/api/blacklist")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    def test_add_to_blacklist(self, client: TestClient):
        resp = client.post(
            "/api/blacklist",
            json={"value": "+1-555-0100", "type": "phone", "reason": "spam"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_add_duplicate_rejected(self, client: TestClient):
        payload = {"value": "+1-555-0101", "type": "phone"}
        client.post("/api/blacklist", json=payload)
        resp = client.post("/api/blacklist", json=payload)
        assert resp.status_code == 400

    def test_blacklist_invalid_type(self, client: TestClient):
        resp = client.post(
            "/api/blacklist", json={"value": "abc123", "type": "email"}
        )
        assert resp.status_code == 422  # pattern validation

    def test_remove_nonexistent_blacklist_entry(self, client: TestClient):
        resp = client.delete("/api/blacklist/99999")
        assert resp.status_code == 404


# ── Bulk operations ───────────────────────────────────────────────────────────

class TestBulkOperations:
    def test_bulk_update_empty_list_rejected(self, client: TestClient):
        resp = client.post("/api/leads/bulk-update", json={"lead_ids": [], "status": "contacted"})
        assert resp.status_code == 422

    def test_bulk_delete_empty_list_rejected(self, client: TestClient):
        resp = client.post("/api/leads/bulk-delete", json={"lead_ids": []})
        assert resp.status_code == 422

    def test_bulk_update_nonexistent_ids(self, client: TestClient):
        """Updating non-existent leads should succeed gracefully (0 updated)."""
        resp = client.post(
            "/api/leads/bulk-update",
            json={"lead_ids": [99990, 99991], "status": "contacted"},
        )
        assert resp.status_code == 200

    def test_bulk_delete_nonexistent_ids(self, client: TestClient):
        """Deleting non-existent leads should succeed gracefully (0 deleted)."""
        resp = client.post(
            "/api/leads/bulk-delete",
            json={"lead_ids": [99990, 99991]},
        )
        assert resp.status_code == 200
