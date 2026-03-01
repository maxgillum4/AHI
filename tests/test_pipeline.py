"""
tests/test_pipeline.py — End-to-end Phase 1 → DB → reanalyze pipeline test.

Verifies the full data contract:
  - submission_id is returned in Phase 1 response (non-empty UUID string)
  - evidence_id is set on every per_question result
  - submission and per-question rows persist to DB (confirmed via debug endpoint)
  - POST /api/submissions/{id}/reanalyze returns a refreshed AnalysisResponse
    with the SAME submission_id
  - followup_resolved flag is set in DB for the answered question after reanalysis
  - GET /api/submissions/{id} returns the correct shape

Run from repo root:
    pytest tests/test_pipeline.py -v

Notes:
  - whisper is stubbed (avoids ~150 MB model download during CI/test)
  - DB is redirected to a temp file; production ahi.db is never touched
  - Uses module-scoped fixtures so Phase 1 runs once and results are shared
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Stub whisper BEFORE any import that causes routes.py to load.
# routes.py executes `_model = whisper.load_model("base")` at module level;
# if whisper is not stubbed first the TestClient startup will attempt to
# load a real model (slow / fails in CI without GPU / requires large download).
# ---------------------------------------------------------------------------
if "whisper" not in sys.modules:
    _whisper_stub = MagicMock()
    _whisper_stub.load_model.return_value = MagicMock()
    sys.modules["whisper"] = _whisper_stub


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """
    FastAPI TestClient backed by an isolated temporary SQLite database.

    db.database.DB_PATH is patched before the app initialises so the
    production ahi.db file is never touched.
    """
    tmp_db = tmp_path_factory.mktemp("ahi_pipeline") / "test.db"

    import db.database as _dbmod
    _orig_path   = _dbmod.DB_PATH
    _dbmod.DB_PATH = tmp_db
    _dbmod.init_db()                   # create tables in temp DB

    from main import app
    from fastapi.testclient import TestClient

    # Ensure the module-level _model in routes points at our stub (not a
    # real whisper model that may have been loaded in a prior test session).
    import routes as _routes
    _routes._model = sys.modules["whisper"].load_model.return_value

    with TestClient(app, raise_server_exceptions=True) as tc:
        yield tc

    _dbmod.DB_PATH = _orig_path        # restore so other tests aren't affected


# ---------------------------------------------------------------------------
# Payload factory — three low-scoring questions to trigger followup flags
# ---------------------------------------------------------------------------

_PHASE1_PAYLOAD = {
    "payload_version": "1.0",
    "respondent_name": "Pipeline Tester",
    "organization_name": "Pytest Corp",
    "respondent_role": "Tech Lead",
    "selected_sections": ["leadership", "workforce"],
    "questions": [
        {
            "question_id": "W1",
            "category": "Workforce",
            "label": "AI Literacy",
            "prompt": "How would you rate AI literacy across your workforce?",
            "score": 1,
            "typed_response": None,
        },
        {
            "question_id": "W3",
            "category": "Workforce",
            "label": "Training Programs",
            "prompt": "How structured are your AI training programs?",
            "score": 1,
            "typed_response": None,
        },
        {
            "question_id": "Q_Decision",
            "category": "Leadership & Vision",
            "label": "AI Decision Ownership",
            "prompt": "Who holds final accountability for AI investment and deployment decisions?",
            "score": 2,
            "typed_response": None,
        },
    ],
    "justifications": [],
}

# A clearly specific follow-up answer — contains owner, metric, system, cadence.
_SPECIFIC_FOLLOWUP = (
    "Our Head of Learning (Jane Smith) owns the programme. "
    "We track completion rate monthly — currently 78% — using Workday Learning."
)


# ---------------------------------------------------------------------------
# Module-scoped result fixtures (one HTTP call per fixture, shared across tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def phase1_result(client):
    """Run Phase 1 analysis once; cache the JSON response."""
    resp = client.post("/api/analyze-assessment", json=_PHASE1_PAYLOAD)
    assert resp.status_code == 200, f"Phase 1 failed ({resp.status_code}): {resp.text}"
    return resp.json()


@pytest.fixture(scope="module")
def submission_id(phase1_result):
    """Extract and validate the submission_id from Phase 1."""
    sid = phase1_result.get("submission_id")
    assert sid, "submission_id is missing or empty in Phase 1 response"
    return sid


@pytest.fixture(scope="module")
def reanalysis_result(client, submission_id):
    """Run reanalysis with a specific follow-up answer for W1."""
    body = {
        "answers": [
            {
                "question_id": "W1",
                "text_response": _SPECIFIC_FOLLOWUP,
            }
        ]
    }
    resp = client.post(f"/api/submissions/{submission_id}/reanalyze", json=body)
    assert resp.status_code == 200, f"Reanalyze failed ({resp.status_code}): {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# Tests — Phase 1 response contract
# ---------------------------------------------------------------------------

class TestPhase1Contract:

    def test_submission_id_is_present(self, phase1_result):
        """submission_id must be a non-empty string in the Phase 1 response."""
        assert "submission_id" in phase1_result, "submission_id key missing"
        assert phase1_result["submission_id"],    "submission_id is empty/null"

    def test_overall_block_present(self, phase1_result):
        """Top-level 'overall' block must be present."""
        assert "overall" in phase1_result

    def test_per_question_list_present(self, phase1_result):
        """per_question list must match input question count."""
        pq = phase1_result.get("per_question", [])
        assert len(pq) == len(_PHASE1_PAYLOAD["questions"]), (
            f"Expected {len(_PHASE1_PAYLOAD['questions'])} per_question items, got {len(pq)}"
        )

    def test_evidence_ids_present_on_all_questions(self, phase1_result):
        """Every per_question result must carry a non-null evidence_id (UUID string)."""
        pq = phase1_result.get("per_question", [])
        missing = [q["question_id"] for q in pq if not q.get("evidence_id")]
        assert not missing, f"evidence_id missing on questions: {missing}"

    def test_evidence_ids_are_unique(self, phase1_result):
        """Each question must have a distinct evidence_id."""
        pq     = phase1_result.get("per_question", [])
        ids    = [q["evidence_id"] for q in pq if q.get("evidence_id")]
        assert len(ids) == len(set(ids)), "Duplicate evidence_ids detected"


# ---------------------------------------------------------------------------
# Tests — DB persistence (via debug endpoint)
# ---------------------------------------------------------------------------

class TestDatabasePersistence:

    def test_debug_endpoint_submission_found(self, client, submission_id):
        """Debug endpoint must confirm the submission row exists in DB."""
        resp = client.get(f"/api/debug/submission/{submission_id}")
        assert resp.status_code == 200, resp.text
        body  = resp.json()
        check = body["pipeline_check"]
        assert check["submission_found"] is True
        assert check["submission_id"] == submission_id

    def test_debug_endpoint_scores_persisted(self, client, submission_id, phase1_result):
        """Composite score and maturity stage from Phase 1 must be in DB."""
        resp  = client.get(f"/api/debug/submission/{submission_id}")
        body  = resp.json()
        check = body["pipeline_check"]
        assert check["composite_score"] is not None
        assert check["maturity_stage"]  is not None
        assert check["question_count"] == len(_PHASE1_PAYLOAD["questions"])

    def test_debug_endpoint_evidence_ids_in_db(self, client, submission_id):
        """All per_question rows in DB must have an evidence_id."""
        resp     = client.get(f"/api/debug/submission/{submission_id}")
        body     = resp.json()
        pq_rows  = body["per_question_summary"]
        missing  = [r["question_id"] for r in pq_rows if not r.get("evidence_id")]
        assert not missing, f"evidence_id missing in DB for: {missing}"

        status = body["reanalysis_status"]
        assert status["evidence_ids_present"] == len(_PHASE1_PAYLOAD["questions"])

    def test_get_submission_endpoint(self, client, submission_id):
        """GET /api/submissions/{id} must return submission + per_question keys."""
        resp = client.get(f"/api/submissions/{submission_id}")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "submission"   in data
        assert "per_question" in data
        assert data["submission"]["submission_id"] == submission_id

    def test_unknown_submission_returns_404(self, client):
        """Fetching a nonexistent submission_id must return HTTP 404."""
        resp = client.get("/api/submissions/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests — Reanalysis contract
# ---------------------------------------------------------------------------

class TestReanalysisPipeline:

    def test_reanalyze_returns_200(self, reanalysis_result):
        """Reanalysis must succeed (fixture asserts 200; here we check shape)."""
        assert "overall"      in reanalysis_result
        assert "per_question" in reanalysis_result

    def test_reanalyze_preserves_submission_id(self, reanalysis_result, submission_id):
        """submission_id must be unchanged after reanalysis."""
        refreshed_sid = reanalysis_result.get("submission_id")
        assert refreshed_sid == submission_id, (
            f"submission_id changed: {refreshed_sid!r} != {submission_id!r}"
        )

    def test_reanalyze_has_evidence_ids(self, reanalysis_result):
        """Refreshed per_question results must still carry evidence_ids."""
        pq      = reanalysis_result.get("per_question", [])
        missing = [q["question_id"] for q in pq if not q.get("evidence_id")]
        assert not missing, f"evidence_id missing after reanalysis on: {missing}"

    def test_followup_resolved_set_in_db(self, client, submission_id, reanalysis_result):
        """
        After reanalysis the debug endpoint must show followup_resolved=True
        for W1 (the question that received a concrete follow-up answer).
        """
        # Reanalysis must have run (fixture guarantees it)
        resp = client.get(f"/api/debug/submission/{submission_id}")
        assert resp.status_code == 200, resp.text
        body = resp.json()

        pq_summary   = body["per_question_summary"]
        resolved_ids = {r["question_id"] for r in pq_summary if r.get("followup_resolved")}

        assert "W1" in resolved_ids, (
            f"W1 not marked followup_resolved in DB. Resolved set: {resolved_ids}"
        )

        status = body["reanalysis_status"]
        assert status["any_followup_resolved"] is True
        assert status["resolved_count"] >= 1

    def test_reanalyze_bad_submission_returns_404(self, client):
        """Reanalyzing a nonexistent submission must return HTTP 404."""
        body = {"answers": [{"question_id": "W1", "text_response": "test"}]}
        resp = client.post(
            "/api/submissions/00000000-0000-0000-0000-000000000000/reanalyze",
            json=body,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests — Health endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint:

    def test_health_ok(self, client):
        """Health endpoint must return status=ok."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "benchmark" in data
