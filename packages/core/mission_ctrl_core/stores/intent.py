from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..errors import MissionCtrlError
from ..models import (
    Actor,
    Constraints,
    LinkedIntent,
    Mission,
    Mvp,
    SessionRef,
)
from .data_stores import (
    BACKLOG,
    CONSTRAINTS,
    META,
    MISSION,
    MVP,
    SPECS,
    Backlog,
    BacklogStore,
    ConstraintsStore,
    MetaStore,
    MissionStore,
    MvpStore,
    SpecStore,
)
from .events import EventBuilder


def _empty_backlog() -> Backlog:
    return Backlog(items=[])


def _empty_specs():
    from ..models import Specs

    return Specs(nodes=[])


@dataclass
class CurrentIntent:
    mission: str
    mvp_version: str
    constraints_version: str
    spec_count: int
    current_spec: str | None = None
    next_specs: list[str] = field(default_factory=list)


class IntentStore:
    """Orchestrator over the per-file stores rooted at `<root>/.intent/`."""

    INTENT_DIRNAME = ".intent"

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.intent_dir = self.root / self.INTENT_DIRNAME
        self.mission = MissionStore(self.intent_dir)
        self.mvp = MvpStore(self.intent_dir)
        self.constraints = ConstraintsStore(self.intent_dir)
        self.backlog = BacklogStore(self.intent_dir)
        self.specs = SpecStore(self.intent_dir)
        self.meta = MetaStore(self.intent_dir)

    def init(
        self,
        *,
        mission: Mission,
        mvp: Mvp,
        constraints: Constraints,
        actor: Actor,
        session: SessionRef,
        reasoning: str = "Initialize project intent.",
    ) -> None:
        if self.intent_dir.exists() and any(self.intent_dir.iterdir()):
            raise MissionCtrlError(f"{self.INTENT_DIRNAME}: already initialized")
        self.intent_dir.mkdir(parents=True, exist_ok=True)
        self.mission.write(mission)
        self.mvp.write(mvp)
        self.constraints.write(constraints)
        self.backlog.write(_empty_backlog())
        self.specs.write(_empty_specs())
        self.builder().build(
            "INTENT_CREATED",
            {
                "mission_version": mission.version,
                "mvp_version": mvp.version,
                "constraints_version": constraints.version,
            },
            actor=actor,
            reasoning=reasoning,
            affected_entities=[
                {"type": "mission", "id": mission.id},
                {"type": "mvp", "id": mvp.version},
                {"type": "constraints", "id": constraints.version},
            ],
            session=session,
        )

    def builder(self) -> EventBuilder:
        mission = self.mission.read()
        mvp = self.mvp.read()
        constraints = self.constraints.read()
        return EventBuilder(
            self.meta,
            LinkedIntent(
                mission_id=mission.id,
                mvp_version=mvp.version,
                constraints_version=constraints.version,
            ),
        )

    def get_current_intent(self) -> CurrentIntent:
        from ..models import SpecStatus

        mission = self.mission.read()
        mvp = self.mvp.read()
        constraints = self.constraints.read()
        nodes = self.specs.read().nodes

        current: str | None = None
        next_specs: list[str] = []
        done = {n.id for n in nodes if n.status is SpecStatus.DONE}
        for node in nodes:
            if node.status is SpecStatus.IN_PROGRESS and current is None:
                current = node.id
            if node.status is SpecStatus.DESIGN_APPROVED and all(
                d in done for d in node.depends_on
            ):
                next_specs.append(node.id)
        return CurrentIntent(
            mission=mission.statement,
            mvp_version=mvp.version,
            constraints_version=constraints.version,
            spec_count=len(nodes),
            current_spec=current,
            next_specs=next_specs,
        )

    def validate_all(self) -> list[str]:
        errors: list[str] = []
        for store, fname in (
            (self.mission, MISSION),
            (self.mvp, MVP),
            (self.constraints, CONSTRAINTS),
            (self.backlog, BACKLOG),
            (self.specs, SPECS),
        ):
            try:
                store.read()
            except MissionCtrlError as exc:
                errors.append(str(exc))
        try:
            self.specs.validate_no_cycles()
        except MissionCtrlError as exc:
            errors.append(str(exc))
        try:
            events = self.meta.read_all()
        except MissionCtrlError as exc:
            errors.append(str(exc))
            events = []
        seen: dict[str, int] = {}
        for event in events:
            seen[event.event_id] = seen.get(event.event_id, 0) + 1
        dupes = [k for k, v in seen.items() if v > 1]
        if dupes:
            errors.append(f"{META}: duplicate event ids: {', '.join(dupes)}")
        return errors
