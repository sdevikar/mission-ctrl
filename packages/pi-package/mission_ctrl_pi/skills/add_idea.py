from __future__ import annotations

from pathlib import Path

from mission_ctrl_core.models import (
    Actor,
    BacklogAddedDecision,
    Bucket,
    EntityRef,
    SessionRef,
)
from mission_ctrl_core.stores import IntentStore

from ..schemas import AddIdeaInput, AddIdeaResult
from .common import get_store, require_initialized


def intent_add_idea(
    input: AddIdeaInput,
    store: IntentStore | None = None,
    root: Path | str = ".",
    actor: Actor | None = None,
    session: SessionRef | None = None,
) -> AddIdeaResult:
    st = get_store(store, root)
    require_initialized(st)

    title = input.title.strip()
    description = input.description.strip() if input.description else None
    item = st.backlog.add(title=title, description=description, bucket=Bucket.UNTRIAGED)
    idea_id = item.id

    act = actor or Actor(type="human", name="developer")
    ses = session or SessionRef(id="ses_0001")
    st.builder().build(
        "BACKLOG_ADDED",
        BacklogAddedDecision(title=item.title, bucket=item.bucket.value),
        actor=act,
        reasoning=f"Added idea: {item.title}",
        affected_entities=[EntityRef(type="backlog", id=idea_id)],
        session=ses,
    )

    return AddIdeaResult(idea_id=idea_id, status="added")
