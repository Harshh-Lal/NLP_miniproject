"""Integration tests for FastAPI endpoints in api/main.py using TestClient."""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from scripts.demo_cli import FIXTURE_MESSAGE, FIXTURE_DIFF

client = TestClient(app)


class TestApiEndpoints:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_audit_standard_fixture(self):
        response = client.post("/audit", json={
            "message": FIXTURE_MESSAGE,
            "diff": FIXTURE_DIFF,
        })
        assert response.status_code == 200
        data = response.json()

        # Check expected top-level keys
        assert "commit_message" in data
        assert "overall_score" in data
        assert "overall_status" in data
        assert "scores" in data
        assert "diff_summary" in data
        assert "aggregation" in data

        # Check exact score and status values
        assert data["overall_score"] == 0.41
        assert data["overall_status"] == "FAIL"

        # Check imperative mood
        imp = data["scores"]["imperative_mood"]
        assert imp["score"] == 0.0
        assert imp["status"] == "FAIL"
        assert imp["suggestion"] == "fix"
        assert imp["first_word"] == "fixed"

        # Check coverage
        cov = data["scores"]["coverage"]
        assert cov["score"] == 0.5
        assert cov["status"] == "WARN"
        assert "validate_token" in cov["omitted_symbols"]
        assert "login" in cov["mentioned_symbols"]

        # Check risk flags
        risk = data["scores"]["risk_flags"]
        assert risk["status"] == "WARN"
        assert "auth" in risk["layers_triggered"]
        assert any("auth" in f.lower() for f in risk["flags"])

        # Check type consistency (neutral score=None)
        tcons = data["scores"]["type_consistency"]
        assert tcons["score"] is None
        assert tcons["status"] == "N/A"

    def test_audit_empty_or_malformed_diff_sane_response(self):
        # 1. Empty diff with valid message -> returns 200 (not 500)
        res1 = client.post("/audit", json={
            "message": "fix: update docs",
            "diff": "",
        })
        assert res1.status_code == 200
        d1 = res1.json()
        assert d1["diff_summary"]["files"] == []
        assert d1["diff_summary"]["added_lines"] == 0

        # 2. Malformed non-unified diff -> handled gracefully without 500
        malformed_diff = "Random text that is not a git diff @@ corrupted @@"
        res2 = client.post("/audit", json={
            "message": "fix login",
            "diff": malformed_diff,
        })
        assert res2.status_code == 200
        d2 = res2.json()
        assert "scores" in d2

        # 3. Both empty message and diff -> 400 Bad Request (not 500)
        res3 = client.post("/audit", json={
            "message": "",
            "diff": "",
        })
        assert res3.status_code == 400
        assert "cannot be empty" in res3.json()["detail"]

    def test_empty_message_returns_400(self):
        """Item 4: empty message (whitespace-only) must return HTTP 400."""
        for msg in ["", "   ", "\t"]:
            res = client.post("/audit", json={"message": msg, "diff": "--- a/f\n+++ b/f\n"})
            assert res.status_code == 400, f"Expected 400 for message={repr(msg)}, got {res.status_code}"
            assert "cannot be empty" in res.json()["detail"]

    def test_empty_diff_returns_na_status(self):
        """Item 4: valid message + empty diff must return 200 with overall_status='N/A' and overall_score=None."""
        res = client.post("/audit", json={"message": "fix login", "diff": ""})
        assert res.status_code == 200
        data = res.json()
        assert data["overall_score"] is None
        assert data["overall_status"] == "N/A"
        assert data["evidence"] == "No valid diff detected"
