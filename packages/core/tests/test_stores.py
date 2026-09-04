from __future__ import annotations

from pathlib import Path

import pytest
from mission_ctrl_core.errors import MissionCtrlError
from mission_ctrl_core.models import (
    Actor,
    Backlog,
    Bucket,
    Constraint,
    Constraints,
    ConstraintSeverity,
    EntityRef,
    IntentCreatedEvent,
    LinkedIntent,
    MetaEventAdapter,
    Mission,
    Mvp,
    MvpItem,
    SessionRef,
    SpecLinks,
    SpecNode,
    Specs,
    SpecStatus,
)
from mission_ctrl_core.stores import (
    BacklogStore,
    ConstraintsStore,
    EventBuilder,
    IntentStore,
    MetaStore,
    MissionStore,
    MvpStore,
    SpecStore,
)

TS = "2026-03-10T10:15:00Z"


def make_mission() -> Mission:
    return Mission(
        id="mis_001",
        version="v1.0",
        statement="A mission.",
        success_criteria=["a"],
        created_at=TS,
        updated_at=TS,
    )


def make_mvp() -> Mvp:
    return Mvp(
        version="v1.0",
        items=[MvpItem(id="mvp_001", title="one")],
        created_at=TS,
        updated_at=TS,
    )


def make_constraints() -> Constraints:
    return Constraints(
        version="v1.0",
        constraints=[
            Constraint(id="con_001", rule="r", rationale="why", severity="high")
        ],
        created_at=TS,
        updated_at=TS,
    )


def _actor() -> Actor:
    return Actor(type="agent", name="test")


def _session() -> SessionRef:
    return SessionRef(id="ses_0001")


def _linked() -> LinkedIntent:
    return LinkedIntent(
        mission_id="mis_001", mvp_version="v1.0", constraints_version="v1.0"
    )


def _intent_event(event_id: str) -> IntentCreatedEvent:
    return IntentCreatedEvent(
        event_id=event_id,
        timestamp=TS,
        event_type="INTENT_CREATED",
        actor=_actor(),
        affected_entities=[EntityRef(type="mission", id="mis_001")],
        linked_intent=_linked(),
        decision={
            "mission_version": "v1.0",
            "mvp_version": "v1.0",
            "constraints_version": "v1.0",
        },
        reasoning="r",
        session=_session(),
    )


@pytest.fixture
def intent_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".intent"
    d.mkdir()
    return d


def test_mission_store_roundtrip_missing_and_malformed(intent_dir):
    store = MissionStore(intent_dir)
    before = make_mission()
    store.write(before)
    assert store.read() == before
    assert (intent_dir / "mission.json").exists()

    empty = intent_dir.parent / "empty-dir"
    empty.mkdir()
    with pytest.raises(FileNotFoundError):
        MissionStore(empty).read()

    (intent_dir / "mission.json").write_text(
        '{"id": "BOGL", "version": "v1", "statement": "s", "success_criteria": []}',
        encoding="utf-8",
    )
    with pytest.raises(MissionCtrlError, match=r"mission\.json: id: "):
        store.read()


def test_mvp_store_next_id_and_roundtrip(intent_dir):
    store = MvpStore(intent_dir)
    store.write(make_mvp())
    assert store.next_id() == "mvp_002"
    big = Mvp(
        version="v1.0",
        items=[
            MvpItem(id="mvp_001", title="one"),
            MvpItem(id="mvp_007", title="seven"),
        ],
        created_at=TS,
        updated_at=TS,
    )
    store.write(big)
    assert store.read().items[1].id == "mvp_007"
    assert store.next_id() == "mvp_008"


def test_constraints_store_add_and_get(intent_dir):
    store = ConstraintsStore(intent_dir)
    store.write(make_constraints())
    assert store.next_id() == "con_002"
    new_rule = store.add("rule t", "rational", ConstraintSeverity.LOW, scope=["x"])
    assert new_rule.id == "con_002"
    assert new_rule.scope == ["x"]
    assert store.get("con_001").rule == "r"
    assert [c.id for c in store.read().constraints] == ["con_001", "con_002"]
    with pytest.raises(KeyError):
        store.get("con_999")


def test_backlog_store_ops(intent_dir):
    store = BacklogStore(intent_dir)
    store.write(Backlog(items=[]))
    a = store.add("Export progress bar")
    b = store.add("Async export queue")
    assert (a.id, b.id) == ("idea_001", "idea_002")
    assert a.bucket is Bucket.UNTRIAGED
    assert store.get("idea_001").title == "Export progress bar"
    triaged = store.update("idea_002", bucket="mvp_critical")
    assert triaged.bucket is Bucket.MVP_CRITICAL
    assert store.read().items[1].bucket is Bucket.MVP_CRITICAL
    assert [s.id for s in store.search(bucket=Bucket.MVP_CRITICAL)] == ["idea_002"]
    assert [s.id for s in store.search(text="progress")] == ["idea_001"]
    with pytest.raises(KeyError):
        store.get("idea_009")
    with pytest.raises(KeyError):
        store.update("idea_009", bucket="parked")


def test_backlog_store_search_no_match(intent_dir):
    store = BacklogStore(intent_dir)
    store.write(Backlog(items=[]))
    store.add("Something")
    assert store.search(text="zzz-nope") == []
    assert store.search(bucket=Bucket.PARKED) == []


def test_spec_store_add_update_get_next_id(intent_dir):
    store = SpecStore(intent_dir)
    store.write(Specs(nodes=[]))
    assert store.next_id() == "spec_001"
    store.add_node(SpecNode(id="spec_001", title="One"))
    store.add_node(
        SpecNode(
            id="spec_002",
            title="Two",
            depends_on=["spec_001"],
            links=SpecLinks(mvp_items=["mvp_001"]),
        )
    )
    node = store.get("spec_002")
    assert node.depends_on == ["spec_001"]
    assert node.links.mvp_items == ["mvp_001"]
    store.update_node("spec_002", title="Two!")
    assert store.get("spec_002").title == "Two!"
    assert store.next_id() == "spec_003"
    with pytest.raises(KeyError):
        store.get("spec_009")
    with pytest.raises(KeyError):
        store.update_node("spec_009", title="nope")
    with pytest.raises(MissionCtrlError, match="duplicated spec id"):
        store.add_node(SpecNode(id="spec_001", title="dup"))


def test_spec_store_add_missing_dep_rejected(intent_dir):
    store = SpecStore(intent_dir)
    store.write(Specs(nodes=[]))
    with pytest.raises(MissionCtrlError, match="unknown spec spec_999"):
        store.add_node(SpecNode(id="spec_001", title="A", depends_on=["spec_999"]))


def test_spec_store_cycle_detection(intent_dir):
    store = SpecStore(intent_dir)
    store.write(
        Specs(
            nodes=[
                SpecNode(id="spec_001", title="A"),
                SpecNode(id="spec_002", title="B"),
            ]
        )
    )
    store.validate_no_cycles()
    store.update_node("spec_001", depends_on=["spec_002"])
    store.update_node("spec_002", depends_on=["spec_001"])
    with pytest.raises(MissionCtrlError, match="dependency cycle"):
        store.validate_no_cycles()


def test_spec_store_unknown_dep_in_validation(intent_dir):
    store = SpecStore(intent_dir)
    store.write(
        Specs(nodes=[SpecNode(id="spec_001", title="A", depends_on=["spec_777"])])
    )
    with pytest.raises(MissionCtrlError, match="unknown depends_on targets"):
        store.validate_no_cycles()


def test_spec_store_in_progress_gating(intent_dir):
    store = SpecStore(intent_dir)
    store.write(
        Specs(
            nodes=[
                SpecNode(id="spec_001", title="A"),
                SpecNode(id="spec_002", title="B", depends_on=["spec_001"]),
            ]
        )
    )
    with pytest.raises(MissionCtrlError, match="cannot be in_progress"):
        store.set_status("spec_002", "in_progress")
    with pytest.raises(MissionCtrlError, match="cannot be in_progress"):
        store.add_node(
            SpecNode(
                id="spec_003",
                title="C",
                status=SpecStatus.IN_PROGRESS,
                depends_on=["spec_001"],
            )
        )
    store.set_status("spec_001", "done")
    store.set_status("spec_002", "in_progress")
    assert store.get("spec_002").status is SpecStatus.IN_PROGRESS
    with pytest.raises(KeyError):
        store.set_status("spec_009", "done")


def test_meta_store_append_sequential_ids(intent_dir):
    store = MetaStore(intent_dir)
    assert store.next_id() == "evt_000001"
    for _ in range(3):
        store.append(_intent_event(store.next_id()))
    assert store.next_id() == "evt_000004"
    events = store.read_all()
    assert [e.event_id for e in events] == ["evt_000001", "evt_000002", "evt_000003"]
    lines = (intent_dir / "meta.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("{")
    assert lines[0].endswith("}")


def test_meta_store_read_since(intent_dir):
    store = MetaStore(intent_dir)
    for _ in range(3):
        store.append(_intent_event(store.next_id()))
    since_1 = store.read_since("evt_000001")
    assert [e.event_id for e in since_1] == ["evt_000002", "evt_000003"]
    assert store.read_since(None) == store.read_all()
    with pytest.raises(MissionCtrlError, match="invalid event id"):
        store.read_since("evt_bogus")


def test_meta_store_malformed_line_errors(intent_dir):
    store = MetaStore(intent_dir)
    store.append(
        IntentCreatedEvent(
            event_id="evt_000001",
            timestamp=TS,
            event_type="INTENT_CREATED",
            actor=_actor(),
            affected_entities=[EntityRef(type="mission", id="mis_001")],
            linked_intent=_linked(),
            decision={
                "mission_version": "v1.0",
                "mvp_version": "v1.0",
                "constraints_version": "v1.0",
            },
            reasoning="r",
            session=_session(),
        )
    )
    with (intent_dir / "meta.jsonl").open("a", encoding="utf-8") as fh:
        fh.write('{"event_id": "evt_000002", "timestamp": "2026')
    with pytest.raises(MissionCtrlError, match=r"meta\.jsonl:2"):
        store.read_all()


def test_event_builder_spec_events(intent_dir):
    builder = EventBuilder(MetaStore(intent_dir), _linked())
    created = builder.spec_created(
        "spec_001",
        "Async export",
        actor=_actor(),
        reasoning="make it real",
        session=_session(),
        links={"ideas": ["idea_002"]},
    )
    assert created.event_type == "SPEC_CREATED"
    assert created.event_id == "evt_000001"
    assert created.decision.status == "draft"
    assert created.decision.links == {"ideas": ["idea_002"]}
    updated = builder.spec_status_updated(
        "spec_001",
        "draft",
        "design_proposed",
        actor=_actor(),
        reasoning="design gate",
        session=_session(),
    )
    assert updated.event_id == "evt_000002"
    assert updated.decision.from_status == "draft"
    assert updated.decision.to == "design_proposed"
    lines = (intent_dir / "meta.jsonl").read_text(encoding="utf-8").splitlines()
    event = MetaEventAdapter.validate_json(lines[-1])
    assert event.event_type == "SPEC_STATUS_UPDATED"


def test_event_builder_session_started(intent_dir):
    builder = EventBuilder(MetaStore(intent_dir), _linked())
    event = builder.session_started(
        gap_hours=10.5,
        verbosity="standard",
        actor=_actor(),
        reasoning="session opened",
        session=_session(),
    )
    assert event.event_type == "SESSION_STARTED"
    assert event.event_id == "evt_000001"
    assert event.decision.gap_hours == 10.5
    assert event.decision.verbosity == "standard"
    lines = (intent_dir / "meta.jsonl").read_text(encoding="utf-8").splitlines()
    assert MetaEventAdapter.validate_json(lines[-1]).event_type == "SESSION_STARTED"


def test_event_builder_unknown_type_rejected(intent_dir):
    builder = EventBuilder(MetaStore(intent_dir), _linked())
    with pytest.raises(MissionCtrlError, match="unknown event type NOPE"):
        builder.build(
            "NOPE",
            {},
            actor=_actor(),
            reasoning="r",
            affected_entities=[],
            session=_session(),
        )


def _init_store(intent_dir: Path) -> IntentStore:
    store = IntentStore(intent_dir.parent)
    store.init(
        mission=make_mission(),
        mvp=make_mvp(),
        constraints=make_constraints(),
        actor=_actor(),
        session=_session(),
    )
    return store


def test_intent_store_init_creates_all_files(intent_dir):
    store = _init_store(intent_dir)
    for name in (
        "mission.json",
        "mvp.json",
        "constraints.json",
        "backlog.json",
        "specs.json",
        "meta.jsonl",
    ):
        assert (intent_dir / name).exists(), name
    events = store.meta.read_all()
    assert len(events) == 1
    assert events[0].event_type == "INTENT_CREATED"
    assert store.validate_all() == []
    with pytest.raises(MissionCtrlError, match="already initialized"):
        store.init(
            mission=make_mission(),
            mvp=make_mvp(),
            constraints=make_constraints(),
            actor=_actor(),
            session=_session(),
        )


def test_intent_store_get_current_intent_empty(intent_dir):
    store = _init_store(intent_dir)
    got = store.get_current_intent()
    assert got.mission == "A mission."
    assert got.mvp_version == "v1.0"
    assert got.constraints_version == "v1.0"
    assert got.spec_count == 0
    assert got.current_spec is None
    assert got.next_specs == []


def test_intent_store_current_spec_and_next_up(intent_dir):
    store = _init_store(intent_dir)
    s = store.specs
    s.add_node(SpecNode(id="spec_001", title="A", status=SpecStatus.DONE))
    s.add_node(SpecNode(id="spec_004", title="D", status=SpecStatus.IN_PROGRESS))
    s.add_node(
        SpecNode(
            id="spec_002",
            title="B",
            status=SpecStatus.DESIGN_APPROVED,
            depends_on=["spec_001"],
        )
    )
    s.add_node(
        SpecNode(
            id="spec_003",
            title="C",
            status=SpecStatus.DESIGN_APPROVED,
            depends_on=["spec_004"],
        )
    )
    got = store.get_current_intent()
    assert got.current_spec == "spec_004"
    assert got.next_specs == ["spec_002"]
    assert got.spec_count == 4


def test_validate_all_detects_corrupt_file_and_dupes(intent_dir):
    store = _init_store(intent_dir)
    with (intent_dir / "backlog.json").open("w", encoding="utf-8") as fh:
        fh.write('{"items": [not-json')
    errs = store.validate_all()
    assert any("backlog.json" in e for e in errs)
    with (intent_dir / "backlog.json").open("w", encoding="utf-8") as fh:
        fh.write('{"items": []}')
    assert store.validate_all() == []
    store.meta.append(
        IntentCreatedEvent(
            event_id="evt_000001",
            timestamp=TS,
            event_type="INTENT_CREATED",
            actor=_actor(),
            affected_entities=[EntityRef(type="mission", id="mis_001")],
            linked_intent=_linked(),
            decision={
                "mission_version": "v1.0",
                "mvp_version": "v1.0",
                "constraints_version": "v1.0",
            },
            reasoning="dup",
            session=_session(),
        )
    )
    errs = store.validate_all()
    assert any("duplicate event ids: evt_000001" in e for e in errs)


def test_validate_all_detects_cycle(intent_dir):
    store = _init_store(intent_dir)
    s = store.specs
    s.add_node(SpecNode(id="spec_001", title="A"))
    s.add_node(SpecNode(id="spec_002", title="B"))
    s.update_node("spec_001", depends_on=["spec_002"])
    s.update_node("spec_002", depends_on=["spec_001"])
    errs = store.validate_all()
    assert any("dependency cycle" in e for e in errs)
