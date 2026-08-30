"""Logic layer: deterministic decision support on top of intent state.

Pure functions of `.intent/` state plus read-only git history. No LLM, no
network. See `docs/decisions/no-llm-in-core.md`.
"""

from .gitutil import Commit, commits_summary, git_commits_since, is_git_repo
from .planner import Suggestion, suggest_next
from .recap import RecapEvent, RecapResult, Verbosity, generate_recap

__all__ = [
    "Commit",
    "RecapEvent",
    "RecapResult",
    "Suggestion",
    "Verbosity",
    "commits_summary",
    "generate_recap",
    "git_commits_since",
    "is_git_repo",
    "suggest_next",
]
