"""Tests for on_before_send interception, redirect, override, logging (M3)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from mission_ctrl_core.models import SpecStatus
from mission_ctrl_core.stores import IntentStore
from mission_ctrl_pi.hooks import (
    find_implementation_intent,
    on_before_send,
)
from mission_ctrl_pi.hooks.before_send import EXCERPT_LEN
from mission_ctrl_pi.schemas import (
    AddIdeaInput,
    DesignApproveInput,
    DesignProposeInput,
    InitInput,
    SpecCreateInput,
    TriageInput,
)
from mission_ctrl_pi.skills import (
    intent_add_idea,
    intent_design_approve,
    intent_design_propose,
    intent_init,
    intent_spec_create,
    intent_triage,
)


def _init_store(tmp_path) -> IntentStore:
    store = IntentStore(tmp_path)
    intent_init(
        InitInput(project_name="BeforeSendApp", mission="Guarded mission"),
        store=store,
    )
    return store


def _store_with_untriaged_idea(tmp_path) -> tuple[IntentStore, str]:
    store = _init_store(tmp_path)
    add = intent_add_idea(AddIdeaInput(title="SSO login"), store=store)
    return store, add.idea_id


def _store_with_approved_design(tmp_path) -> tuple[IntentStore, str]:
    store, idea_id = _store_with_untriaged_idea(tmp_path)
    intent_triage(
        TriageInput(idea_id=idea_id, bucket="mvp", alignment_verdict="Core"),
        store=store,
    )
    create = intent_spec_create(SpecCreateInput(idea_id=idea_id), store=store)
    intent_design_propose(
        DesignProposeInput(spec_id=create.spec_id, digest="Design reasoning here"),
        store=store,
    )
    intent_design_approve(
        DesignApproveInput(spec_id=create.spec_id, decision="approved"),
        store=store,
    )
    return store, create.spec_id


def _event_types(store: IntentStore) -> list[str]:
    return [e.event_type for e in store.meta.read_all()]


# ---------------------------------------------------------------------------
# No-op paths
# ---------------------------------------------------------------------------


def test_no_intent_dir_proceeds_and_writes_nothing(tmp_path):
    result = on_before_send("implement SSO", root=tmp_path)
    assert result.action == "proceed"
    assert result.target is None
    assert not (tmp_path / ".intent").exists()


def test_partial_intent_dir_proceeds(tmp_path):
    (tmp_path / ".intent").mkdir()
    result = on_before_send("implement SSO", root=tmp_path)
    assert result.action == "proceed"


@pytest.mark.parametrize("message", ["", "   "])
def test_blank_message_proceeds_without_event(tmp_path, message):
    store = _init_store(tmp_path)
    before = len(store.meta.read_all())
    assert on_before_send(message, store=store).action == "proceed"
    assert len(store.meta.read_all()) == before


def test_plain_message_proceeds_without_event(tmp_path):
    store = _init_store(tmp_path)
    before = len(store.meta.read_all())
    result = on_before_send("What's the status of the project?", store=store)
    assert result.action == "proceed"
    assert result.target is None
    assert result.pattern is None
    assert len(store.meta.read_all()) == before


@pytest.mark.parametrize(
    "message",
    ["rebuilding credibility with users", "The builder pattern is nice"],
)
def test_substring_matches_do_not_intercept(tmp_path, message):
    """Full-word matching: 'build' must not fire inside rebuild/builder."""
    store = _init_store(tmp_path)
    before = len(store.meta.read_all())
    assert find_implementation_intent(message) is None
    assert on_before_send(message, store=store).action == "proceed"
    assert len(store.meta.read_all()) == before


# ---------------------------------------------------------------------------
# Interception + redirect
# ---------------------------------------------------------------------------


def test_implement_redirects_to_add_idea_on_empty_backlog(tmp_path):
    store = _init_store(tmp_path)
    result = on_before_send("Implement SSO login", store=store)
    assert result.action == "redirect"
    assert result.target == "intent:add-idea"
    assert result.pattern == "implement"
    assert "override intent" in result.message  # bypass surfaced, never silent

    events = store.meta.read_all()
    assert _event_types(store)[-1] == "INTENT_INTERCEPTED"
    decision = events[-1].decision
    assert decision.pattern_matched == "implement"
    assert decision.redirect_target == "intent:add-idea"
    assert decision.original_message_excerpt == "Implement SSO login"
    assert events[-1].actor.type == "agent"


def test_matching_is_case_insensitive(tmp_path):
    store = _init_store(tmp_path)
    result = on_before_send("Please BUILD the export page", store=store)
    assert result.action == "redirect"
    assert result.pattern == "build"


def test_multiword_phrase_matches(tmp_path):
    store = _init_store(tmp_path)
    result = on_before_send("Can you add feature flags?", store=store)
    assert result.action == "redirect"
    assert result.pattern == "add feature"


def test_first_list_pattern_wins(tmp_path):
    store = _init_store(tmp_path)
    result = on_before_send("build and implement the cache", store=store)
    assert result.pattern == "implement"  # earlier in IMPLEMENTATION_PATTERNS


def test_untriaged_ideas_redirect_to_triage(tmp_path):
    store, idea_id = _store_with_untriaged_idea(tmp_path)
    result = on_before_send("implement SSO", store=store)
    assert result.action == "redirect"
    assert result.target == "intent:triage"
    assert idea_id in result.message
    assert store.meta.read_all()[-1].decision.redirect_target == "intent:triage"


def test_approved_design_redirects_to_spec_status(tmp_path):
    store, spec_id = _store_with_approved_design(tmp_path)
    assert store.specs.get(spec_id).status == SpecStatus.DESIGN_APPROVED
    result = on_before_send("let's build it now", store=store)
    assert result.action == "redirect"
    assert result.target == "intent:spec-status"
    assert spec_id in result.message
    assert store.meta.read_all()[-1].decision.redirect_target == "intent:spec-status"


def test_excerpt_truncated_to_limit(tmp_path):
    store = _init_store(tmp_path)
    long_message = "implement " + "x" * 500
    on_before_send(long_message, store=store)
    excerpt = store.meta.read_all()[-1].decision.original_message_excerpt
    assert len(excerpt) == EXCERPT_LEN


# ---------------------------------------------------------------------------
# Override / bypass
# ---------------------------------------------------------------------------


def test_bypass_phrase_skips_matching_and_logs(tmp_path):
    store = _init_store(tmp_path)
    result = on_before_send("override intent: implement SSO now", store=store)
    assert result.action == "bypass"
    assert result.target is None
    assert "logged" in result.message  # surfaced, never silent

    types = _event_types(store)
    assert types[-1] == "INTENT_BYPASS_USED"
    assert "INTENT_INTERCEPTED" not in types
    decision = store.meta.read_all()[-1].decision
    assert decision.bypass_phrase == "override intent"
    assert "implement SSO" in decision.original_message_excerpt


def test_bypass_matching_is_case_insensitive(tmp_path):
    store = _init_store(tmp_path)
    result = on_before_send("OVERRIDE INTENT just do it", store=store)
    assert result.action == "bypass"
    assert _event_types(store)[-1] == "INTENT_BYPASS_USED"


# ---------------------------------------------------------------------------
# Manifest wiring
# ---------------------------------------------------------------------------


def test_manifest_before_send_hook_redirects(tmp_path):
    from mission_ctrl_pi.extension import Extension

    store = _init_store(tmp_path)
    hook = Extension().hooks["on_before_send"]
    result = hook("implement SSO", {"cwd": str(tmp_path)})
    assert result.action == "redirect"
    assert result.target == "intent:add-idea"
    assert "INTENT_INTERCEPTED" in _event_types(store)


def test_manifest_before_send_hook_no_ops_without_intent(tmp_path):
    from mission_ctrl_pi.extension import Extension

    hook = Extension().hooks["on_before_send"]
    result = hook("implement SSO", {"cwd": str(tmp_path)})
    assert result.action == "proceed"
    assert not (tmp_path / ".intent").exists()


# ---------------------------------------------------------------------------
# E2E on a copied mid-flight fixture (never write to the shared fixture dir)
# ---------------------------------------------------------------------------

CORE_FIXTURES = Path(__file__).resolve().parents[2] / "core" / "tests" / "fixtures"


def _copied_mid_flight(tmp_path) -> IntentStore:
    shutil.copytree(CORE_FIXTURES / "mid-flight" / ".intent", tmp_path / ".intent")
    return IntentStore(tmp_path)


def test_e2e_intercept_on_mid_flight_fixture(tmp_path):
    store = _copied_mid_flight(tmp_path)
    before = len(store.meta.read_all())
    result = on_before_send("implement the export retry", store=store)
    assert result.action == "redirect"
    # No untriaged ideas and no design-approved spec → add-idea.
    assert result.target == "intent:add-idea"
    events = store.meta.read_all()
    assert len(events) == before + 1
    assert events[-1].event_type == "INTENT_INTERCEPTED"
    assert events[-1].decision.pattern_matched == "implement"


def test_e2e_bypass_on_mid_flight_fixture(tmp_path):
    store = _copied_mid_flight(tmp_path)
    before = len(store.meta.read_all())
    result = on_before_send("override intent: implement it anyway", store=store)
    assert result.action == "bypass"
    events = store.meta.read_all()
    assert len(events) == before + 1
    assert events[-1].event_type == "INTENT_BYPASS_USED"
