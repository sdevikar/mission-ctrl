from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from mission_ctrl_core.logic import (
    Commit,
    RecapResult,
    generate_recap,
    git_commits_since,
    is_git_repo,
    suggest_next,
)
from mission_ctrl_core.stores import IntentStore

FIXTURES = Path(__file__).parent / "fixtures"


def _store(name: str) -> IntentStore:
    return IntentStore(FIXTURES / name)


# --------------------------------------------------------------------------
# Planner
# --------------------------------------------------------------------------
def test_planner_empty_project_has_no_candidates():
    recos = suggest_next(_store("empty-project"))
    assert recos == []


def test_planner_excludes_blocked_and_done():
    recos = suggest_next(_store("complex-graph"))
    ids = [s.spec_id for s in recos]
    # spec_004 is blocked (spec_005 not done) -> excluded
    assert "spec_004" not in ids
    # done specs excluded
    assert "spec_001" not in ids
    assert "spec_002" not in ids
    # spec_003 is design_approved with a done dep -> included
    assert "spec_003" in ids


def test_planner_mid_flight():
    recos = suggest_next(_store("mid-flight"))
    ids = [s.spec_id for s in recos]
    # spec_001 is in_progress (excluded), spec_002 is draft but depends on
    # spec_001 which is not done -> blocked, excluded
    assert ids == []


def test_planner_mvp_linked_ranked_first():
    # Build a synthetic store to assert MVP-linked ordering deterministically.
    import tempfile

    from mission_ctrl_core.models import (
        Actor,
        Constraint,
        Constraints,
        Mission,
        Mvp,
        MvpItem,
        SessionRef,
        SpecLinks,
        SpecNode,
        Specs,
    )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        st = IntentStore(root)
        ts = "2026-03-10T10:15:00Z"
        st.init(
            mission=Mission(
                id="mis_001",
                version="v1.0",
                statement="m",
                success_criteria=[],
                created_at=ts,
                updated_at=ts,
            ),
            mvp=Mvp(
                version="v1.0",
                items=[MvpItem(id="mvp_001", title="t")],
                created_at=ts,
                updated_at=ts,
            ),
            constraints=Constraints(
                version="v1.0",
                constraints=[
                    Constraint(id="con_001", rule="r", rationale="r", severity="high")
                ],
                created_at=ts,
                updated_at=ts,
            ),
            actor=Actor(type="human", name="h"),
            session=SessionRef(id="ses_0001"),
        )
        st.specs.write(
            Specs(
                nodes=[
                    # A: unblocked, not MVP-linked
                    SpecNode(id="spec_010", title="A"),
                    # B: unblocked, MVP-linked
                    SpecNode(
                        id="spec_020", title="B", links=SpecLinks(mvp_items=["mvp_001"])
                    ),
                    # C: blocked (depends on A, not done)
                    SpecNode(id="spec_030", title="C", depends_on=["spec_010"]),
                ]
            )
        )
        recos = suggest_next(st)
        ids = [s.spec_id for s in recos]
        # MVP-linked B first, then A; C blocked
        assert ids == ["spec_020", "spec_010"]
        assert recos[0].mvp_linked is True
        assert recos[0].reason == "MVP-linked; no prerequisites"


def test_planner_count_limits_results():
    recos = suggest_next(_store("complex-graph"), count=1)
    assert len(recos) <= 1


def test_planner_continuity_tie_break():
    import tempfile

    from mission_ctrl_core.models import (
        Actor,
        Constraints,
        Mission,
        Mvp,
        SessionRef,
        SpecLinks,
        SpecNode,
        Specs,
    )

    with tempfile.TemporaryDirectory() as tmp:
        st = IntentStore(Path(tmp))
        ts = "2026-03-10T10:15:00Z"
        st.init(
            mission=Mission(
                id="mis_001",
                version="v1.0",
                statement="m",
                success_criteria=[],
                created_at=ts,
                updated_at=ts,
            ),
            mvp=Mvp(version="v1.0", items=[], created_at=ts, updated_at=ts),
            constraints=Constraints(
                version="v1.0", constraints=[], created_at=ts, updated_at=ts
            ),
            actor=Actor(type="human", name="h"),
            session=SessionRef(id="ses_0001"),
        )
        st.specs.write(
            Specs(
                nodes=[
                    # in_progress focus on spec_001 (area: idea_i)
                    SpecNode(
                        id="spec_001",
                        title="Focus",
                        status="in_progress",
                        links=SpecLinks(ideas=["idea_share"]),
                    ),
                    # X shares the focus area (idea_share)
                    SpecNode(
                        id="spec_002", title="X", links=SpecLinks(ideas=["idea_share"])
                    ),
                    # Y unrelated
                    SpecNode(
                        id="spec_003", title="Y", links=SpecLinks(ideas=["idea_other"])
                    ),
                ]
            )
        )
        recos = suggest_next(st)
        ids = [s.spec_id for s in recos]
        # both unlinked & unblocked & no deps -> tie; continuity wins for X
        assert ids == ["spec_002", "spec_003"]
        assert recos[0].continuous is True
        assert recos[1].continuous is False


# --------------------------------------------------------------------------
# Recap
# --------------------------------------------------------------------------
def test_recap_empty_project():
    res = generate_recap(_store("empty-project"))
    assert isinstance(res, RecapResult)
    assert res.mvp_percent == 0
    assert res.mvp_total == 2
    assert res.last_focus is None
    assert res.recommendations == []
    assert "Mission:" in res.rendered
    assert "0% complete" in res.rendered


def test_recap_mid_flight_mvp_percent():
    res = generate_recap(_store("mid-flight"))
    # 2 mvp items; spec_001 (mvp_001) is in_progress not done;
    # spec_002 (mvp_002) is draft -> 0% complete
    assert res.mvp_completed == 0
    assert res.mvp_percent == 0
    assert res.last_focus == "spec_001"
    assert res.last_focus_status == "in_progress"


def test_recap_complex_graph_mvp_and_focus():
    res = generate_recap(_store("complex-graph"))
    # both mvp items link to spec_001/spec_002, both done -> 100%
    assert res.mvp_completed == 2
    assert res.mvp_percent == 100
    # no in_progress spec
    assert res.last_focus is None
    # unblocked candidates: spec_003 (design_approved) and spec_005 (draft);
    # both deps done (spec_001/spec_002). Sorted by id since neither is
    # mvp-linked and there is no focus for continuity.
    assert [s.spec_id for s in res.recommendations] == ["spec_003", "spec_005"]


def test_recap_changes_since_iso_bounded():
    store = _store("mid-flight")
    # last event in mid-flight is the 3rd (evt_000003). Pick its timestamp so
    # nothing comes after -> empty changes.
    events = store.meta.read_all()
    last_ts = events[-1].timestamp
    res = generate_recap(store, since_iso=last_ts.isoformat())
    assert res.events_since == []
    assert res.changes == []


def test_recap_verbosity_brief_is_shorter():
    store = _store("mid-flight")
    brief = generate_recap(store, verbosity="brief")
    standard = generate_recap(store, verbosity="standard")
    assert len(brief.rendered) <= len(standard.rendered)
    assert "## Next up" in standard.rendered
    assert "## Next up" not in brief.rendered


# --------------------------------------------------------------------------
# Git utility (real temp repo, read-only assertions)
# --------------------------------------------------------------------------
def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@t",
        },
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(["init"], r)
    for i, day in enumerate(
        [
            "2026-01-01T00:00:00Z",
            "2026-01-02T00:00:00Z",
            "2026-01-03T00:00:00Z",
            "2026-01-04T00:00:00Z",
        ],
        start=1,
    ):
        (r / f"f{i}.txt").write_text(f"v{i}")
        _git(["add", "."], r)
        env_dates = {
            "GIT_AUTHOR_DATE": day,
            "GIT_COMMITTER_DATE": day,
        }
        subprocess.run(
            ["git", "commit", "-m", f"commit {i}"],
            cwd=r,
            check=True,
            capture_output=True,
            env={
                **os.environ,
                **env_dates,
                "GIT_AUTHOR_NAME": "t",
                "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t",
                "GIT_COMMITTER_EMAIL": "t@t",
            },
        )
    return r


def test_not_a_git_repo(tmp_path: Path):
    assert is_git_repo(tmp_path) is False
    assert git_commits_since(tmp_path, None) == []


def test_git_commits_since_since_iso(repo: Path):
    commits = git_commits_since(repo, None)
    assert len(commits) == 4
    subjects = [c.subject for c in commits]
    # oldest first
    assert subjects[0] == "commit 1"
    assert subjects[-1] == "commit 4"
    assert all(isinstance(c, Commit) for c in commits)


def test_git_commits_since_respects_boundary(repo: Path):
    assert len(git_commits_since(repo, None)) == 4
    # boundary exactly between commit 2 (Jan 2) and 3 (Jan 3):
    # strictly newer -> commit 3 and 4
    mid = git_commits_since(repo, "2026-01-02T12:00:00Z")
    assert [c.subject for c in mid] == ["commit 3", "commit 4"]
    # far future -> nothing strictly newer
    assert git_commits_since(repo, "2999-01-01T00:00:00Z") == []
    # far past -> everything
    assert len(git_commits_since(repo, "1970-01-01T00:00:00Z")) == 4


def test_recap_git_read_only_leaves_tree_clean(repo: Path, monkeypatch):
    # Point the recap at a fixture intent dir but read git from `repo`.
    store = _store("mid-flight")
    before_status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True
    ).stdout
    res = generate_recap(store, since_iso="2020-01-01T00:00:00Z", root=repo)
    after_status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True
    ).stdout
    assert before_status == after_status  # clean before and after
    assert len(res.git_commits) == 4
    assert len(res.changes) == 4


# --------------------------------------------------------------------------
# Zero network
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["empty-project", "mid-flight", "complex-graph"])
def test_logic_layer_no_network(monkeypatch, name: str):
    def _blocked(*a, **k):
        raise AssertionError("network access attempted in logic layer")

    monkeypatch.setattr("urllib.request.urlopen", _blocked)
    monkeypatch.setattr("socket.getaddrinfo", _blocked, raising=False)
    store = _store(name)
    # must complete without raising
    suggest_next(store)
    generate_recap(store)
