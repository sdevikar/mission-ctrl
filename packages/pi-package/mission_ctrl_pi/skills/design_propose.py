from __future__ import annotations

from pathlib import Path

from mission_ctrl_core.models import Actor, SessionRef, SpecStatus
from mission_ctrl_core.stores import IntentStore

from ..agents_sync import sync_after_write
from ..schemas import DesignProposeInput, DesignProposeResult, SkillError
from .common import get_store, require_initialized


@sync_after_write
def intent_design_propose(
    input: DesignProposeInput,
    store: IntentStore | None = None,
    root: Path | str = ".",
    actor: Actor | None = None,
    session: SessionRef | None = None,
) -> DesignProposeResult:
    """Transition a spec from draft → design_proposed.

    Pi supplies the design digest text; the skill validates the spec is in draft,
    updates the spec status, and emits a DESIGN_PROPOSED event.
    """
    st = get_store(store, root)
    require_initialized(st)

    try:
        spec = st.specs.get(input.spec_id)
    except KeyError:
        raise SkillError("NOT_FOUND", f"Spec {input.spec_id} not found")

    if spec.status is not SpecStatus.DRAFT:
        raise SkillError(
            "ILLEGAL_TRANSITION",
            f"Spec {input.spec_id} must be in draft to propose a design "
            f"(current status: {spec.status.value})",
        )

    st.specs.set_status(input.spec_id, SpecStatus.DESIGN_PROPOSED)

    act = actor or Actor(type="human", name="developer")
    ses = session or SessionRef(id="ses_0001")
    st.builder().design_proposed(
        input.spec_id,
        input.digest,
        actor=act,
        reasoning=f"Design proposed for {input.spec_id}: {input.digest[:80]}",
        session=ses,
    )

    return DesignProposeResult(spec_id=input.spec_id)
