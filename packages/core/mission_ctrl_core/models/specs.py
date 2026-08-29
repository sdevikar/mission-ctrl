from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from .common import SpecId, UtcDatetime


class SpecStatus(StrEnum):
    DRAFT = "draft"
    DESIGN_PROPOSED = "design_proposed"
    DESIGN_APPROVED = "design_approved"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class SpecLinks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ideas: list[str] = Field(default_factory=list)
    mvp_items: list[str] = Field(default_factory=list)


class SpecNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: SpecId
    title: str = Field(min_length=1)
    status: SpecStatus = SpecStatus.DRAFT
    depends_on: list[str] = Field(default_factory=list)
    links: SpecLinks = Field(default_factory=SpecLinks)


class Specs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[SpecNode]
    updated_at: UtcDatetime | None = None
