"""Shared constants for Pi hooks (single import, no cycles)."""

from mission_ctrl_core.models import Actor, SessionRef

HOOK_ACTOR = Actor(type="agent", name="mission-ctrl-hook")
HOOK_SESSION = SessionRef(id="ses_0001")
