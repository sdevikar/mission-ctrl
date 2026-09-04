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


def test_session_start_appends_session_started(tmp_path):
    store = _init_store(tmp_path)
    _seed_session(store, T0)
    before = len(store.meta.read_all())
    result = on_session_start(store=store, now=T0 + timedelta(hours=10))
    assert isinstance(result, RecapResult)
    events = store.meta.read_all()
    assert len(events) == before + 1
    logged = events[-1]
    assert logged.event_type == "SESSION_STARTED"
    assert logged.decision.verbosity == "standard"
    assert logged.decision.gap_hours == pytest.approx(10.0)
    assert logged.actor.type == "agent"


def test_session_start_no_history_logs_zero_gap_full(tmp_path):
    store = _init_store(tmp_path)
    (tmp_path / ".intent" / "meta.jsonl").unlink()
    result = on_session_start(store=store, now=T0)
    assert isinstance(result, RecapResult)
    assert result.verbosity == "full"
    events = store.meta.read_all()
    assert [e.event_type for e in events] == ["SESSION_STARTED"]
    assert events[0].decision.gap_hours == 0.0


# ---------------------------------------------------------------------------
# Manifest wiring: Pi entry point (M3 task 3)
# ---------------------------------------------------------------------------


def test_manifest_session_start_hook_injects_recap(tmp_path):
    from mission_ctrl_pi.extension import Extension

    store = _init_store(tmp_path)
    _seed_session(store, utcnow() - timedelta(hours=10))
    hook = Extension().get_skill("intent:recap")
    assert hook is not None  # sanity: manifest skills intact
    session_hook = Extension().hooks["on_session_start"]
    result = session_hook({"cwd": str(tmp_path)})
    assert isinstance(result, RecapResult)
    assert result.mission == "Hooked mission"
    assert result.verbosity == "standard"


def test_manifest_session_start_hook_no_ops_without_intent(tmp_path):
    from mission_ctrl_pi.extension import Extension

    session_hook = Extension().hooks["on_session_start"]
    assert session_hook({"cwd": str(tmp_path)}) is None
    assert not (tmp_path / ".intent").exists()


def test_session_start_hook_accepts_path_context(tmp_path):
    from mission_ctrl_pi.hooks import session_start_hook

    store = _init_store(tmp_path)
    _seed_session(store, utcnow() - timedelta(hours=10))
    result = session_start_hook(tmp_path)
    assert isinstance(result, RecapResult)
    assert result.verbosity == "standard"


def test_session_start_hook_bare_context_never_raises(tmp_path, monkeypatch):
    from mission_ctrl_pi.hooks import session_start_hook

    monkeypatch.chdir(tmp_path)  # "." has no `.intent/` here
    assert session_start_hook() is None
    assert session_start_hook({}) is None
    assert session_start_hook(object()) is None
    assert not (tmp_path / ".intent").exists()


def test_e2e_session_open_on_mid_flight_fixture(tmp_path):
    """E2E: opening the mid-flight project shows a recap and logs the session."""
    import shutil
    from pathlib import Path as _Path

    from mission_ctrl_pi.hooks import session_start_hook

    fixtures = _Path(__file__).resolve().parents[2] / "core" / "tests" / "fixtures"
    shutil.copytree(fixtures / "mid-flight" / ".intent", tmp_path / ".intent")
    store = IntentStore(tmp_path)
    before = len(store.meta.read_all())

    result = session_start_hook(str(tmp_path))
    assert isinstance(result, RecapResult)
    assert result.last_focus == "spec_001"

    types = [e.event_type for e in store.meta.read_all()]
    assert len(types) == before + 1
    assert types[-1] == "SESSION_STARTED"
