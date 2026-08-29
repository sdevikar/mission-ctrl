import json
from pathlib import Path
from typing import Any

import pytest
from mission_ctrl_core.errors import MissionCtrlError
from mission_ctrl_core.models import (
    Backlog,
    Constraints,
    MetaEventAdapter,
    Mission,
    Mvp,
    Specs,
)
from mission_ctrl_core.models.common import next_id
from pydantic import ValidationError

EXAMPLES = Path(__file__).parents[3] / "docs" / "examples" / "domain"


def load(name: str) -> Any:
    return json.loads((EXAMPLES / name).read_text())


def test_mission_parses_living_sample() -> None:
    mission = Mission.model_validate(load("mission.json"))
    assert mission.id == "mis_001"
    assert len(mission.success_criteria) == 3


def test_mvp_parses_living_sample() -> None:
    mvp = Mvp.model_validate(load("mvp.json"))
    assert mvp.items[0].id == "mvp_001"
    assert mvp.items[0].linked_specs == ["spec_001"]


def test_constraints_parse_living_sample() -> None:
    data = Constraints.model_validate(load("constraints.json"))
    assert data.constraints[0].severity == "high"


def test_backlog_parses_living_sample() -> None:
    backlog = Backlog.model_validate(load("backlog.json"))
    assert backlog.items[0].bucket == "parked"
    assert backlog.items[0].alignment.mission == "weak"


def test_backlog_alignment_mvp_enforced() -> None:
    item = load("backlog.json")["items"][0]
    item["alignment"]["mvp"] = "sometimes"
    with pytest.raises(ValidationError, match="mvp"):
        Backlog.model_validate({"items": [item]})


def test_backlog_bad_id_rejected() -> None:
    item = load("backlog.json")["items"][0]
    item["id"] = "X-123"
    with pytest.raises(ValidationError, match="id"):
        Backlog.model_validate({"items": [item]})


def test_specs_parse_living_sample() -> None:
    specs = Specs.model_validate(load("specs.json"))
    assert specs.nodes[0].status == "design_approved"


def test_specs_bad_status_rejected() -> None:
    data = load("specs.json")
    data["nodes"][0]["status"] = "cancelled"
    with pytest.raises(ValidationError, match="status"):
        Specs.model_validate(data)


def test_mission_bad_id_rejected() -> None:
    data = load("mission.json")
    data["id"] = "mission_1"
    with pytest.raises(ValidationError, match="id"):
        Mission.model_validate(data)


def test_utc_roundtrip_normalizes_to_zulu() -> None:
    data = load("mission.json")
    data["created_at"] = "2026-03-10T10:15:00+02:00"
    assert Mission.model_validate(data).model_dump_json().count("+02:00") == 0
    data["created_at"] = "2026-03-10T10:15:00"
    with pytest.raises(ValidationError, match="UTC"):
        Mission.model_validate(data)


def test_event_roundtrip_spec_status_updated() -> None:
    raw = {
        "event_id": "evt_000001",
        "timestamp": "2026-03-12T14:05:00Z",
        "event_type": "SPEC_STATUS_UPDATED",
        "actor": {"type": "agent", "name": "spec-skill"},
        "affected_entities": [{"type": "spec", "id": "spec_001"}],
        "linked_intent": {
            "mission_id": "mis_001",
            "mvp_version": "v1.0",
            "constraints_version": "v1.0",
        },
        "decision": {"from": "draft", "to": "in_progress"},
        "reasoning": "Design approved, work starting.",
        "depends_on": [],
        "git_refs": [],
        "tags": ["status"],
        "session": {"id": "ses_0003"},
    }
    event = MetaEventAdapter.validate_python(raw)
    assert type(event).__name__ == "SpecStatusUpdatedEvent"
    assert event.decision.from_status == "draft"
    assert '"from":"draft"' in event.model_dump_json(by_alias=True)


def test_event_missing_reasoning_rejected() -> None:
    raw = {
        "event_id": "evt_000002",
        "timestamp": "2026-03-12T14:05:00Z",
        "event_type": "BACKLOG_ADDED",
        "actor": {"type": "human", "name": "owner"},
        "affected_entities": [{"type": "idea", "id": "idea_001"}],
        "linked_intent": {
            "mission_id": "mis_001",
            "mvp_version": "v1.0",
            "constraints_version": "v1.0",
        },
        "decision": {"title": "Add search", "bucket": "untriaged"},
        "session": {"id": "ses_0001"},
    }
    with pytest.raises(ValidationError, match="reasoning"):
        MetaEventAdapter.validate_python(raw)


def test_event_bad_id_rejected() -> None:
    raw = {
        "event_id": "EV-1",
        "timestamp": "2026-03-12T14:05:00Z",
        "event_type": "BACKLOG_ADDED",
        "actor": {"type": "human", "name": "owner"},
        "affected_entities": [],
        "linked_intent": {
            "mission_id": "mis_001",
            "mvp_version": "v1.0",
            "constraints_version": "v1.0",
        },
        "decision": {"title": "x", "bucket": "untriaged"},
        "reasoning": "test",
        "session": {"id": "ses_0001"},
    }
    with pytest.raises(ValidationError, match="event_id"):
        MetaEventAdapter.validate_python(raw)


def test_event_unknown_type_rejected() -> None:
    raw = {
        "event_id": "evt_000003",
        "timestamp": "2026-03-12T14:05:00Z",
        "event_type": "NOT_A_REAL_EVENT",
        "actor": {"type": "human", "name": "owner"},
        "affected_entities": [],
        "linked_intent": {
            "mission_id": "mis_001",
            "mvp_version": "v1.0",
            "constraints_version": "v1.0",
        },
        "decision": {},
        "reasoning": "test",
        "session": {"id": "ses_0001"},
    }
    with pytest.raises(ValidationError, match="NOT_A_REAL_EVENT"):
        MetaEventAdapter.validate_python(raw)


def test_render_validation_error_names_file_and_field() -> None:
    from mission_ctrl_core.errors import render_validation_error
    from pydantic import ValidationError as VE

    try:
        Backlog.model_validate({"items": [{"id": "bogus"}]})
    except VE as exc:
        err = render_validation_error("backlog.json", exc)
        assert "backlog.json" in str(err)
        assert "items[0].id" in str(err)
        assert isinstance(err, MissionCtrlError)


def test_next_id_monotonic() -> None:
    assert next_id("idea", 3, ["idea_001", "idea_002"]) == "idea_003"
    assert next_id("evt", 6, []) == "evt_000001"
    assert next_id("spec", 3, ["spec_007"]) == "spec_008"
