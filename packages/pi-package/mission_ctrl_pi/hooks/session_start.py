"""`on_session_start` hook: auto-recap on session open for initialized projects."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from mission_ctrl_core.logic.recap import RecapResult
from mission_ctrl_core.stores import IntentStore
from mission_ctrl_core.stores.base import utcnow

from ..schemas import RecapInput
from ..skills import intent_recap

SessionTier = Literal["skip", "brief", "standard", "full"]

# Single source of truth for gap tiers (design.md §Session Gap Verbosity
# Tiers); tests import these constants rather than hardcoding thresholds.
SKIP_UNDER_HOURS = 1.0
BRIEF_UNDER_HOURS = 8.0
STANDARD_UNDER_HOURS = 48.0


def has_intent_dir(root: Path | str) -> bool:
    """True when `<root>/.intent/` exists and holds `mission.json`.

    This is the hook-side presence check (mirrors the skill-side
    `require_initialized` without raising): anything less than a full init
    marker counts as absent so hooks no-op gracefully on fresh projects.
    """
    intent_dir = Path(root) / IntentStore.INTENT_DIRNAME
    return intent_dir.is_dir() and (intent_dir / "mission.json").is_file()


def _as_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def last_session_time(store: IntentStore) -> datetime | None:
    """Timestamp of the last `SESSION_STARTED` event, else the last
    `INTENT_CREATED`, else None (no session history at all)."""
    events = store.meta.read_all()
    sessions = [e.timestamp for e in events if e.event_type == "SESSION_STARTED"]
    if sessions:
        return max(sessions)
    intents = [e.timestamp for e in events if e.event_type == "INTENT_CREATED"]
    if intents:
        return max(intents)
    return None


def select_tier(gap_hours: float) -> SessionTier:
    """Map a session gap to its verbosity tier (boundary-inclusive upward)."""
    if gap_hours < SKIP_UNDER_HOURS:
        return "skip"
    if gap_hours < BRIEF_UNDER_HOURS:
        return "brief"
    if gap_hours < STANDARD_UNDER_HOURS:
        return "standard"
    return "full"


def on_session_start(
    root: Path | str = ".",
    *,
    store: IntentStore | None = None,
    now: datetime | None = None,
) -> RecapResult | None:
    """Fire when Pi opens a workspace.

    Returns None (no-op, no writes) when `.intent/` is absent or the gap tier
    is `skip`; otherwise returns the recap at the tier-selected verbosity,
    windowed on the last session timestamp so standard/full tiers include
    "changes since". `SESSION_STARTED` logging extends this in task 4.
    """
    st = store if store is not None else IntentStore(root)
    if not has_intent_dir(st.root):
        return None

    current = _as_utc(now) if now is not None else utcnow()
    watermark = last_session_time(st)
    if watermark is None:
        return intent_recap(RecapInput(verbosity="full"), store=st, root=st.root)

    gap_hours = (current - _as_utc(watermark)).total_seconds() / 3600
    tier = select_tier(gap_hours)
    if tier == "skip":
        return None
    return intent_recap(
        RecapInput(
            verbosity=tier,
            since_iso=_as_utc(watermark).strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        store=st,
        root=st.root,
    )
