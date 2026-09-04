"""Mission Ctrl Pi Extension Manifest and Hooks."""

from __future__ import annotations

from typing import Any, Callable

from .hooks import session_start_hook
from .skills import (
    intent_add_idea,
    intent_design_approve,
    intent_design_propose,
    intent_init,
    intent_next,
    intent_recap,
    intent_spec_create,
    intent_spec_status,
    intent_status,
    intent_triage,
)


def on_before_send_stub(message: str, context: Any = None) -> None:
    """Stub hook for before send interceptor, to be implemented in M3."""
    pass


MANIFEST: dict[str, Any] = {
    "name": "mission-ctrl",
    "version": "0.1.0",
    "description": "Intent layer extension for Pi coding agent",
    "hooks": {
        "on_session_start": session_start_hook,
        "on_before_send": on_before_send_stub,
    },
    "skills": {
        "intent:init": intent_init,
        "intent:add-idea": intent_add_idea,
        "intent:triage": intent_triage,
        "intent:spec-create": intent_spec_create,
        "intent:spec-status": intent_spec_status,
        "intent:next": intent_next,
        "intent:status": intent_status,
        # M2b: design-gate skills
        "intent:recap": intent_recap,
        "intent:design-propose": intent_design_propose,
        "intent:design-approve": intent_design_approve,
    },
}


class Extension:
    """Extension wrapper providing access to skills and hooks."""

    def __init__(self) -> None:
        self.manifest = MANIFEST
        self.skills: dict[str, Callable[..., Any]] = MANIFEST["skills"]
        self.hooks: dict[str, Callable[..., Any]] = MANIFEST["hooks"]

    def get_skill(self, name: str) -> Callable[..., Any] | None:
        return self.skills.get(name)
