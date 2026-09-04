from __future__ import annotations

from pathlib import Path

from mission_ctrl_core.models import (
    Actor,
    BacklogTriageDecision,
    Bucket,
    EntityRef,
    SessionRef,
)
from mission_ctrl_core.stores import IntentStore

from ..schemas import SkillError, TriageInput, TriageResult
from .common import get_store, require_initialized

_BUCKET_MAP: dict[str, Bucket] = {
    "mvp": Bucket.MVP_CRITICAL,
    "later": Bucket.PARKED,
    "rejected": Bucket.ARCHIVED,
}


def intent_triage(
    input: TriageInput,
    store: IntentStore | None = None,
    root: Path | str = ".",
    actor: Actor | None = None,
    session: SessionRef | None = None,
) -> TriageResult:
    st = get_store(store, root)
    require_initialized(st)

    try:
        st.backlog.get(input.idea_id)
    except KeyError:
        raise SkillError("NOT_FOUND", f"Idea {input.idea_id} not found in backlog")

    target_bucket = _BUCKET_MAP.get(input.bucket)
    if target_bucket is None:
        raise SkillError("INVALID_INPUT", f"Invalid bucket: {input.bucket}")

    updated = st.backlog.update(input.idea_id, bucket=target_bucket)

    act = actor or Actor(type="agent", name="pi")
    ses = session or SessionRef(id="ses_0001")
    st.builder().build(
        "BACKLOG_TRIAGE",
        BacklogTriageDecision(
            bucket=target_bucket.value,
            alignment={
                "mission": updated.alignment.mission.value,
                "mvp": updated.alignment.mvp.value,
                "verdict": input.alignment_verdict,
            },
        ),
        actor=act,
        reasoning=input.alignment_verdict,
        affected_entities=[EntityRef(type="backlog", id=input.idea_id)],
        session=ses,
    )

    return TriageResult(idea_id=input.idea_id, bucket=input.bucket, status="triaged")
