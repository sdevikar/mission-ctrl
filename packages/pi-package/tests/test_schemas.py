from __future__ import annotations

import pytest
from mission_ctrl_pi.schemas import (
    AddIdeaInput,
    AddIdeaResult,
    InitInput,
    InitResult,
    NextResult,
    SkillError,
    SpecCreateInput,
    SpecCreateResult,
    SpecStatusInput,
    SpecStatusResult,
    SpecSummary,
    StatusResult,
    TriageInput,
    TriageResult,
)
from pydantic import ValidationError


def test_init_schemas():
    inp = InitInput(project_name="demo")
    assert inp.project_name == "demo"
    assert inp.mission is None

    inp_mission = InitInput(project_name="demo", mission="Build something great")
    assert inp_mission.mission == "Build something great"

    res = InitResult(status="created", intent_dir="/tmp/test/.intent")
    assert res.status == "created"
    assert res.intent_dir == "/tmp/test/.intent"

    with pytest.raises(ValidationError):
        InitInput()


def test_add_idea_schemas():
    inp = AddIdeaInput(title="Idea A", description="Desc")
    assert inp.title == "Idea A"
    assert inp.description == "Desc"

    res = AddIdeaResult(idea_id="bkl_001", status="added")
    assert res.idea_id == "bkl_001"
    assert res.status == "added"

    with pytest.raises(ValidationError):
        AddIdeaInput(title="")


def test_triage_schemas():
    inp = TriageInput(
        idea_id="bkl_001", bucket="mvp", alignment_verdict="Aligned with mission"
    )
    assert inp.bucket == "mvp"

    res = TriageResult(idea_id="bkl_001", bucket="mvp", status="triaged")
    assert res.status == "triaged"

    with pytest.raises(ValidationError):
        TriageInput(idea_id="bkl_001", bucket="invalid", alignment_verdict="reason")


def test_spec_create_schemas():
    inp = SpecCreateInput(idea_id="bkl_001")
    assert inp.title is None
    inp2 = SpecCreateInput(idea_id="bkl_001", title="Custom Title")
    assert inp2.title == "Custom Title"

    res = SpecCreateResult(spec_id="spec_001", status="draft")
    assert res.status == "draft"


def test_spec_status_schemas():
    inp = SpecStatusInput(spec_id="spec_001", new_status="in_progress")
    assert inp.new_status == "in_progress"

    res = SpecStatusResult(
        spec_id="spec_001", previous_status="draft", new_status="in_progress"
    )
    assert res.previous_status == "draft"
    assert res.new_status == "in_progress"

    with pytest.raises(ValidationError):
        SpecStatusInput(spec_id="spec_001", new_status="unknown_status")


def test_next_and_status_schemas():
    nxt = NextResult(spec_id="spec_001", title="A", reason="Highest priority")
    assert nxt.spec_id == "spec_001"

    status = StatusResult(
        mission="Test mission",
        mvp_completion_pct=50.0,
        active_specs=[SpecSummary(id="spec_001", title="A", status="in_progress")],
        next_suggestion=nxt,
    )
    assert status.mvp_completion_pct == 50.0
    assert len(status.active_specs) == 1


def test_skill_error():
    err = SkillError("ILLEGAL_TRANSITION", "Cannot transition to done directly")
    assert err.code == "ILLEGAL_TRANSITION"
    assert "Cannot transition" in err.message
    assert str(err) == "[ILLEGAL_TRANSITION] Cannot transition to done directly"
