"""
Tests for phase2/storage.py — SessionStore TTL and CRUD.
Run: pytest Desktop/AHI/phase2/tests/
"""

import uuid
from datetime import datetime, timedelta

import pytest

from phase2.schemas import ConversationState, InterviewMode, V2Session
from phase2.storage import SessionStore


def _make_session(ttl_offset_seconds: int = 7200) -> V2Session:
    now = datetime.utcnow()
    return V2Session(
        session_id        = uuid.uuid4(),
        mode              = InterviewMode.A,
        selected_sections = ["leadership"],
        state             = ConversationState.ASK,
        created_at        = now,
        updated_at        = now,
        expires_at        = now + timedelta(seconds=ttl_offset_seconds),
    )


class TestSessionStore:

    def test_create_and_get(self):
        store   = SessionStore(ttl_hours=2)
        session = _make_session()
        store.create(session)

        fetched = store.get(str(session.session_id))
        assert fetched is not None
        assert fetched.session_id == session.session_id

    def test_get_nonexistent_returns_none(self):
        store = SessionStore()
        assert store.get("nonexistent-id") is None

    def test_delete(self):
        store   = SessionStore()
        session = _make_session()
        store.create(session)

        sid     = str(session.session_id)
        deleted = store.delete(sid)
        assert deleted is True
        assert store.get(sid) is None

    def test_delete_nonexistent_returns_false(self):
        store = SessionStore()
        assert store.delete("nonexistent") is False

    def test_ttl_expiry(self):
        store   = SessionStore(ttl_hours=1)
        # Create a session that is already expired
        session = _make_session(ttl_offset_seconds=-1)
        store._store[str(session.session_id)] = session  # bypass create to skip cleanup

        fetched = store.get(str(session.session_id))
        assert fetched is None

    def test_count_excludes_expired(self):
        store   = SessionStore()
        live    = _make_session(ttl_offset_seconds=3600)
        expired = _make_session(ttl_offset_seconds=-1)

        store._store[str(live.session_id)]    = live
        store._store[str(expired.session_id)] = expired

        assert store.count() == 1

    def test_update_persists_state(self):
        store   = SessionStore()
        session = _make_session()
        store.create(session)

        session.state = ConversationState.WRAP
        store.update(session)

        fetched = store.get(str(session.session_id))
        assert fetched is not None
        assert fetched.state == ConversationState.WRAP

    def test_new_expiry_is_future(self):
        store  = SessionStore(ttl_hours=2)
        expiry = store.new_expiry()
        assert expiry > datetime.utcnow()
