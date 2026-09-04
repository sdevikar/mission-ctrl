from __future__ import annotations

import shutil
from pathlib import Path

from mission_ctrl_core.models import (
    Actor,
    Alignment,
    Backlog,
    BacklogItem,
    BacklogLinks,
    Bucket,
    Constraint,
    Constraints,
    Mission,
    Mvp,
    MvpItem,
    SessionRef,
    SpecNode,
    Specs,
)
from mission_ctrl_core.stores import IntentStore

TS = "2026-03-10T10:15:00Z"
FIXTURES = Path(__file__).parent / "fixtures"


def _actor(human: bool = True) -> Actor:
    return Actor(type="human" if human else "agent", name="owner" if human else "agent")


def _session(n: int) -> SessionRef:
    return SessionRef(id=f"ses_{n:04d}")


def _mission() -> Mission:
    return Mission(
        id="mis_001",
        version="v1.0",
        statement="A deterministic export system for testing the intent layer.",
        success_criteria=["exports complete", "failures are visible"],
        created_at=TS,
        updated_at=TS,
    )


def _mvp(items: list[MvpItem]) -> Mvp:
    return Mvp(version="v1.0", items=items, created_at=TS, updated_at=TS)


def _constraints(items: list[Constraint]) -> Constraints:
    return Constraints(version="v1.0", constraints=items, created_at=TS, updated_at=TS)


def _item(
    id: str,
    title: str,
    bucket: Bucket,
    mission: str,
    mvp: str,
    cons: list[str] = (),
    specs: list[str] = (),
) -> BacklogItem:
    return BacklogItem(
        id=id,
        title=title,
        bucket=bucket,
        alignment=Alignment(mission=mission, mvp=mvp, constraints=list(cons)),
        links=BacklogLinks(specs=list(specs)),
        created_at=TS,
        updated_at=TS,
    )


def _node(
    id: str,
    title: str,
    status: str,
    deps: list[str] = (),
    ideas: list[str] = (),
    mvp: list[str] = (),
) -> SpecNode:
    from mission_ctrl_core.models import SpecLinks

    return SpecNode(
        id=id,
        title=title,
        status=status,
        depends_on=list(deps),
        links=SpecLinks(ideas=list(ideas), mvp_items=list(mvp)),
    )


def _init(root: Path) -> IntentStore:
    store = IntentStore(root)
    store.init(
        mission=_mission(),
        mvp=_mvp(
            [
                MvpItem(
                    id="mvp_001",
                    title="Async export execution",
                    linked_specs=["spec_001"],
                ),
                MvpItem(
                    id="mvp_002",
                    title="Export result retrieval",
                    linked_specs=["spec_002"],
                ),
            ]
        ),
        constraints=_constraints(
            [
                Constraint(
                    id="con_001",
                    rule="Keep it simple",
                    rationale="Less complexity, faster iteration",
                    severity="high",
                )
            ]
        ),
        actor=_actor(),
        session=_session(1),
        reasoning="Scaffold a valid intent space.",
    )
    return store


def build_empty_project(root: Path) -> None:
    _init(root)


def build_mid_flight(root: Path) -> None:
    store = _init(root)
    store.backlog.write(
        Backlog(
            items=[
                _item(
                    "idea_001",
                    "Show export progress bar",
                    Bucket.PARKED,
                    "weak",
                    "not_required",
                    cons=["con_001"],
                ),
                _item(
                    "idea_002",
                    "Async export queue",
                    Bucket.MVP_CRITICAL,
                    "strong",
                    "required",
                    specs=["spec_001"],
                ),
            ]
        )
    )
    store.specs.write(
        Specs(
            nodes=[
                _node(
                    "spec_001",
                    "Async export execution",
                    "in_progress",
                    ideas=["idea_002"],
                    mvp=["mvp_001"],
                ),
                _node(
                    "spec_002",
                    "Export download endpoint",
                    "draft",
                    deps=["spec_001"],
                    mvp=["mvp_002"],
                ),
            ]
        )
    )
    builder = store.builder()
    builder.spec_created(
        "spec_001",
        "Async export execution",
        actor=_actor(human=False),
        reasoning="Convert the MVP-critical idea into a tracked spec.",
        session=_session(2),
        links={"ideas": ["idea_002"], "mvp_items": ["mvp_001"]},
        depends_on=["evt_000001"],
    )
    builder.spec_status_updated(
        "spec_001",
        "draft",
        "in_progress",
        actor=_actor(human=False),
        reasoning="Start implementation.",
        session=_session(3),
        depends_on=["evt_000002"],
    )


def build_complex_graph(root: Path) -> None:
    store = _init(root)
    store.backlog.write(
        Backlog(
            items=[
                _item(
                    "idea_001",
                    "Foundation",
                    Bucket.MVP_CRITICAL,
                    "strong",
                    "required",
                    specs=["spec_001"],
                ),
                _item(
                    "idea_002",
                    "Left branch",
                    Bucket.MVP_CRITICAL,
                    "strong",
                    "required",
                    specs=["spec_002"],
                ),
                _item(
                    "idea_003",
                    "Right branch",
                    Bucket.MVP_CRITICAL,
                    "strong",
                    "required",
                    specs=["spec_003"],
                ),
                _item(
                    "idea_004", "Parked extra", Bucket.PARKED, "weak", "not_required"
                ),
            ]
        )
    )
    store.specs.write(
        Specs(
            nodes=[
                _node("spec_001", "Foundation", "done", ideas=["idea_001"]),
                _node(
                    "spec_002",
                    "Left branch",
                    "done",
                    deps=["spec_001"],
                    ideas=["idea_002"],
                ),
                _node(
                    "spec_003",
                    "Right branch",
                    "design_approved",
                    deps=["spec_001"],
                    ideas=["idea_003"],
                ),
                _node(
                    "spec_004",
                    "Blocked merge",
                    "blocked",
                    deps=["spec_002", "spec_005"],
                ),
                _node("spec_005", "Late dependency", "draft", deps=["spec_002"]),
            ]
        )
    )


def main() -> None:
    if FIXTURES.exists():
        shutil.rmtree(FIXTURES)
    FIXTURES.mkdir(parents=True)
    for name, fn in (
        ("empty-project", build_empty_project),
        ("mid-flight", build_mid_flight),
        ("complex-graph", build_complex_graph),
    ):
        root = FIXTURES / name
        root.mkdir()
        fn(root)
    for name in ("empty-project", "mid-flight", "complex-graph"):
        store = IntentStore(FIXTURES / name)
        errs = store.validate_all()
        assert not errs, f"{name}: {errs}"
        events = store.meta.read_all()
        print(f"{name}: ok, {len(events)} events")


if __name__ == "__main__":
    main()
