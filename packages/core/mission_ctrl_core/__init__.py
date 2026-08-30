"""mission_ctrl_core: Pure Python intent-layer library.

No network, no LLM. Validates and persists `.intent/` artifacts and provides
deterministic decision support (planner, recap). Git history is read via a
read-only `git log` (`logic/gitutil.py`) — never a write, and absent when the
path is not a repository.
"""

from .logic import (
    Commit,
    RecapEvent,
    RecapResult,
    Suggestion,
    commits_summary,
    generate_recap,
    git_commits_since,
    is_git_repo,
    suggest_next,
)
from .stores import (
    BacklogStore,
    ConstraintsStore,
    EventBuilder,
    IntentStore,
    MetaStore,
    MissionStore,
    MvpStore,
    SpecStore,
)

__all__ = [
    "BacklogStore",
    "Commit",
    "ConstraintsStore",
    "EventBuilder",
    "IntentStore",
    "MetaStore",
    "MissionStore",
    "MvpStore",
    "RecapEvent",
    "RecapResult",
    "SpecStore",
    "Suggestion",
    "commits_summary",
    "generate_recap",
    "git_commits_since",
    "is_git_repo",
    "suggest_next",
    "__version__",
]

__version__ = "0.1.0"
