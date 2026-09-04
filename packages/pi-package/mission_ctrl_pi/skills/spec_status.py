from __future__ import annotations

from pathlib import Path

from mission_ctrl_core.errors import MissionCtrlError
from mission_ctrl_core.models import (
    Actor,
    SessionRef,
    SpecStatus,
)
from mission_ctrl_core.stores import IntentStore

from ..agents_sync import sync_after_write
from ..schemas import SkillError, SpecStatusInput, SpecStatusResult
from .common import get_store, require_initialized

_STATUS_MAP: dict[str, SpecStatus] = {
    "draft": SpecStatus.DRAFT,
    "design_proposed": SpecStatus.DESIGN_PROPOSED,
    "design_approved": SpecStatus.DESIGN_APPROVED,
    "in_progress": SpecStatus.IN_PROGRESS,
    "done": SpecStatus.DONE,
    "blocked": SpecStatus.BLOCKED,
}

_ALLOWED_TRANSITIONS: set[tuple[SpecStatus, SpecStatus]] = {
    # M2a paths
    (SpecStatus.DRAFT, SpecStatus.IN_PROGRESS),
    (SpecStatus.DRAFT, SpecStatus.BLOCKED),
    (SpecStatus.IN_PROGRESS, SpecStatus.DONE),
    (SpecStatus.IN_PROGRESS, SpecStatus.BLOCKED),
    (SpecStatus.BLOCKED, SpecStatus.IN_PROGRESS),
    (SpecStatus.BLOCKED, SpecStatus.DONE),
    # M2b path: design gate → in_progress
    (SpecStatus.DESIGN_APPROVED, SpecStatus.IN_PROGRESS),
    (SpecStatus.DESIGN_APPROVED, SpecStatus.BLOCKED),
}


@sync_after_write
def intent_spec_status(
    input: SpecStatusInput,
    store: IntentStore | None = None,
    root: Path | str = ".",
    actor: Actor | None = None,
    session: SessionRef | None = None,
    allowed_transitions: set[tuple[SpecStatus, SpecStatus]] | None = None,
) -> SpecStatusResult:
    st = get_store(store, root)
    require_initialized(st)

    try:
        spec = st.specs.get(input.spec_id)
    except KeyError:
        raise SkillError("NOT_FOUND", f"Spec {input.spec_id} not found")

    target = _STATUS_MAP.get(input.new_status)
    if target is None:
        raise SkillError("INVALID_INPUT", f"Invalid status: {input.new_status}")

    if target == SpecStatus.BLOCKED and not (input.note and input.note.strip()):
        raise SkillError(
            "INVALID_INPUT", "Note is required when transitioning to blocked"
        )

    curr = spec.status
    transitions = (
        allowed_transitions if allowed_transitions is not None else _ALLOWED_TRANSITIONS
    )
    if (curr, target) not in transitions:
        raise SkillError(
            "ILLEGAL_TRANSITION",
            f"Illegal transition from {curr.value} to {target.value}",
        )

    try:
        st.specs.set_status(input.spec_id, target)
    except MissionCtrlError as exc:
        raise SkillError("ILLEGAL_TRANSITION", str(exc)) from exc

    act = actor or Actor(type="human", name="developer")
    ses = session or SessionRef(id="ses_0001")
    st.builder().spec_status_updated(
        spec_id=input.spec_id,
        from_status=curr.value,
        to_status=target.value,
        actor=act,
        reasoning=input.note or f"Updated status of {input.spec_id} to {target.value}.",
        session=ses,
    )

    return SpecStatusResult(
        spec_id=input.spec_id,
        previous_status=curr.value,
        new_status=target.value,
    )
