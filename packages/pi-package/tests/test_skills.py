from __future__ import annotations

import pytest
from mission_ctrl_core.models import SpecNode, Specs, SpecStatus
from mission_ctrl_core.stores import IntentStore
from mission_ctrl_pi.schemas import (
    AddIdeaInput,
    InitInput,
    SkillError,
    SpecCreateInput,
    SpecStatusInput,
    TriageInput,
)
from mission_ctrl_pi.skills import (
    intent_add_idea,
    intent_init,
    intent_next,
    intent_spec_create,
    intent_spec_status,
    intent_status,
    intent_triage,
)


@pytest.fixture
def empty_store(tmp_path):
    store = IntentStore(tmp_path)
    return store


@pytest.fixture
def initialized_store(empty_store):
    intent_init(
        InitInput(project_name="TestApp", mission="A great mission"), store=empty_store
    )
    return empty_store


def test_init_skill(empty_store):
    res = intent_init(
        InitInput(project_name="Demo", mission="Our mission"), store=empty_store
    )
    assert res.status == "created"
    assert (empty_store.intent_dir / "mission.json").exists()
    assert (empty_store.intent_dir / "meta.jsonl").exists()
    assert empty_store.mission.read().statement == "Our mission"

    # Second init fails
    with pytest.raises(SkillError) as exc:
        intent_init(InitInput(project_name="Demo2"), store=empty_store)
    assert exc.value.code == "ALREADY_INITIALIZED"


def test_add_idea_skill(initialized_store):
    res = intent_add_idea(
        AddIdeaInput(title="Idea 1", description="Details 1"), store=initialized_store
    )
    assert res.status == "added"
    assert res.idea_id == "idea_001"

    item = initialized_store.backlog.get("idea_001")
    assert item is not None
    assert item.title == "Idea 1"
    assert item.description == "Details 1"
    assert item.bucket.value == "untriaged"

    events = initialized_store.meta.read_all()
    # 1 from init, 1 from add_idea
    assert len(events) == 2
    assert events[-1].event_type == "BACKLOG_ADDED"


def test_triage_skill(initialized_store):
    add_res = intent_add_idea(AddIdeaInput(title="Idea 1"), store=initialized_store)

    # Triage to mvp
    triage_res = intent_triage(
        TriageInput(
            idea_id=add_res.idea_id,
            bucket="mvp",
            alignment_verdict="Directly serves mission",
        ),
        store=initialized_store,
    )
    assert triage_res.status == "triaged"
    assert triage_res.bucket == "mvp"

    item = initialized_store.backlog.get(add_res.idea_id)
    assert item.bucket.value == "mvp_critical"

    # Non-existent idea raises NOT_FOUND
    with pytest.raises(SkillError) as exc:
        intent_triage(
            TriageInput(idea_id="bkl_999", bucket="later", alignment_verdict="Not now"),
            store=initialized_store,
        )
    assert exc.value.code == "NOT_FOUND"


def test_spec_create_skill(initialized_store):
    add_res = intent_add_idea(
        AddIdeaInput(title="Feature Idea"), store=initialized_store
    )

    # Creating spec before triaging raises INVALID_INPUT
    with pytest.raises(SkillError) as exc:
        intent_spec_create(
            SpecCreateInput(idea_id=add_res.idea_id), store=initialized_store
        )
    assert exc.value.code == "INVALID_INPUT"

    # Triage to mvp
    intent_triage(
        TriageInput(idea_id=add_res.idea_id, bucket="mvp", alignment_verdict="Crucial"),
        store=initialized_store,
    )

    # Create spec with default title
    spec_res = intent_spec_create(
        SpecCreateInput(idea_id=add_res.idea_id), store=initialized_store
    )
    assert spec_res.spec_id == "spec_001"
    assert spec_res.status == "draft"

    node = initialized_store.specs.get("spec_001")
    assert node is not None
    assert node.title == "Feature Idea"
    assert node.status == SpecStatus.DRAFT
    assert node.links.ideas == [add_res.idea_id]

    # Check backlink on backlog item
    item = initialized_store.backlog.get(add_res.idea_id)
    assert "spec_001" in item.links.specs


def test_spec_status_transitions_m2a(initialized_store):
    add_res = intent_add_idea(AddIdeaInput(title="Feature"), store=initialized_store)
    intent_triage(
        TriageInput(idea_id=add_res.idea_id, bucket="mvp", alignment_verdict="Go"),
        store=initialized_store,
    )
    spec_res = intent_spec_create(
        SpecCreateInput(idea_id=add_res.idea_id), store=initialized_store
    )
    spec_id = spec_res.spec_id

    # 1. Illegal direct transition: draft -> done
    with pytest.raises(SkillError) as exc:
        intent_spec_status(
            SpecStatusInput(spec_id=spec_id, new_status="done"), store=initialized_store
        )
    assert exc.value.code == "ILLEGAL_TRANSITION"

    # 2. Blocked transition requires a note
    with pytest.raises(SkillError) as exc:
        intent_spec_status(
            SpecStatusInput(spec_id=spec_id, new_status="blocked"),
            store=initialized_store,
        )
    assert exc.value.code == "INVALID_INPUT"

    # 3. Draft -> blocked with note
    st_res = intent_spec_status(
        SpecStatusInput(
            spec_id=spec_id,
            new_status="blocked",
            note="Waiting for external dependency",
        ),
        store=initialized_store,
    )
    assert st_res.previous_status == "draft"
    assert st_res.new_status == "blocked"

    # 4. Blocked -> in_progress
    st_res2 = intent_spec_status(
        SpecStatusInput(spec_id=spec_id, new_status="in_progress"),
        store=initialized_store,
    )
    assert st_res2.previous_status == "blocked"
    assert st_res2.new_status == "in_progress"

    # 5. In_progress -> done
    st_res3 = intent_spec_status(
        SpecStatusInput(spec_id=spec_id, new_status="done"),
        store=initialized_store,
    )
    assert st_res3.previous_status == "in_progress"
    assert st_res3.new_status == "done"

    # 6. Cannot transition out of done
    with pytest.raises(SkillError) as exc:
        intent_spec_status(
            SpecStatusInput(spec_id=spec_id, new_status="in_progress"),
            store=initialized_store,
        )
    assert exc.value.code == "ILLEGAL_TRANSITION"


def test_spec_status_dep_gating(initialized_store):
    # Setup: spec B depends on spec A
    # A is draft, B is draft
    # Transitioning B to in_progress should fail because A is not done
    initialized_store.specs.write(
        Specs(
            nodes=[
                SpecNode(id="spec_001", title="A", status=SpecStatus.DRAFT),
                SpecNode(
                    id="spec_002",
                    title="B",
                    status=SpecStatus.DRAFT,
                    depends_on=["spec_001"],
                ),
            ]
        )
    )

    with pytest.raises(SkillError) as exc:
        intent_spec_status(
            SpecStatusInput(spec_id="spec_002", new_status="in_progress"),
            store=initialized_store,
        )
    assert exc.value.code == "ILLEGAL_TRANSITION"


def test_read_only_skills_leave_store_untouched(initialized_store):
    add_res = intent_add_idea(AddIdeaInput(title="Feature"), store=initialized_store)
    intent_triage(
        TriageInput(idea_id=add_res.idea_id, bucket="mvp", alignment_verdict="Go"),
        store=initialized_store,
    )
    intent_spec_create(
        SpecCreateInput(idea_id=add_res.idea_id), store=initialized_store
    )

    events_before = initialized_store.meta.read_all()
    m_before = initialized_store.mission.read()
    s_before = initialized_store.specs.read()

    # Call read-only skills
    nxt = intent_next(store=initialized_store)
    assert nxt.spec_id == "spec_001"

    status = intent_status(store=initialized_store)
    assert status.mission == initialized_store.mission.read().statement
    assert len(status.active_specs) == 1

    events_after = initialized_store.meta.read_all()
    assert len(events_before) == len(events_after)
    assert m_before == initialized_store.mission.read()
    assert s_before == initialized_store.specs.read()
