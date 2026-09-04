from __future__ import annotations

from pathlib import Path

from mission_ctrl_core.logic.recap import RecapResult, generate_recap
from mission_ctrl_core.stores import IntentStore

from ..schemas import RecapInput
from .common import get_store, require_initialized


def intent_recap(
    input: RecapInput | None = None,
    store: IntentStore | None = None,
    root: Path | str = ".",
) -> RecapResult:
    """Return an on-demand recap of the current intent state.

    Accepts an optional verbosity override; if omitted, defaults to "standard".
    This is the user-invoked form. The session hook (M3) will call this with a
    verbosity tier derived from the session gap.
    """
    st = get_store(store, root)
    require_initialized(st)

    inp = input or RecapInput()
    verbosity = inp.verbosity or "standard"

    return generate_recap(
        st,
        verbosity=verbosity,
        since_iso=inp.since_iso,
        root=root if root != "." else None,
    )
