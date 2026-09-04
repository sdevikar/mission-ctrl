from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from .common import EvtId, UtcDatetime


class Actor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["human", "agent"]
    name: str


class EntityRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    id: str


class LinkedIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mission_id: str
    mvp_version: str
    constraints_version: str


class SessionRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str


class EventBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, ser_json_by_alias=True
    )

    event_id: EvtId
    timestamp: UtcDatetime
    actor: Actor
    affected_entities: list[EntityRef]
    linked_intent: LinkedIntent
    reasoning: str
    depends_on: list[str] = Field(default_factory=list)
    git_refs: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    session: SessionRef


class IntentCreatedDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mission_version: str
    mvp_version: str
    constraints_version: str


class BacklogAddedDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    bucket: str


class BacklogTriageDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bucket: str
    alignment: dict[str, Any]


class SpecCreatedDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec_title: str
    status: str
    links: dict[str, list[str]] = Field(default_factory=dict)


class SpecStatusUpdatedDecision(BaseModel):
    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, ser_json_by_alias=True
    )

    from_status: str = Field(validation_alias="from", serialization_alias="from")
    to: str


class DesignProposedDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    digest_id: str
    key_choices: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class DesignApprovedDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    digest_id: str
    approval: bool
    notes: str | None = None


class SessionStartedDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gap_hours: float
    verbosity: str


class IntentInterceptedDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern_matched: str
    redirect_target: str
    original_message_excerpt: str


class IntentBypassUsedDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bypass_phrase: str
    original_message_excerpt: str


class IntentCreatedEvent(EventBase):
    event_type: Literal["INTENT_CREATED"]
    decision: IntentCreatedDecision


class BacklogAddedEvent(EventBase):
    event_type: Literal["BACKLOG_ADDED"]
    decision: BacklogAddedDecision


class BacklogTriageEvent(EventBase):
    event_type: Literal["BACKLOG_TRIAGE"]
    decision: BacklogTriageDecision


class SpecCreatedEvent(EventBase):
    event_type: Literal["SPEC_CREATED"]
    decision: SpecCreatedDecision


class SpecStatusUpdatedEvent(EventBase):
    event_type: Literal["SPEC_STATUS_UPDATED"]
    decision: SpecStatusUpdatedDecision


class DesignProposedEvent(EventBase):
    event_type: Literal["DESIGN_PROPOSED"]
    decision: DesignProposedDecision


class DesignApprovedEvent(EventBase):
    event_type: Literal["DESIGN_APPROVED"]
    decision: DesignApprovedDecision


class SessionStartedEvent(EventBase):
    event_type: Literal["SESSION_STARTED"]
    decision: SessionStartedDecision


class IntentInterceptedEvent(EventBase):
    event_type: Literal["INTENT_INTERCEPTED"]
    decision: IntentInterceptedDecision


class IntentBypassUsedEvent(EventBase):
    event_type: Literal["INTENT_BYPASS_USED"]
    decision: IntentBypassUsedDecision


MetaEvent = Annotated[
    Union[
        IntentCreatedEvent,
        BacklogAddedEvent,
        BacklogTriageEvent,
        SpecCreatedEvent,
        SpecStatusUpdatedEvent,
        DesignProposedEvent,
        DesignApprovedEvent,
        IntentInterceptedEvent,
        IntentBypassUsedEvent,
        SessionStartedEvent,
    ],
    Field(discriminator="event_type"),
]

MetaEventAdapter = TypeAdapter(MetaEvent)
