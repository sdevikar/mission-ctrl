from __future__ import annotations

from mission_ctrl_core.models import Bucket, SpecStatus
from mission_ctrl_core.stores import IntentStore
from mission_ctrl_pi.schemas import (
    AddIdeaInput,
    DesignApproveInput,
    DesignProposeInput,
    InitInput,
    SpecCreateInput,
    SpecStatusInput,
    TriageInput,
)
from mission_ctrl_pi.skills import (
    intent_add_idea,
    intent_design_approve,
    intent_design_propose,
    intent_init,
    intent_next,
    intent_spec_create,
    intent_spec_status,
    intent_status,
    intent_triage,
)


def test_core_lifecycle_e2e(tmp_path):
    store = IntentStore(tmp_path)

    # 1. intent:init
    init_res = intent_init(
        InitInput(project_name="MissionDogfood", mission="Build an end-to-end system"),
        store=store,
    )
    assert init_res.status == "created"
    assert store.mission.read().statement == "Build an end-to-end system"
    assert len(store.meta.read_all()) == 1

    # 2. intent:add-idea
    add_res = intent_add_idea(
        AddIdeaInput(title="Initial core feature", description="First step"),
        store=store,
    )
    assert add_res.status == "added"
    idea_id = add_res.idea_id
    assert store.backlog.get(idea_id).bucket == Bucket.UNTRIAGED
    assert len(store.meta.read_all()) == 2

    # 3. intent:triage
    triage_res = intent_triage(
        TriageInput(
            idea_id=idea_id, bucket="mvp", alignment_verdict="Essential for MVP"
        ),
        store=store,
    )
    assert triage_res.status == "triaged"
    assert store.backlog.get(idea_id).bucket == Bucket.MVP_CRITICAL
    assert len(store.meta.read_all()) == 3

    # 4. intent:spec-create
    create_res = intent_spec_create(
        SpecCreateInput(idea_id=idea_id, title="Implement initial feature"),
        store=store,
    )
    assert create_res.status == "draft"
    spec_id = create_res.spec_id
    node = store.specs.get(spec_id)
    assert node.status == SpecStatus.DRAFT
    assert len(store.meta.read_all()) == 4

    # 5. intent:spec-status -> in_progress
    status_prog_res = intent_spec_status(
        SpecStatusInput(spec_id=spec_id, new_status="in_progress"),
        store=store,
    )
    assert status_prog_res.previous_status == "draft"
    assert status_prog_res.new_status == "in_progress"
    assert store.specs.get(spec_id).status == SpecStatus.IN_PROGRESS
    assert len(store.meta.read_all()) == 5

    # 6. intent:spec-status -> done
    status_done_res = intent_spec_status(
        SpecStatusInput(spec_id=spec_id, new_status="done"),
        store=store,
    )
    assert status_done_res.previous_status == "in_progress"
    assert status_done_res.new_status == "done"
    assert store.specs.get(spec_id).status == SpecStatus.DONE
    assert len(store.meta.read_all()) == 6

    # 7. intent:next
    next_res = intent_next(store=store)
    # Since only spec is now done, nothing unblocked is remaining
    assert next_res.spec_id is None

    # 8. intent:status
    dash = intent_status(store=store)
    assert dash.mission == "Build an end-to-end system"
    assert len(dash.active_specs) == 0  # No active specs since spec_001 is done
    assert len(store.meta.read_all()) == 6  # Read-only didn't append any event


def test_full_lifecycle_with_design_gate_e2e(tmp_path):
    """M2b full lifecycle: init → add-idea → triage → spec-create →
    design-propose → design-approve → spec-status(in_progress) →
    spec-status(done) → status, asserting `.intent/` state at each step."""
    store = IntentStore(tmp_path)

    # 1. intent:init
    init_res = intent_init(
        InitInput(project_name="DesignGateApp", mission="Ship gated designs"),
        store=store,
    )
    assert init_res.status == "created"
    assert store.mission.read().statement == "Ship gated designs"
    assert [e.event_type for e in store.meta.read_all()] == ["INTENT_CREATED"]

    # 2. intent:add-idea
    add_res = intent_add_idea(
        AddIdeaInput(title="Gated feature", description="Needs design review"),
        store=store,
    )
    assert add_res.status == "added"
    idea_id = add_res.idea_id
    assert store.backlog.get(idea_id).bucket == Bucket.UNTRIAGED

    # 3. intent:triage
    triage_res = intent_triage(
        TriageInput(idea_id=idea_id, bucket="mvp", alignment_verdict="Core MVP scope"),
        store=store,
    )
    assert triage_res.status == "triaged"
    assert store.backlog.get(idea_id).bucket == Bucket.MVP_CRITICAL

    # 4. intent:spec-create
    create_res = intent_spec_create(
        SpecCreateInput(idea_id=idea_id, title="Build gated feature"),
        store=store,
    )
    assert create_res.status == "draft"
    spec_id = create_res.spec_id
    assert store.specs.get(spec_id).status == SpecStatus.DRAFT

    # 5. intent:design-propose (draft → design_proposed)
    propose_res = intent_design_propose(
        DesignProposeInput(spec_id=spec_id, digest="Layered design with retries"),
        store=store,
    )
    assert propose_res.status == "design_proposed"
    assert store.specs.get(spec_id).status == SpecStatus.DESIGN_PROPOSED

    # 6. intent:design-approve (design_proposed → design_approved)
    approve_res = intent_design_approve(
        DesignApproveInput(spec_id=spec_id, decision="approved"),
        store=store,
    )
    assert approve_res.new_status == "design_approved"
    assert store.specs.get(spec_id).status == SpecStatus.DESIGN_APPROVED

    # 7. intent:spec-status → in_progress (design-gate exit)
    prog_res = intent_spec_status(
        SpecStatusInput(spec_id=spec_id, new_status="in_progress"),
        store=store,
    )
    assert prog_res.previous_status == "design_approved"
    assert prog_res.new_status == "in_progress"
    assert store.specs.get(spec_id).status == SpecStatus.IN_PROGRESS

    # 8. intent:spec-status → done
    done_res = intent_spec_status(
        SpecStatusInput(spec_id=spec_id, new_status="done"),
        store=store,
    )
    assert done_res.previous_status == "in_progress"
    assert done_res.new_status == "done"
    assert store.specs.get(spec_id).status == SpecStatus.DONE

    # Full event trail in order
    assert [e.event_type for e in store.meta.read_all()] == [
        "INTENT_CREATED",
        "BACKLOG_ADDED",
        "BACKLOG_TRIAGE",
        "SPEC_CREATED",
        "DESIGN_PROPOSED",
        "DESIGN_APPROVED",
        "SPEC_STATUS_UPDATED",
        "SPEC_STATUS_UPDATED",
    ]

    # 9. intent:next + intent:status (both read-only)
    next_res = intent_next(store=store)
    assert next_res.spec_id is None  # only spec is done
    dash = intent_status(store=store)
    assert dash.mission == "Ship gated designs"
    assert len(dash.active_specs) == 0
    assert len(store.meta.read_all()) == 8
