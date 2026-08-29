from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .common import MisId, UtcDatetime


class Mission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: MisId
    version: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    success_criteria: list[str]
    created_at: UtcDatetime
    updated_at: UtcDatetime
