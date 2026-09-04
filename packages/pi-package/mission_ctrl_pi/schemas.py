from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SkillError(Exception):
    """Base error raised by Mission Ctrl skills."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class InitInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_name: str
    mission: str | None = None


class InitResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["created"] = "created"
    intent_dir: str


class AddIdeaInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1)
    description: str | None = None


class AddIdeaResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idea_id: str
    status: Literal["added"] = "added"


class TriageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idea_id: str
    bucket: Literal["mvp", "later", "rejected"]
    alignment_verdict: str


class TriageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idea_id: str
    bucket: str
    status: Literal["triaged"] = "triaged"


class SpecCreateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idea_id: str
    title: str | None = None


class SpecCreateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    spec_id: str
    status: Literal["draft"] = "draft"


class SpecStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    spec_id: str
    new_status: Literal["in_progress", "done", "blocked"]
    note: str | None = None


class SpecStatusResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    spec_id: str
    previous_status: str
    new_status: str


class NextResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    spec_id: str | None = None
    title: str
    reason: str


class SpecSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    status: str


class StatusResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mission: str
    mvp_completion_pct: float
    active_specs: list[SpecSummary]
    next_suggestion: NextResult


# ---------------------------------------------------------------------------
# M2b: Design-gate schemas
# ---------------------------------------------------------------------------

# RecapResult is the canonical typed output — imported from core, not redefined.
from mission_ctrl_core.logic.recap import RecapResult as RecapResult  # noqa: E402,F401


class RecapInput(BaseModel):
    """Input for intent:recap skill."""

    model_config = ConfigDict(extra="forbid")
    verbosity: Literal["brief", "standard", "full"] | None = None
    since_iso: str | None = None


class DesignProposeInput(BaseModel):
    """Input for intent:design-propose skill."""

    model_config = ConfigDict(extra="forbid")
    spec_id: str
    digest: str = Field(min_length=10)


class DesignProposeResult(BaseModel):
    """Output of intent:design-propose skill."""

    model_config = ConfigDict(extra="forbid")
    spec_id: str
    status: Literal["design_proposed"] = "design_proposed"


class DesignApproveInput(BaseModel):
    """Input for intent:design-approve skill."""

    model_config = ConfigDict(extra="forbid")
    spec_id: str
    decision: Literal["approved", "rejected"]
    notes: str | None = None


class DesignApproveResult(BaseModel):
    """Output of intent:design-approve skill."""

    model_config = ConfigDict(extra="forbid")
    spec_id: str
    decision: str
    new_status: Literal["design_approved", "draft"]
