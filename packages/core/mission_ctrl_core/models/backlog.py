from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from .common import IdeaId, UtcDatetime


class Bucket(StrEnum):
    UNTRIAGED = "untriaged"
    MVP_CRITICAL = "mvp_critical"
    PARKED = "parked"
    ARCHIVED = "archived"


class MissionAlignment(StrEnum):
    STRONG = "strong"
    WEAK = "weak"
    NEUTRAL = "neutral"
    NOT_ALIGNED = "not_aligned"


class MvpAlignment(StrEnum):
    REQUIRED = "required"
    NOT_REQUIRED = "not_required"
    EXTENDS = "extends"


class Alignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mission: MissionAlignment
    mvp: MvpAlignment
    constraints: list[str] = Field(default_factory=list)


class BacklogLinks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    specs: list[str] = Field(default_factory=list)
    mvp_items: list[str] = Field(default_factory=list)


class BacklogItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: IdeaId
    title: str = Field(min_length=1)
    description: str | None = None
    bucket: Bucket = Bucket.UNTRIAGED
    alignment: Alignment
    links: BacklogLinks = Field(default_factory=BacklogLinks)
    created_at: UtcDatetime
    updated_at: UtcDatetime


class Backlog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[BacklogItem]
