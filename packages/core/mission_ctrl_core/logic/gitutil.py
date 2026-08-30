from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_GIT_FMT = "%h%x09%ct%x09%s"  # sha <TAB> epoch <TAB> subject


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    epoch: int = 0


def is_git_repo(root: Path | str) -> bool:
    return (Path(root) / ".git").exists()


def _since_epoch(since_iso: str) -> int:
    return int(datetime.fromisoformat(since_iso.replace("Z", "+00:00")).timestamp())


def git_commits_since(root: Path | str, since_iso: str | None) -> list[Commit]:
    """Return commits strictly newer than `since_iso`, oldest first.

    Read-only: invokes `git log --no-pager` only; never writes to the repo,
    index, or working tree. Returns [] when `root` is not a git repo, git is
    unavailable, or no commits match. Commit timestamps are filtered in Python
    (epoch compare) so the result is deterministic regardless of git's
    `--since` walking quirks.
    """
    root = Path(root)
    if not is_git_repo(root):
        return []
    argv = ["git", "-C", str(root), "--no-pager", "log",
            f"--pretty=format:{_GIT_FMT}"]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True,
                              check=False, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        return []

    commits: list[Commit] = []
    for line in proc.stdout.splitlines():
        line = line.rstrip()
        if not line:
            continue
        sha, _, rest = line.partition("\t")
        epoch_s, _, subject = rest.partition("\t")
        if not epoch_s.isdigit():
            continue
        commits.append(Commit(sha=sha, subject=subject, epoch=int(epoch_s)))

    if since_iso is not None:
        cutoff = _since_epoch(since_iso)
        commits = [c for c in commits if c.epoch > cutoff]

    # `git log` prints newest first; we want oldest first
    commits.reverse()
    return commits


def commits_summary(commits: list[Commit]) -> list[str]:
    return [f"{c.sha} {c.subject}" for c in commits]
