from __future__ import annotations

from pathlib import Path

from mission_ctrl_core.logic import suggest_next
from mission_ctrl_core.models import SpecStatus
from mission_ctrl_core.stores import IntentStore

from ..schemas import NextResult, SpecSummary, StatusResult
from .common import get_store, require_initialized


def intent_status(
    store: IntentStore | None = None,
    root: Path | str = ".",
) -> StatusResult:
    st = get_store(store, root)
    require_initialized(st)

    mission = st.mission.read()
    mvp = st.mvp.read()
    specs = st.specs.read()

    done_specs = {n.id for n in specs.nodes if n.status is SpecStatus.DONE}
    total_mvp = len(mvp.items)
    completed_mvp = 0
    for item in mvp.items:
        if item.linked_specs and all(s in done_specs for s in item.linked_specs):
            completed_mvp += 1
    mvp_pct = float(round(100.0 * completed_mvp / total_mvp, 1)) if total_mvp else 0.0

    active_specs = [
        SpecSummary(id=s.id, title=s.title, status=s.status.value)
        for s in specs.nodes
        if s.status is not SpecStatus.DONE
    ]

    suggestions = suggest_next(st)
    if suggestions:
        s = suggestions[0]
        next_sug = NextResult(
            spec_id=s.spec_id,
            title=s.title,
            reason=s.reason,
        )
    else:
        next_sug = NextResult(
            spec_id=None,
            title="No suggestions",
            reason="No actionable specs available",
        )

    return StatusResult(
        mission=mission.statement,
        mvp_completion_pct=mvp_pct,
        active_specs=active_specs,
        next_suggestion=next_sug,
    )
