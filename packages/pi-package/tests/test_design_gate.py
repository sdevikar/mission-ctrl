"""Tests for M2b design-gate skills (recap, design-propose, design-approve)."""

from __future__ import annotations

import pytest
from mission_ctrl_core.models import SpecStatus
from mission_ctrl_core.stores import IntentStore
from mission_ctrl_pi.schemas import (
    AddIdeaInput,
    DesignApproveInput,
    DesignProposeInput,
    InitInput,
    RecapInput,
    SkillError,
    SpecCreateInput,
    SpecStatusInput,
    TriageInput,
)
from mission_ctrl_pi.skills import (
    intent_add_idea,
    intent_design_approve,
    intent_design_propose,
    intent_init,
    intent_recap,
    intent_spec_create,
    intent_spec_status,
    intent_triage,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def initialized_store(tmp_path):
    store = IntentStore(tmp_path)
    intent_init(
        InitInput(project_name="TestApp", mission="A great mission"), store=store
    )
    return store


@pytest.fixture
def store_with_draft_spec(initialized_store):
    """One draft spec ready for design-propose; returns (store, spec_id)."""
    add = intent_add_idea(AddIdeaInput(title="Big Feature"), store=initialized_store)
    intent_triage(
        TriageInput(idea_id=add.idea_id, bucket="mvp", alignment_verdict="Core"),
        store=initialized_store,
    )
    create = intent_spec_create(
        SpecCreateInput(idea_id=add.idea_id), store=initialized_store
    )
    return initialized_store, create.spec_id


# ---------------------------------------------------------------------------
# intent:recap
# ---------------------------------------------------------------------------


def test_recap_returns_recap_result(initialized_store):
    from mission_ctrl_core.logic.recap import RecapResult

    result = intent_recap(store=initialized_store)
    assert isinstance(result, RecapResult)
    assert result.mission == "A great mission"
    assert result.mvp_percent == 0


def test_recap_brief_verbosity(initialized_store):
    result = intent_recap(RecapInput(verbosity="brief"), store=initialized_store)
    assert result.verbosity == "brief"
    assert "MVP" in result.rendered


def test_recap_standard_verbosity(initialized_store):
    result = intent_recap(RecapInput(verbosity="standard"), store=initialized_store)
    assert result.verbosity == "standard"


def test_recap_full_verbosity(initialized_store):
    result = intent_recap(RecapInput(verbosity="full"), store=initialized_store)
    assert result.verbosity == "full"


def test_recap_default_verbosity_is_standard(initialized_store):
    result = intent_recap(store=initialized_store)
    assert result.verbosity == "standard"


def test_recap_on_store_with_spec(store_with_draft_spec):
    store, spec_id = store_with_draft_spec
    result = intent_recap(store=store)
    assert result.mission == "A great mission"
    # draft spec is not in_progress, so no last_focus
    assert result.last_focus is None


def test_recap_is_read_only(initialized_store):
    events_before = len(initialized_store.meta.read_all())
    intent_recap(store=initialized_store)
    events_after = len(initialized_store.meta.read_all())
    assert events_before == events_after


# ---------------------------------------------------------------------------
# intent:design-propose
# ---------------------------------------------------------------------------


def test_design_propose_draft_to_proposed(store_with_draft_spec):
    store, spec_id = store_with_draft_spec

    result = intent_design_propose(
        DesignProposeInput(
            spec_id=spec_id, digest="This is the design digest with enough chars"
        ),
        store=store,
    )
    assert result.spec_id == spec_id
    assert result.status == "design_proposed"
    assert store.specs.get(spec_id).status == SpecStatus.DESIGN_PROPOSED

    # DESIGN_PROPOSED event was emitted
    events = [e for e in store.meta.read_all() if e.event_type == "DESIGN_PROPOSED"]
    assert len(events) == 1


def test_design_propose_rejects_non_draft(store_with_draft_spec):
    store, spec_id = store_with_draft_spec
    # Move to in_progress first (M2a path)
    intent_spec_status(
        SpecStatusInput(spec_id=spec_id, new_status="in_progress"), store=store
    )

    with pytest.raises(SkillError) as exc:
        intent_design_propose(
            DesignProposeInput(
                spec_id=spec_id, digest="Cannot propose when in_progress"
            ),
            store=store,
        )
    assert exc.value.code == "ILLEGAL_TRANSITION"


def test_design_propose_rejects_unknown_spec(initialized_store):
    with pytest.raises(SkillError) as exc:
        intent_design_propose(
            DesignProposeInput(spec_id="spec_999", digest="Unknown spec design"),
            store=initialized_store,
        )
    assert exc.value.code == "NOT_FOUND"


def test_design_propose_digest_min_length(store_with_draft_spec):
    """Pydantic validation: digest must be ≥ 10 chars."""
    store, spec_id = store_with_draft_spec
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        DesignProposeInput(spec_id=spec_id, digest="short")


# ---------------------------------------------------------------------------
# intent:design-approve
# ---------------------------------------------------------------------------


def test_design_approve_approved(store_with_draft_spec):
    store, spec_id = store_with_draft_spec
    intent_design_propose(
        DesignProposeInput(spec_id=spec_id, digest="Detailed design reasoning here"),
        store=store,
    )

    result = intent_design_approve(
        DesignApproveInput(spec_id=spec_id, decision="approved"),
        store=store,
    )
    assert result.spec_id == spec_id
    assert result.decision == "approved"
    assert result.new_status == "design_approved"
    assert store.specs.get(spec_id).status == SpecStatus.DESIGN_APPROVED

    events = [e for e in store.meta.read_all() if e.event_type == "DESIGN_APPROVED"]
    assert len(events) == 1
    assert events[0].decision.approval is True


def test_design_approve_rejected_with_notes(store_with_draft_spec):
    store, spec_id = store_with_draft_spec
    intent_design_propose(
        DesignProposeInput(spec_id=spec_id, digest="Initial design attempt here"),
        store=store,
    )

    result = intent_design_approve(
        DesignApproveInput(
            spec_id=spec_id,
            decision="rejected",
            notes="Missing data flow diagram and error handling details",
        ),
        store=store,
    )
    assert result.decision == "rejected"
    assert result.new_status == "draft"
    # Spec goes back to draft
    assert store.specs.get(spec_id).status == SpecStatus.DRAFT

    events = [e for e in store.meta.read_all() if e.event_type == "DESIGN_APPROVED"]
    assert len(events) == 1
    assert events[0].decision.approval is False
    assert "Missing data flow" in (events[0].decision.notes or "")


def test_design_approve_rejected_without_notes_fails(store_with_draft_spec):
    store, spec_id = store_with_draft_spec
    intent_design_propose(
        DesignProposeInput(spec_id=spec_id, digest="Design digest content here"),
        store=store,
    )

    with pytest.raises(SkillError) as exc:
        intent_design_approve(
            DesignApproveInput(spec_id=spec_id, decision="rejected"),
            store=store,
        )
    assert exc.value.code == "NOTES_REQUIRED"


def test_design_approve_rejects_non_proposed_spec(store_with_draft_spec):
    """design-approve raises ILLEGAL_TRANSITION unless spec is design_proposed."""
    store, spec_id = store_with_draft_spec

    with pytest.raises(SkillError) as exc:
        intent_design_approve(
            DesignApproveInput(spec_id=spec_id, decision="approved"),
            store=store,
        )
    assert exc.value.code == "ILLEGAL_TRANSITION"


def test_design_approve_rejects_unknown_spec(initialized_store):
    with pytest.raises(SkillError) as exc:
        intent_design_approve(
            DesignApproveInput(spec_id="spec_999", decision="approved"),
            store=initialized_store,
        )
    assert exc.value.code == "NOT_FOUND"


# ---------------------------------------------------------------------------
# State machine: design_approved → in_progress via spec-status
# ---------------------------------------------------------------------------


def test_spec_status_design_approved_to_in_progress(store_with_draft_spec):
    store, spec_id = store_with_draft_spec
    # Propose → approve → in_progress
    intent_design_propose(
        DesignProposeInput(spec_id=spec_id, digest="Design reasoning in full here"),
        store=store,
    )
    intent_design_approve(
        DesignApproveInput(spec_id=spec_id, decision="approved"),
        store=store,
    )
    # Now spec-status should allow design_approved → in_progress
    res = intent_spec_status(
        SpecStatusInput(spec_id=spec_id, new_status="in_progress"),
        store=store,
    )
    assert res.previous_status == "design_approved"
    assert res.new_status == "in_progress"
    assert store.specs.get(spec_id).status == SpecStatus.IN_PROGRESS


def test_spec_status_rejects_draft_to_done_still(store_with_draft_spec):
    """M2a illegal transitions still rejected after M2b extension."""
    store, spec_id = store_with_draft_spec
    with pytest.raises(SkillError) as exc:
        intent_spec_status(
            SpecStatusInput(spec_id=spec_id, new_status="done"),
            store=store,
        )
    assert exc.value.code == "ILLEGAL_TRANSITION"


def test_spec_status_design_proposed_not_allowed_to_in_progress_directly(
    store_with_draft_spec,
):
    """design_proposed must go through design-approve, not directly in_progress."""
    store, spec_id = store_with_draft_spec
    # Set to design_proposed by hand
    store.specs.set_status(spec_id, SpecStatus.DESIGN_PROPOSED)

    with pytest.raises(SkillError) as exc:
        intent_spec_status(
            SpecStatusInput(spec_id=spec_id, new_status="in_progress"),
            store=store,
        )
    assert exc.value.code == "ILLEGAL_TRANSITION"
