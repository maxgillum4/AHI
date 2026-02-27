"""
phase2/storage.py — In-memory session store with TTL.

NDA guarantee: no raw audio bytes, no full transcript logs.
Only session state and extracted scores are stored in RAM.
Sessions expire after SESSION_TTL_HOURS (default: 2h) and are cleaned up
automatically on every store access.
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta
from typing import Dict, Optional

from .schemas import V2Session

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SESSION_TTL_HOURS: int = 2


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

class SessionStore:
    """
    Thread-safe in-memory session store.
    TTL cleanup runs on every mutating access (no background thread needed).
    """

    def __init__(self, ttl_hours: int = SESSION_TTL_HOURS) -> None:
        self._store: Dict[str, V2Session] = {}
        self._lock  = threading.Lock()
        self._ttl   = timedelta(hours=ttl_hours)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self, session: V2Session) -> None:
        """Add a new session. Runs TTL cleanup first."""
        with self._lock:
            self._cleanup_expired()
            self._store[str(session.session_id)] = session

    def get(self, session_id: str) -> Optional[V2Session]:
        """Return session or None if not found / expired."""
        with self._lock:
            self._cleanup_expired()
            s = self._store.get(session_id)
            if s is None:
                return None
            if s.expires_at < datetime.utcnow():
                del self._store[session_id]
                return None
            return s

    def update(self, session: V2Session) -> None:
        """Persist updated session state."""
        with self._lock:
            session.updated_at = datetime.utcnow()
            self._store[str(session.session_id)] = session

    def delete(self, session_id: str) -> bool:
        """Explicitly delete a session. Returns True if it existed."""
        with self._lock:
            if session_id in self._store:
                del self._store[session_id]
                return True
            return False

    def count(self) -> int:
        """Return number of live (non-expired) sessions."""
        with self._lock:
            self._cleanup_expired()
            return len(self._store)

    def new_expiry(self) -> datetime:
        """Return a fresh expiry datetime for a new session."""
        return datetime.utcnow() + self._ttl

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _cleanup_expired(self) -> None:
        """Remove all sessions past their expiry. Caller must hold _lock."""
        now     = datetime.utcnow()
        expired = [sid for sid, s in self._store.items() if s.expires_at < now]
        for sid in expired:
            del self._store[sid]


# ---------------------------------------------------------------------------
# Singleton — imported by api.py
# ---------------------------------------------------------------------------

store = SessionStore()
