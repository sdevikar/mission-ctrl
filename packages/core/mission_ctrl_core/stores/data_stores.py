from __future__ import annotations

import json
from graphlib import CycleError, TopologicalSorter
from pathlib import Path

from pydantic import ValidationError

from ..errors import MissionCtrlError, render_validation_error
from ..models import (
    Backlog,
    BacklogItem,
    Bucket,
    Constraint,
    Constraints,
    ConstraintSeverity,
    MetaEvent,
    Mission,
    Mvp,
    Specs,
    SpecStatus,
)
from ..models.common import next_id
from .base import Store, utcnow

MISSION = "mission.json"
MVP = "mvp.json"
CONSTRAINTS = "constraints.json"
BACKLOG = "backlog.json"
SPECS = "specs.json"
META = "meta.jsonl"


class _SingleFileStore(Store):
    def next_id(self) -> str:  # pragma: no cover - interface marker
        raise NotImplementedError


class MissionStore(_SingleFileStore):
    FILENAME = MISSION
    MODEL = Mission


class MvpStore(_SingleFileStore):
    FILENAME = MVP
    MODEL = Mvp

    def next_id(self) -> str:
        return next_id("mvp", 3, [i.id for i in self.read().items])


class ConstraintsStore(_SingleFileStore):
    FILENAME = CONSTRAINTS
    MODEL = Constraints

    def next_id(self) -> str:
        return next_id("con", 3, [c.id for c in self.read().constraints])

    def add(
        self,
        rule: str,
        rationale: str,
        severity: ConstraintSeverity,
        scope: list[str] | None = None,
    ) -> Constraint:
        data = self.read()
        item = Constraint(
            id=self.next_id(),
            rule=rule,
            rationale=rationale,
            severity=severity,
            scope=list(scope or []),
        )
        data.constraints.append(item)
        data.updated_at = utcnow()
        self.write(data)
        return item

    def get(self, id: str) -> Constraint:
        for item in self.read().constraints:
            if item.id == id:
                return item
        raise KeyError(id)


class BacklogStore(_SingleFileStore):
    FILENAME = BACKLOG
    MODEL = Backlog

    def next_id(self) -> str:
        return next_id("idea", 3, [i.id for i in self.read().items])

    def add(
        self,
        title: str,
        description: str | None = None,
        bucket: Bucket = Bucket.UNTRIAGED,
    ) -> BacklogItem:
        from ..models import Alignment

        data = self.read()
        now = utcnow()
        item = BacklogItem(
            id=self.next_id(),
            title=title,
            description=description,
            bucket=bucket,
            alignment=Alignment(mission="neutral", mvp="not_required"),
            created_at=now,
            updated_at=now,
        )
        data.items.append(item)
        self.write(data)
        return item

    def get(self, id: str) -> BacklogItem:
        for item in self.read().items:
            if item.id == id:
                return item
        raise KeyError(id)

    def update(self, id: str, **fields: object) -> BacklogItem:
        data = self.read()
        for i, item in enumerate(data.items):
            if item.id == id:
                raw = item.model_dump(mode="json")
                raw.update(fields)
                raw["updated_at"] = utcnow().isoformat()
                updated = BacklogItem.model_validate(raw)
                data.items[i] = updated
                self.write(data)
                return updated
        raise KeyError(id)

    def search(
        self, *, text: str | None = None, bucket: Bucket | None = None
    ) -> list[BacklogItem]:
        results = []
        for item in self.read().items:
            if bucket is not None and item.bucket is not bucket:
                continue
            if text is not None and text.lower() not in item.title.lower():
                continue
            results.append(item)
        return results


class SpecStore(_SingleFileStore):
    FILENAME = SPECS
    MODEL = Specs

    def next_id(self) -> str:
        return next_id("spec", 3, [n.id for n in self.read().nodes])

    def get(self, id: str):
        for node in self.read().nodes:
            if node.id == id:
                return node
        raise KeyError(id)

    def add_node(self, node) -> None:
        data = self.read()
        known = {n.id for n in data.nodes}
        if node.id in known:
            raise MissionCtrlError(f"specs.json: {node.id}: duplicated spec id")
        unknown = [d for d in node.depends_on if d not in known]
        if unknown:
            raise MissionCtrlError(
                f"specs.json: {node.id}.depends_on: unknown spec {', '.join(unknown)}"
            )
        if node.status is SpecStatus.IN_PROGRESS:
            self._require_done_deps(node, data)
        data.nodes.append(node)
        data.updated_at = utcnow()
        self.write(data)

    def update_node(self, id: str, **fields: object) -> None:
        from ..models import SpecNode

        data = self.read()
        for i, node in enumerate(data.nodes):
            if node.id == id:
                raw = node.model_dump(mode="json")
                raw.update(fields)
                data.nodes[i] = SpecNode.model_validate(raw)
                data.updated_at = utcnow()
                self.write(data)
                return
        raise KeyError(id)

    def set_status(self, id: str, to: str) -> None:
        data = self.read()
        node = next((n for n in data.nodes if n.id == id), None)
        if node is None:
            raise KeyError(id)
        target = SpecStatus(to)
        if target is SpecStatus.IN_PROGRESS:
            self._require_done_deps(node, data)
        node.status = target
        data.updated_at = utcnow()
        self.write(data)

    def _require_done_deps(self, node, data) -> None:
        done = {n.id for n in data.nodes if n.status is SpecStatus.DONE}
        unfinished = [d for d in node.depends_on if d not in done]
        if unfinished:
            raise MissionCtrlError(
                f"specs.json: {node.id}: cannot be in_progress, "
                f"unfinished deps: {', '.join(unfinished)}"
            )

    def validate_no_cycles(self) -> None:
        data = self.read()
        known = {n.id for n in data.nodes}
        missing = sorted(
            {d for n in data.nodes for d in n.depends_on if d not in known}
        )
        if missing:
            raise MissionCtrlError(
                f"specs.json: unknown depends_on targets: {', '.join(missing)}"
            )
        graph = {n.id: [d for d in n.depends_on if d in known] for n in data.nodes}
        sorter = TopologicalSorter(graph)
        try:
            sorter.prepare()
        except CycleError as exc:
            cycle = exc.args[1] if len(exc.args) > 1 else ()
            cycle = " -> ".join(cycle) if cycle else "detected"
            raise MissionCtrlError(f"specs.json: dependency cycle: {cycle}") from exc


class MetaStore:
    """Append-only JSONL event log (one JSON object per line, no array)."""

    FILENAME = META

    def __init__(self, intent_dir: Path | str) -> None:
        self.dir = Path(intent_dir)
        self.path = self.dir / self.FILENAME

    def append(self, event: MetaEvent) -> MetaEvent:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(event.model_dump_json() + "\n")
        return event

    def read_all(self) -> list[MetaEvent]:
        return self._read(0)

    def read_since(self, event_id: str | None = None) -> list[MetaEvent]:
        return self._read(_event_num(event_id) if event_id else 0)

    def _read(self, after: int) -> list[MetaEvent]:
        from ..models import MetaEventAdapter

        if not self.path.exists():
            return []
        events = []
        for lineno, line in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                event = MetaEventAdapter.validate_json(line)
            except ValidationError as exc:
                raise render_validation_error(f"{self.FILENAME}:{lineno}", exc) from exc
            if _event_num(event.event_id) > after:
                events.append(event)
        return events

    def next_id(self) -> str:
        num = 0
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    tail = json.loads(line)["event_id"].rsplit("_", 1)[-1]
                except (json.JSONDecodeError, KeyError, AttributeError):
                    continue
                if tail.isdigit():
                    num = max(num, int(tail))
        return f"evt_{num + 1:06d}"


def _event_num(event_id: str) -> int:
    tail = event_id.rsplit("_", 1)[-1]
    if not tail.isdigit():
        raise MissionCtrlError(f"meta.jsonl: invalid event id {event_id}")
    return int(tail)
