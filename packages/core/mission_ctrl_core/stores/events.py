from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models import (
    Actor,
    BacklogAddedEvent,
    BacklogTriageEvent,
    DesignApprovedEvent,
    DesignProposedEvent,
    EntityRef,
    IntentBypassUsedEvent,
    IntentCreatedEvent,
    IntentInterceptedEvent,
    LinkedIntent,
    MetaEvent,
    SessionRef,
    SessionStartedEvent,
    SpecCreatedEvent,
    SpecStatusUpdatedEvent,
)
from .data_stores import MetaStore

_EVENT_CLASSES: dict[str, type] = {
    "INTENT_CREATED": IntentCreatedEvent,
    "BACKLOG_ADDED": BacklogAddedEvent,
    "BACKLOG_TRIAGE": BacklogTriageEvent,
    "SPEC_CREATED": SpecCreatedEvent,
    "SPEC_STATUS_UPDATED": SpecStatusUpdatedEvent,
    "DESIGN_PROPOSED": DesignProposedEvent,
    "DESIGN_APPROVED": DesignApprovedEvent,
    "SESSION_STARTED": SessionStartedEvent,
    "INTENT_INTERCEPTED": IntentInterceptedEvent,
    "INTENT_BYPASS_USED": IntentBypassUsedEvent,
}


class EventBuilder:
    """Builds and appends v1 meta events with consistent common fields."""

    def __init__(self, meta: MetaStore, linked_intent: LinkedIntent) -> None:
        self.meta = meta
        self.linked_intent = linked_intent

    def build(
        self,
        event_type: str,
        decision: Any,
        *,
        actor: Actor,
        reasoning: str,
        affected_entities: list[EntityRef],
        session: SessionRef,
        event_id: str | None = None,
        timestamp: datetime | None = None,
        depends_on: list[str] | None = None,
        git_refs: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> MetaEvent:
        event_cls = _EVENT_CLASSES.get(event_type)
        if event_cls is None:
            from ..errors import MissionCtrlError

            raise MissionCtrlError(f"meta.jsonl: unknown event type {event_type}")
        from .base import utcnow

        kwargs: dict[str, Any] = {
            "event_type": event_type,
            "event_id": event_id or self.meta.next_id(),
            "timestamp": timestamp or utcnow(),
            "actor": actor,
            "affected_entities": affected_entities,
            "linked_intent": self.linked_intent,
            "decision": decision,
            "reasoning": reasoning,
            "session": session,
        }
        if depends_on is not None:
            kwargs["depends_on"] = depends_on
        if git_refs is not None:
            kwargs["git_refs"] = git_refs
        if tags is not None:
            kwargs["tags"] = tags
        event = event_cls(**kwargs)
        self.meta.append(event)
        return event

    def spec_created(
        self,
        spec_id: str,
        spec_title: str,
        *,
        actor: Actor,
        reasoning: str,
        session: SessionRef,
        links: dict[str, list[str]] | None = None,
        **common: Any,
    ) -> MetaEvent:
        from ..models import SpecCreatedDecision

        return self.build(
            "SPEC_CREATED",
            SpecCreatedDecision(
                spec_title=spec_title,
                status="draft",
                links=links or {},
            ),
            actor=actor,
            reasoning=reasoning,
            affected_entities=[EntityRef(type="spec", id=spec_id)],
            session=session,
            **common,
        )

    def spec_status_updated(
        self,
        spec_id: str,
        from_status: str,
        to_status: str,
        *,
        actor: Actor,
        reasoning: str,
        session: SessionRef,
        **common: Any,
    ) -> MetaEvent:
        from ..models import SpecStatusUpdatedDecision

        return self.build(
            "SPEC_STATUS_UPDATED",
            SpecStatusUpdatedDecision(from_status=from_status, to=to_status),
            actor=actor,
            reasoning=reasoning,
            affected_entities=[EntityRef(type="spec", id=spec_id)],
            session=session,
            **common,
        )

    def design_proposed(
        self,
        spec_id: str,
        digest: str,
        *,
        actor: Actor,
        reasoning: str,
        session: SessionRef,
        **common: Any,
    ) -> MetaEvent:
        from ..models import DesignProposedDecision

        return self.build(
            "DESIGN_PROPOSED",
            DesignProposedDecision(
                digest_id=digest[:64],  # store first 64 chars as digest_id summary
                key_choices=[],
                risks=[],
                open_questions=[],
            ),
            actor=actor,
            reasoning=reasoning,
            affected_entities=[EntityRef(type="spec", id=spec_id)],
            session=session,
            **common,
        )

    def session_started(
        self,
        *,
        gap_hours: float,
        verbosity: str,
        actor: Actor,
        reasoning: str,
        session: SessionRef,
        **common: Any,
    ) -> MetaEvent:
        from ..models import SessionStartedDecision

        return self.build(
            "SESSION_STARTED",
            SessionStartedDecision(
                gap_hours=gap_hours,
                verbosity=verbosity,
            ),
            actor=actor,
            reasoning=reasoning,
            affected_entities=[],
            session=session,
            **common,
        )

    def design_approved(
        self,
        spec_id: str,
        *,
        approval: bool,
        notes: str | None,
        actor: Actor,
        reasoning: str,
        session: SessionRef,
        **common: Any,
    ) -> MetaEvent:
        from ..models import DesignApprovedDecision

        return self.build(
            "DESIGN_APPROVED",
            DesignApprovedDecision(
                digest_id="",
                approval=approval,
                notes=notes,
            ),
            actor=actor,
            reasoning=reasoning,
            affected_entities=[EntityRef(type="spec", id=spec_id)],
            session=session,
            **common,
        )

    def intent_intercepted(
        self,
        *,
        pattern_matched: str,
        redirect_target: str,
        original_message_excerpt: str,
        actor: Actor,
        reasoning: str,
        session: SessionRef,
        **common: Any,
    ) -> MetaEvent:
        from ..models import IntentInterceptedDecision

        return self.build(
            "INTENT_INTERCEPTED",
            IntentInterceptedDecision(
                pattern_matched=pattern_matched,
                redirect_target=redirect_target,
                original_message_excerpt=original_message_excerpt,
            ),
            actor=actor,
            reasoning=reasoning,
            affected_entities=[],
            session=session,
            **common,
        )

    def intent_bypass_used(
        self,
        *,
        bypass_phrase: str,
        original_message_excerpt: str,
        actor: Actor,
        reasoning: str,
        session: SessionRef,
        **common: Any,
    ) -> MetaEvent:
        from ..models import IntentBypassUsedDecision

        return self.build(
            "INTENT_BYPASS_USED",
            IntentBypassUsedDecision(
                bypass_phrase=bypass_phrase,
                original_message_excerpt=original_message_excerpt,
            ),
            actor=actor,
            reasoning=reasoning,
            affected_entities=[],
            session=session,
            **common,
        )
