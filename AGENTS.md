# AGENTS.md — Mission Ctrl

> Intent layer between a developer and an AI coding agent (Pi). Keeps a git-tracked
> local record of mission/MVP/constraints, a backlog, a spec dependency graph, and
> a session event log (`meta.jsonl`). The agent reasons; skills validate & persist.
>
> **Key fact:** This repo is greenfield — no Python code exists yet. All work flows
> through OpenSpec changes. Start at `docs/kanban.md`.

## Architecture

- `packages/core` → `mission_ctrl_core`: pure Python, **no network / LLM / subprocess**.
  Pydantic v2 models, JSON + JSONL stores, `graphlib.TopologicalSorter` for cycle detection.
- `packages/pi-package` → `mission_ctrl_pi`: Pi extension (hooks + skills).
  Imports core directly — no bridge, no Node.js.
- Toolchain: Python 3.11+, **uv workspaces** (root `pyproject.toml` + single
  `uv.lock`, members `packages/*`), pytest, ruff.

## Before You Start

1. Read `docs/handoff.md` — last session's decisions + next steps.
2. Read `docs/kanban.md` — find the **active OpenSpec change** in the Change Index.
3. Read `openspec/changes/<change-id>/{proposal,design,tasks}.md` — your spec & task list.
4. Ask one clarifying question if anything is ambiguous. Don't gold-plate.

## Commands

Once code exists, from repo root:
- `uv sync` — install both packages (single lock).
- `uv run pytest packages/core/tests/` or `uv run pytest packages/pi-package/tests/` — run one package's tests.
- `uv run ruff check . && uv run ruff format .` — lint + format.

This repo's own OpenSpec workflow uses the `openspec` CLI. Available skills
live in `.pi/skills/openspec-*` (propose, apply-change, archive-change,
explore, sync-specs, update-change). These manage the project's own spec
changes — they are **not** the `mission_ctrl_pi` package's skills.

## Workflow

- Pick the **first unchecked** task in the active change's `tasks.md`.
  Implement → test → mark `- [ ] → - [x]`.
- **Atomic commits.** Format: `<change-id>: <what you did>`
  (e.g. `core-foundation-01: add MissionStore read/write + tests`).
- **One task at a time.** No scope creep — if you spot something unrelated,
  note it in `docs/handoff.md` under "Noticed / Deferred" and keep moving.
- **Tests before done.** A task isn't done until it has a test (or a documented
  reason why one can't exist).
- **Update `docs/handoff.md` when an OpenSpec change is completed** (all tasks
  done + archived) — record what shipped, key decisions, and what's next so the
  next session picks up cleanly.
- **Append a session summary to `docs/handoff.md` before stopping.**

## Never Do These Things

- ❌ Hand-edit `.intent/` files — always go through stores or skills.
- ❌ Add network calls, subprocess calls, or LLM calls to `mission_ctrl_core`.
- ❌ Implement features outside the current OpenSpec change unless asked.
- ❌ Refactor "while you're in there" unless the current task requires it.
- ❌ Introduce Node.js, TypeScript, or non-Python dependencies in the v1 path.

## Data Layer (when building stores)

- `.intent/` files: `mission.json`, `mvp.json`, `constraints.json`,
  `backlog.json`, `specs.json`, `meta.jsonl` (one JSON object per line, append-only).
- IDs: global canonical (`mis_001`, `spec_042`, `evt_000391`) — zero-padded counters.
- Timestamps: ISO 8601 UTC.
- Dependency rules (enforced by core): no cycles in `depends_on`; cannot set a
  spec to `in_progress` while any `depends_on` spec isn't `done`.
- Reference contracts: `docs/design.md` §3–4, live samples in `docs/examples/`.

## Session Handoff

Every session ends with an entry in `docs/handoff.md` (newest first).
Format see `docs/handoff.md` header. The next session reads handoff → kanban →
active change docs.
