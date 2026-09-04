"""Tests for on_session_start presence detection + graceful no-op (M3 task 1)."""

from __future__ import annotations

from mission_ctrl_core.logic.recap import RecapResult
from mission_ctrl_core.stores import IntentStore
from mission_ctrl_pi.hooks import has_intent_dir, on_session_start
from mission_ctrl_pi.schemas import InitInput
from mission_ctrl_pi.skills import intent_init


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


def test_initialized_project_returns_recap(tmp_path):
    store = IntentStore(tmp_path)
    intent_init(
        InitInput(project_name="HookApp", mission="Hooked mission"), store=store
    )
    assert has_intent_dir(tmp_path) is True
    result = on_session_start(root=tmp_path)
    assert isinstance(result, RecapResult)
    assert result.mission == "Hooked mission"
    assert result.verbosity == "standard"
