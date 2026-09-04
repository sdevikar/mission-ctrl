from __future__ import annotations

from pathlib import Path

from mission_ctrl_core.models import (
    Actor,
    Bucket,
    SessionRef,
    SpecLinks,
    SpecNode,
    SpecStatus,
)
from mission_ctrl_core.stores import IntentStore

from ..agents_sync import sync_after_write
from ..schemas import SkillError, SpecCreateInput, SpecCreateResult
from .common import get_store, require_initialized


@sync_after_write
def intent_spec_create(
    input: SpecCreateInput,
    store: IntentStore | None = None,
    root: Path | str = ".",
    actor: Actor | None = None,
    session: SessionRef | None = None,
) -> SpecCreateResult:
    st = get_store(store, root)
    require_initialized(st)

    try:
        idea = st.backlog.get(input.idea_id)
    except KeyError:
        raise SkillError("NOT_FOUND", f"Idea {input.idea_id} not found in backlog")

    if idea.bucket not in (Bucket.MVP_CRITICAL, Bucket.PARKED):
        raise SkillError(
            "INVALID_INPUT",
            f"Cannot create spec from idea in bucket '{idea.bucket.value}'."
            " Must be 'mvp_critical' or 'parked'.",
        )

    spec_id = st.specs.next_id()
    title = (input.title or idea.title).strip()
    node = SpecNode(
        id=spec_id,
        title=title,
        status=SpecStatus.DRAFT,
        depends_on=[],
        links=SpecLinks(ideas=[input.idea_id]),
    )
    st.specs.add_node(node)

    # Link spec back to backlog item
    current_specs = list(idea.links.specs)
    if spec_id not in current_specs:
        current_specs.append(spec_id)
        st.backlog.update(
            input.idea_id,
            links={"specs": current_specs, "mvp_items": idea.links.mvp_items},
        )

    act = actor or Actor(type="human", name="developer")
    ses = session or SessionRef(id="ses_0001")
    st.builder().spec_created(
        spec_id=spec_id,
        spec_title=title,
        actor=act,
        reasoning=f"Promoted idea {input.idea_id} to spec {spec_id}.",
        session=ses,
        links={"ideas": [input.idea_id]},
    )

    return SpecCreateResult(spec_id=spec_id, status="draft")
