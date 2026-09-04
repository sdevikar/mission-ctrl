"""`on_before_send` hook: intercept implementation-intent messages before Pi acts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from mission_ctrl_core.models import Bucket, SpecStatus
from mission_ctrl_core.stores import IntentStore

from .hook_common import HOOK_ACTOR, HOOK_SESSION
from .session_start import _root_from_context, has_intent_dir

BeforeSendAction = Literal["proceed", "redirect", "bypass"]

# Hardcoded v1 implementation-intent list (design.md). Constants, not config:
# changed by editing source and shipping a new version.
IMPLEMENTATION_PATTERNS: tuple[str, ...] = (
    "implement",
    "add feature",
    "build",
    "code up",
    "write the",
    "create the",
)

# One-phrase override (design.md). Presence skips pattern matching entirely.
BYPASS_PHRASE = "override intent"

EXCERPT_LEN = 200


@dataclass(frozen=True)
class BeforeSendResult:
    action: BeforeSendAction
    target: str | None
    message: str
    pattern: str | None


def _compile(pattern: str) -> re.Pattern[str]:
    return re.compile(r"\b" + re.escape(pattern) + r"\b", re.IGNORECASE)


def find_implementation_intent(message: str) -> str | None:
    """First hardcoded pattern matching `message` (case-insensitive, full-word),
    or None. List order decides when several patterns match."""
    for pattern in IMPLEMENTATION_PATTERNS:
        if _compile(pattern).search(message):
            return pattern
    return None


def _redirect_target(store: IntentStore) -> tuple[str, str]:
    """Pick the redirect skill + human detail from current `.intent/` state."""
    approved = sorted(
        n.id for n in store.specs.read().nodes if n.status is SpecStatus.DESIGN_APPROVED
    )
    if approved:
        extra = f" (+{len(approved) - 1} more)" if len(approved) > 1 else ""
        return (
            "intent:spec-status",
            f"design-approved {approved[0]}{extra} is ready for in_progress",
        )
    untriaged = store.backlog.search(bucket=Bucket.UNTRIAGED)
    if untriaged:
        extra = f" (+{len(untriaged) - 1} more)" if len(untriaged) > 1 else ""
        first = untriaged[0].id
        return (
            "intent:triage",
            f"{len(untriaged)} untriaged idea(s), starting with {first}{extra}",
        )
    return ("intent:add-idea", "backlog has no untriaged ideas yet")


def on_before_send(
    message: str,
    root: Path | str = ".",
    *,
    store: IntentStore | None = None,
) -> BeforeSendResult:
    """Inspect an outgoing user message before Pi reasons about it.

    - No `.intent/` → `proceed` (no-op, no writes).
    - Bypass phrase present → `bypass` + `INTENT_BYPASS_USED` (surfaced, logged).
    - Implementation-intent pattern matched → `redirect` + `INTENT_INTERCEPTED`.
    - Otherwise → `proceed` (no event).
    """
    st = store if store is not None else IntentStore(root)
    if not message.strip() or not has_intent_dir(st.root):
        return BeforeSendResult(action="proceed", target=None, message="", pattern=None)

    excerpt = message.strip()[:EXCERPT_LEN]
    if BYPASS_PHRASE.lower() in message.lower():
        st.builder().intent_bypass_used(
            bypass_phrase=BYPASS_PHRASE,
            original_message_excerpt=excerpt,
            actor=HOOK_ACTOR,
            reasoning="Bypass phrase detected; proceeding without redirect.",
            session=HOOK_SESSION,
        )
        return BeforeSendResult(
            action="bypass",
            target=None,
            message=(
                "Bypass acknowledged (override intent) — proceeding without "
                "redirect. This bypass has been logged."
            ),
            pattern=None,
        )

    pattern = find_implementation_intent(message)
    if pattern is None:
        return BeforeSendResult(action="proceed", target=None, message="", pattern=None)

    target, detail = _redirect_target(st)
    st.builder().intent_intercepted(
        pattern_matched=pattern,
        redirect_target=target,
        original_message_excerpt=excerpt,
        actor=HOOK_ACTOR,
        reasoning=f"Implementation intent matched ({pattern}); redirecting.",
        session=HOOK_SESSION,
    )
    return BeforeSendResult(
        action="redirect",
        target=target,
        message=(
            f"Hold on — {pattern!r} looks like implementation intent. "
            f"Route through {target} first ({detail}). "
            "Say 'override intent' to proceed anyway."
        ),
        pattern=pattern,
    )


def before_send_hook(message: str, context: Any = None) -> BeforeSendResult:
    """Pi entry point for `on_before_send` (wired in the manifest)."""
    return on_before_send(message, root=_root_from_context(context))
