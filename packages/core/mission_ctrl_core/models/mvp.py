from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .common import MvpId, UtcDatetime


class MvpItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: MvpId
    title: str = Field(min_length=1)
    description: str | None = None
    linked_specs: list[str] = Field(default_factory=list)


class Mvp(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1)
    items: list[MvpItem]
    created_at: UtcDatetime
    updated_at: UtcDatetime
