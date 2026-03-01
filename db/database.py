"""
db/database.py — AHI SQLite initialization.

DB_PATH:  Read from AHI_DB_PATH env var; defaults to ahi.db beside this repo.
init_db:  Called once at startup to create tables if they don't exist.
get_connection: Context-managed sqlite3 connection (autocommit on exit).

NDA note: raw justification text and audio are never written here.
          Only PII-redacted analysis outputs are persisted.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

# ---------------------------------------------------------------------------
# Path configuration
# ---------------------------------------------------------------------------

_DEFAULT_DB = Path(__file__).resolve().parent.parent / "ahi.db"
DB_PATH: Path = Path(os.getenv("AHI_DB_PATH", str(_DEFAULT_DB)))


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS submissions (
    submission_id       TEXT PRIMARY KEY,
    respondent_name     TEXT NOT NULL,
    organization_name   TEXT NOT NULL,
    respondent_role     TEXT,
    organization_unit   TEXT,
    payload_version     TEXT,
    submitted_at        TEXT NOT NULL,
    composite_score     REAL,
    maturity_stage      TEXT,
    needs_human_followup INTEGER NOT NULL DEFAULT 0,
    question_count      INTEGER,
    top_blockers        TEXT,
    quick_wins          TEXT,
    next_best_actions   TEXT
);

CREATE TABLE IF NOT EXISTS per_question_results (
    id                      TEXT PRIMARY KEY,
    submission_id           TEXT NOT NULL
                                REFERENCES submissions(submission_id),
    question_id             TEXT NOT NULL,
    category                TEXT NOT NULL,
    label                   TEXT,
    self_score              INTEGER,
    inferred_stage          TEXT,
    confidence              REAL,
    confidence_label        TEXT,
    evidence_strength       INTEGER,
    evidence_strength_label TEXT,
    evidence_id             TEXT,
    has_supporting_audio    INTEGER NOT NULL DEFAULT 0,
    mentions_metric         INTEGER NOT NULL DEFAULT 0,
    mentions_owner          INTEGER NOT NULL DEFAULT 0,
    mentions_cadence        INTEGER NOT NULL DEFAULT 0,
    mentions_system         INTEGER NOT NULL DEFAULT 0,
    red_flags               TEXT,
    recommended_followups   TEXT,
    supporting_text_excerpt TEXT,
    followup_resolved       INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_pqr_submission
    ON per_question_results(submission_id);

CREATE INDEX IF NOT EXISTS idx_pqr_evidence
    ON per_question_results(evidence_id);
"""

# Migrations for existing databases (safe to run on every startup)
_MIGRATIONS = [
    "ALTER TABLE per_question_results ADD COLUMN followup_resolved INTEGER NOT NULL DEFAULT 0",
    # evidence_id was added after initial release; existing DBs need the column
    "ALTER TABLE per_question_results ADD COLUMN evidence_id TEXT",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _run_migrations(conn: sqlite3.Connection) -> None:
    """Apply additive migrations. Silently ignores 'duplicate column' errors."""
    for stmt in _MIGRATIONS:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise


def init_db() -> None:
    """Create tables and run migrations. Safe to call every startup."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(_DDL)
        _run_migrations(conn)
    print(f"[AHI] DB initialised: {DB_PATH}")


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Yield an open connection; commit on clean exit, rollback on exception."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
