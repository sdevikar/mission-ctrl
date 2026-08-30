from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..models import SpecStatus

if TYPE_CHECKING:
    from ..stores import IntentStore


@dataclass(frozen=True)
class Suggestion:
    spec_id: str
    title: str
    reason: str
    mvp_linked: bool
    unresolved_deps: int
    continuous: bool


# Spec statuses that still represent work to do (not started or finished).
_ELIGIBLE = (SpecStatus.DRAFT, SpecStatus.DESIGN_PROPOSED, SpecStatus.DESIGN_APPROVED)


def _unresolved(node, done: set[str]) -> list[str]:
    return [d for d in node.depends_on if d not in done]


def _feature_area(node) -> set[str]:
    """Feature-area proxy for a spec: its deps + links (ideas/mvp), not its id."""
    return set(node.depends_on) | set(node.links.ideas) | set(node.links.mvp_items)


def suggest_next(store: "IntentStore", *, count: int = 5) -> list[Suggestion]:
    """Rank actionable specs and return the top `count`.

    Candidates are specs in `draft`, `design_proposed`, or `design_approved`
    whose `depends_on` are all `done`. Ordering: MVP-linked first, fewer
    unresolved deps first, current-focus continuity first, then stable by id.
    Blocked and in-progress/done specs are never returned.
    """
    nodes = store.specs.read().nodes
    done = {n.id for n in nodes if n.status is SpecStatus.DONE}
    focus = next((n for n in nodes if n.status is SpecStatus.IN_PROGRESS), None)
    focus_area = _feature_area(focus) if focus else set()

    ranked: list[Suggestion] = []
    for node in nodes:
        if node.status not in _ELIGIBLE:
            continue
        unresolved = _unresolved(node, done)
        if unresolved:  # blocked: a prerequisite is not done yet
            continue
        area = _feature_area(node)
        mvp_linked = bool(node.links.mvp_items)
        continuous = bool(focus_area & area)
        ranked.append(
            Suggestion(
                spec_id=node.id,
                title=node.title,
                reason=_reason(node, mvp_linked, continuous, focus, done),
                mvp_linked=mvp_linked,
                unresolved_deps=len(unresolved),
                continuous=continuous,
            )
        )

    ranked.sort(
        key=lambda s: (
            not s.mvp_linked,
            s.unresolved_deps,
            not s.continuous,
            s.spec_id,
        )
    )
    return ranked[:count]


def _reason(node, mvp_linked: bool, continuous: bool, focus, done: set[str]) -> str:
    bits: list[str] = []
    if mvp_linked:
        bits.append("MVP-linked")
    if continuous and focus is not None:
        bits.append(f"continues {focus.id}")
    if not node.depends_on:
        bits.append("no prerequisites")
    elif all(d in done for d in node.depends_on):
        bits.append("prerequisites done")
    if not bits:
        bits.append("unblocked")
    return "; ".join(bits)
