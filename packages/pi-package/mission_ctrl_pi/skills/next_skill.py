from __future__ import annotations

from pathlib import Path

from mission_ctrl_core.logic import suggest_next
from mission_ctrl_core.stores import IntentStore

from ..schemas import NextResult
from .common import get_store, require_initialized


def intent_next(
    store: IntentStore | None = None,
    root: Path | str = ".",
) -> NextResult:
    st = get_store(store, root)
    require_initialized(st)

    suggestions = suggest_next(st)
    if suggestions:
        s = suggestions[0]
        return NextResult(
            spec_id=s.spec_id,
            title=s.title,
            reason=s.reason,
        )
    return NextResult(
        spec_id=None,
        title="No suggestions",
        reason="No actionable specs available",
    )
