from __future__ import annotations

from pathlib import Path

from mission_ctrl_core.stores import IntentStore

from ..schemas import SkillError


def get_store(store: IntentStore | None = None, root: Path | str = ".") -> IntentStore:
    if store is not None:
        return store
    return IntentStore(root)


def require_initialized(store: IntentStore) -> None:
    if (
        not store.intent_dir.exists()
        or not (store.intent_dir / "mission.json").exists()
    ):
        raise SkillError(
            "NOT_INITIALIZED", "Intent store is not initialized. Run intent:init first."
        )
