"""Tests for on_session_start presence detection + graceful no-op (M3 task 1)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from mission_ctrl_core.logic.recap import RecapResult
from mission_ctrl_core.models import Actor, SessionRef, SessionStartedDecision
from mission_ctrl_core.stores import IntentStore
from mission_ctrl_core.stores.base import utcnow
from mission_ctrl_pi.hooks import has_intent_dir, on_session_start
from mission_ctrl_pi.hooks.session_start import (
    BRIEF_UNDER_HOURS,
    SKIP_UNDER_HOURS,
    STANDARD_UNDER_HOURS,
    last_session_time,
    select_tier,
)
from mission_ctrl_pi.schemas import InitInput
from mission_ctrl_pi.skills import intent_init

T0 = datetime(2026, 9, 4, 12, 0, 0, tzinfo=timezone.utc)


def _init_store(tmp_path) -> IntentStore:
    store = IntentStore(tmp_path)
    intent_init(
        InitInput(project_name="HookApp", mission="Hooked mission"), store=store
    )
    return store


def _seed_session(store: IntentStore, at: datetime) -> None:
    store.builder().build(
        "SESSION_STARTED",
        SessionStartedDecision(gap_hours=0.0, verbosity="standard"),
        actor=Actor(type="human", name="tester"),
        reasoning="prior session",
        affected_entities=[],
        session=SessionRef(id="ses_0001"),
        timestamp=at,
    )


def test_no_intent_dir_no_ops_and_writes_nothing(tmp_path):
    assert on_session_start(root=tmp_path) is None
    # Graceful means no side effects: hook must not create `.intent/`.
    assert not (tmp_path / ".intent").exists()


def test_empty_intent_dir_no_ops(tmp_path):
    (tmp_path / ".intent").mkdir()
    assert has_intent_dir(tmp_path) is False
    assert on_session_start(root=tmp_path) is None


def test_intent_dir_without_mission_json_no_ops(tmp_path):
    intent_dir = tmp_path / ".intent"
    intent_dir.mkdir()
    (intent_dir / "notes.txt").write_text("partial state")
    assert on_session_start(root=tmp_path) is None


def test_explicit_store_on_empty_root_no_ops(tmp_path):
    store = IntentStore(tmp_path)
    assert on_session_start(store=store) is None
    assert not (tmp_path / ".intent").exists()


def test_immediate_reopen_skips_recap(tmp_path):
    """Fresh init + immediate session open: gap ≈ 0 → skip tier → None."""
    _init_store(tmp_path)
    assert has_intent_dir(tmp_path) is True
    assert on_session_start(root=tmp_path) is None


# ---------------------------------------------------------------------------
# Session-gap tiers (M3 task 2)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("gap_hours", "expected"),
    [
        (0.0, "skip"),
        (SKIP_UNDER_HOURS - 0.01, "skip"),
        (SKIP_UNDER_HOURS, "brief"),
        (BRIEF_UNDER_HOURS - 0.01, "brief"),
        (BRIEF_UNDER_HOURS, "standard"),
        (STANDARD_UNDER_HOURS - 0.01, "standard"),
        (STANDARD_UNDER_HOURS, "full"),
        (500.0, "full"),
    ],
)
def test_select_tier_thresholds(gap_hours, expected):
    assert select_tier(gap_hours) == expected


def test_gap_skip_returns_none_and_writes_nothing(tmp_path):
    store = _init_store(tmp_path)
    _seed_session(store, T0)
    before = len(store.meta.read_all())
    assert on_session_start(store=store, now=T0 + timedelta(minutes=30)) is None
    assert len(store.meta.read_all()) == before


@pytest.mark.parametrize(
    ("delta_hours", "expected_verbosity"),
    [(2.0, "brief"), (10.0, "standard"), (50.0, "full")],
)
def test_gap_tiers_drive_recap_verbosity(tmp_path, delta_hours, expected_verbosity):
    store = _init_store(tmp_path)
    _seed_session(store, T0)
    result = on_session_start(store=store, now=T0 + timedelta(hours=delta_hours))
    assert isinstance(result, RecapResult)
    assert result.verbosity == expected_verbosity


@pytest.mark.parametrize(
    ("delta_hours", "expected_verbosity"),
    [
        (SKIP_UNDER_HOURS, "brief"),
        (BRIEF_UNDER_HOURS, "standard"),
        (STANDARD_UNDER_HOURS, "full"),
    ],
)
def test_gap_tier_boundaries(tmp_path, delta_hours, expected_verbosity):
    """Exact thresholds belong to the higher tier (1h→brief, 8h→standard)."""
    store = _init_store(tmp_path)
    _seed_session(store, T0)
    result = on_session_start(store=store, now=T0 + timedelta(hours=delta_hours))
    assert isinstance(result, RecapResult)
    assert result.verbosity == expected_verbosity


def test_gap_falls_back_to_intent_created(tmp_path):
    """No SESSION_STARTED → gap measured from INTENT_CREATED."""
    before = utcnow()
    store = _init_store(tmp_path)
    assert last_session_time(store) is not None
    result = on_session_start(store=store, now=before + timedelta(hours=10))
    assert isinstance(result, RecapResult)
    assert result.verbosity == "standard"


def test_session_started_takes_precedence_over_newer_init(tmp_path):
    """A prior SESSION_STARTED watermarks the gap even when INTENT_CREATED
    would imply a longer gap (spec: SESSION_STARTED preferred)."""
    before = utcnow()
    store = _init_store(tmp_path)
    _seed_session(store, before + timedelta(hours=9))
    # Gap from SESSION_STARTED is 0.5h → skip, although INTENT_CREATED is 9.5h old.
    assert on_session_start(store=store, now=before + timedelta(hours=9.5)) is None


def test_no_session_history_returns_full_recap(tmp_path):
    store = _init_store(tmp_path)
    (tmp_path / ".intent" / "meta.jsonl").unlink()
    assert last_session_time(store) is None
    result = on_session_start(store=store, now=T0)
    assert isinstance(result, RecapResult)
    assert result.verbosity == "full"


def test_non_skip_tiers_are_read_only_until_task_4(tmp_path):
    """Gap recaps must not write until SESSION_STARTED logging lands (task 4)."""
    store = _init_store(tmp_path)
    _seed_session(store, T0)
    before = len(store.meta.read_all())
    on_session_start(store=store, now=T0 + timedelta(hours=10))
    assert len(store.meta.read_all()) == before
