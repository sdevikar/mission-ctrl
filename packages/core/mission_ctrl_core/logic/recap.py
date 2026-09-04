from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..models import MetaEvent, SpecStatus
from .gitutil import Commit, commits_summary, git_commits_since
from .planner import Suggestion, suggest_next

Verbosity = Literal["brief", "standard", "full"]


class RecapEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    timestamp: str
    event_type: str
    reason: str


class RecapResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mission: str
    mvp_completed: int
    mvp_total: int
    mvp_percent: int
    last_focus: str | None
    last_focus_status: str | None
    changes: list[str] = Field(default_factory=list)
    recommendations: list[Suggestion] = Field(default_factory=list)
    git_commits: list[Commit] = Field(default_factory=list)
    events_since: list[RecapEvent] = Field(default_factory=list)
    rendered: str = ""
    verbosity: Verbosity = "standard"


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _mvp_percent(store) -> tuple[int, int, int]:
    mvp = store.mvp.read()
    done_specs = {n.id for n in store.specs.read().nodes if n.status is SpecStatus.DONE}
    total = len(mvp.items)
    completed = 0
    for item in mvp.items:
        if item.linked_specs and all(s in done_specs for s in item.linked_specs):
            completed += 1
    percent = round(100 * completed / total) if total else 0
    return completed, total, percent


def _events_since(store, since_dt: datetime) -> list[MetaEvent]:
    return [e for e in store.meta.read_all() if e.timestamp > since_dt]


def generate_recap(
    store,
    *,
    verbosity: Verbosity = "standard",
    since_iso: str | None = None,
    root=None,
    since_event: str | None = None,
) -> RecapResult:
    """Build a typed recap of current intent state.

    `since_iso` (UTC) bounds "what changed": meta events and git commits newer
    than it. When omitted, no change window is applied (everything counts).
    `root` is the repo root used for the read-only `git log` lookup.
    Git lookups are always read-only and never raise for a missing repo.
    """
    mission = store.mission.read()
    completed, total, percent = _mvp_percent(store)

    in_progress = [
        n for n in store.specs.read().nodes if n.status is SpecStatus.IN_PROGRESS
    ]
    last_focus = in_progress[0] if in_progress else None

    # Resolve the "changes since" timestamp.
    change_dt = None
    events_since: list[MetaEvent] = []
    if since_iso is not None:
        change_dt = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
        events_since = _events_since(store, change_dt)
    elif since_event is not None:
        prior = store.meta.read_since(since_event)
        if prior:
            # the last event *at or before* since_event is the watermark
            before = [e for e in store.meta.read_all() if e.event_id <= since_event]
            if before:
                change_dt = before[-1].timestamp
                events_since = store.meta.read_since(since_event)

    git_commits = []
    if root is not None and change_dt is not None:
        git_commits = git_commits_since(root, since_iso) if since_iso else []

    recommendations = suggest_next(store)
    rendered = _render(
        verbosity,
        mission.statement,
        percent,
        last_focus,
        events_since,
        git_commits,
        recommendations,
    )
    return RecapResult(
        mission=mission.statement,
        mvp_completed=completed,
        mvp_total=total,
        mvp_percent=percent,
        last_focus=last_focus.id if last_focus else None,
        last_focus_status=last_focus.status.value if last_focus else None,
        changes=commits_summary(git_commits),
        recommendations=recommendations,
        git_commits=git_commits,
        events_since=[
            RecapEvent(
                event_id=e.event_id,
                timestamp=_iso(e.timestamp),
                event_type=e.event_type,
                reason=e.reasoning,
            )
            for e in events_since
        ],
        rendered=rendered,
        verbosity=verbosity,
    )


def _render(
    verbosity,
    mission: str,
    percent: int,
    last_focus,
    events_since: list[MetaEvent],
    git_commits: list[Commit],
    recommendations: list[Suggestion],
) -> str:
    lines: list[str] = []
    lines.append(f"Mission: {mission}")
    lines.append(f"MVP: {percent}% complete")

    if verbosity == "brief":
        if last_focus:
            lines.append(f"Focus: {last_focus.id} ({last_focus.title})")
        if recommendations:
            top = recommendations[0]
            lines.append(f"Next: {top.spec_id} {top.title}")
        return "\n".join(lines)

    lines.append("")
    lines.append("## Focus")
    if last_focus:
        lines.append(
            f"- {last_focus.id} - {last_focus.title} [{last_focus.status.value}]"
        )
    else:
        lines.append("- none (no spec in progress)")

    lines.append("")
    lines.append("## Changes")
    if events_since:
        for e in events_since:
            lines.append(f"- {e.event_type}: {e.reasoning}")
    elif git_commits:
        for c in git_commits:
            lines.append(f"- {c.sha} {c.subject}")
    else:
        lines.append("- no changes since last session")

    lines.append("")
    lines.append("## Next up")
    if recommendations:
        limit = 3 if verbosity == "full" else 5
        for rec in recommendations[:limit]:
            lines.append(f"- {rec.spec_id} - {rec.title} ({rec.reason})")
    else:
        lines.append("- none available; triage the backlog or finish a spec")
    return "\n".join(lines)
