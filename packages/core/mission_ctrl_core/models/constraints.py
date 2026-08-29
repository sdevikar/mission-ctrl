from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from .common import ConId, UtcDatetime


class ConstraintSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Constraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: ConId
    rule: str = Field(min_length=1)
    rationale: str
    severity: ConstraintSeverity
    scope: list[str] = Field(default_factory=list)


class Constraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1)
    constraints: list[Constraint]
    created_at: UtcDatetime
    updated_at: UtcDatetime
