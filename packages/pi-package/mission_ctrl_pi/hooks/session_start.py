"""`on_session_start` hook: auto-recap on session open for initialized projects."""

from __future__ import annotations

from pathlib import Path

from mission_ctrl_core.logic.recap import RecapResult
from mission_ctrl_core.stores import IntentStore

from ..skills import intent_recap


def has_intent_dir(root: Path | str) -> bool:
    """True when `<root>/.intent/` exists and holds `mission.json`.

    This is the hook-side presence check (mirrors the skill-side
    `require_initialized` without raising): anything less than a full init
    marker counts as absent so hooks no-op gracefully on fresh projects.
    """
    intent_dir = Path(root) / IntentStore.INTENT_DIRNAME
    return intent_dir.is_dir() and (intent_dir / "mission.json").is_file()


def on_session_start(
    root: Path | str = ".",
    *,
    store: IntentStore | None = None,
) -> RecapResult | None:
    """Fire when Pi opens a workspace. Returns None (no-op, no writes) when
    `.intent/` is absent; otherwise returns the session recap.

    Session-gap tiers (task 2) and `SESSION_STARTED` logging (task 4) extend
    the present-path; the absent-path contract here is final.
    """
    st = store if store is not None else IntentStore(root)
    if not has_intent_dir(st.root):
        return None
    return intent_recap(store=st)
