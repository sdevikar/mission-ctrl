from __future__ import annotations

from pathlib import Path

from mission_ctrl_core.models import Actor, SessionRef, SpecStatus
from mission_ctrl_core.stores import IntentStore

from ..agents_sync import sync_after_write
from ..schemas import DesignApproveInput, DesignApproveResult, SkillError
from .common import get_store, require_initialized


@sync_after_write
def intent_design_approve(
    input: DesignApproveInput,
    store: IntentStore | None = None,
    root: Path | str = ".",
    actor: Actor | None = None,
    session: SessionRef | None = None,
) -> DesignApproveResult:
    """Approve or reject a design proposal.

    - approved → spec transitions to design_approved; emits DESIGN_APPROVED
    - rejected → spec returns to draft; notes are required; emits DESIGN_APPROVED
      (with approval=False, following the existing core model convention)
    """
    st = get_store(store, root)
    require_initialized(st)

    try:
        spec = st.specs.get(input.spec_id)
    except KeyError:
        raise SkillError("NOT_FOUND", f"Spec {input.spec_id} not found")

    if spec.status is not SpecStatus.DESIGN_PROPOSED:
        raise SkillError(
            "ILLEGAL_TRANSITION",
            f"Spec {input.spec_id} must be in design_proposed to approve/reject "
            f"(current status: {spec.status.value})",
        )

    if input.decision == "rejected" and not (input.notes and input.notes.strip()):
        raise SkillError(
            "NOTES_REQUIRED",
            "Notes are required when rejecting a design proposal",
        )

    if input.decision == "approved":
        new_status = SpecStatus.DESIGN_APPROVED
        new_status_str: str = "design_approved"
        reasoning = f"Design approved for {input.spec_id}."
    else:
        new_status = SpecStatus.DRAFT
        new_status_str = "draft"
        reasoning = f"Design rejected for {input.spec_id}: {input.notes}"

    st.specs.set_status(input.spec_id, new_status)

    act = actor or Actor(type="human", name="developer")
    ses = session or SessionRef(id="ses_0001")
    st.builder().design_approved(
        input.spec_id,
        approval=input.decision == "approved",
        notes=input.notes,
        actor=act,
        reasoning=reasoning,
        session=ses,
    )

    return DesignApproveResult(
        spec_id=input.spec_id,
        decision=input.decision,
        new_status=new_status_str,  # type: ignore[arg-type]
    )
