from __future__ import annotations

from pathlib import Path

from mission_ctrl_core.models import (
    Actor,
    Constraints,
    Mission,
    Mvp,
    SessionRef,
)
from mission_ctrl_core.stores import IntentStore
from mission_ctrl_core.stores.base import utcnow

from ..agents_sync import sync_after_write
from ..schemas import InitInput, InitResult, SkillError
from .common import get_store


@sync_after_write
def intent_init(
    input: InitInput,
    store: IntentStore | None = None,
    root: Path | str = ".",
    actor: Actor | None = None,
    session: SessionRef | None = None,
) -> InitResult:
    st = get_store(store, root)
    if st.intent_dir.exists() and any(st.intent_dir.iterdir()):
        raise SkillError(
            "ALREADY_INITIALIZED",
            f"Intent directory {st.intent_dir} is already initialized",
        )

    ts = utcnow()
    statement = (
        input.mission.strip()
        if input.mission and input.mission.strip()
        else f"Mission statement for {input.project_name}."
    )
    mission = Mission(
        id="mis_001",
        version="v1.0",
        statement=statement,
        success_criteria=[],
        created_at=ts,
        updated_at=ts,
    )
    mvp = Mvp(
        version="v1.0",
        items=[],
        created_at=ts,
        updated_at=ts,
    )
    constraints = Constraints(
        version="v1.0",
        constraints=[],
        created_at=ts,
        updated_at=ts,
    )
    act = actor or Actor(type="human", name="developer")
    ses = session or SessionRef(id="ses_0001")

    st.init(
        mission=mission,
        mvp=mvp,
        constraints=constraints,
        actor=act,
        session=ses,
        reasoning=f"Initialize project intent for {input.project_name}.",
    )
    return InitResult(status="created", intent_dir=str(st.intent_dir.resolve()))
