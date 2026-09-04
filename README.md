# Mission Ctrl

Intent layer between a developer and an AI coding agent. It keeps a
git-tracked local record (`.intent/`) of mission, MVP, constraints, backlog,
specs, and a session event log — so the agent works from explicit intent
instead of scattered chat context.

The loop: capture an idea → triage it → turn it into a spec → pass a design
gate → work it → mark it done. Hooks onboard returning sessions automatically
and nudge implementation-intent messages back to the backlog-first workflow.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (workspace toolchain)
- [Pi](https://github.com/anomalyco/opencode) coding agent (for the extension;
  core works standalone)

## Installation

```bash
git clone <repo> && cd mission-ctrl
uv sync --all-packages
```

For Pi, install the extension from the local path (project-local config with `-l`):

```bash
pi install ./packages/pi-package
```

Remote distribution (PyPI + npm wrapper) lands with v0.1.0 — see
`docs/kanban.md` (M4). Until then, local path install is the supported route.

## Usage

All state lives in `<project>/.intent/` (JSON + JSONL). Never hand-edit those
files — go through the skills.

### Core lifecycle (in Pi)

```
intent:init            # create .intent/ for a project (mission, MVP, constraints)
intent:add-idea        # capture an idea → backlog (title, description)
intent:triage          # classify it: mvp / later / rejected (+ alignment verdict)
intent:spec-create     # turn a triaged idea into a spec node (status: draft)
intent:design-propose  # draft → design_proposed (Pi supplies design digest)
intent:design-approve  # design_proposed → design_approved, or back to draft
                       # (rejections require notes)
intent:spec-status     # design_approved → in_progress → done (blocked allowed)
intent:next            # ranked next-spec suggestion (MVP-first, unblocked)
intent:status          # dashboard: mission, MVP %, active specs, next step
intent:recap           # on-demand recap (brief / standard / full)
```

Minimal happy path:

```
init → add-idea → triage → spec-create → design-propose →
design-approve → spec-status(in_progress) → spec-status(done) → status
```

### Hooks (automatic)

- **Session start** — opening a project with `.intent/` injects a recap sized
  to the gap since the last session (<1h: skip, 1–8h: brief, 8–48h:
  standard, >48h: full) and logs `SESSION_STARTED`. No `.intent/` → silent
  no-op.
- **Before send** — messages like "implement X" are intercepted and redirected
  to the right skill (`add-idea` → `triage` → `spec-create` →
  `design-propose` → `spec-status`, closest-to-code first). Say
  **"override intent"** to bypass; bypasses are surfaced and logged, never
  silent.
- **AGENTS.md sync** — every skill write regenerates the project's `AGENTS.md`
  context file from a template (user text sanitized; injection patterns
  rejected).

## Development

```bash
uv sync                                   # install both packages
uv run pytest packages/core/tests/        # core tests
uv run pytest packages/pi-package/tests/  # extension tests
uv run pytest packages/                   # everything
uv run ruff check . && uv run ruff format .  # lint + format
```

## Layout

- `packages/core` (`mission_ctrl_core`) — pure Python stores, models,
  planner, recap. Deterministic, network-free, no LLM calls.
- `packages/pi-package` (`mission_ctrl_pi`) — skills, hooks, AGENTS.md sync,
  Jinja2 template.
- `docs/` — `design.md` (source of truth), `architecture.md`, `kanban.md`
  (build status), `handoff.md` (session log), `examples/`.
- `openspec/` — spec changes (active) and synced capability specs.

Status: M0–M3 implemented and archived (core, logic, Pi extension, hooks).
Next: feedback-logging skill, then a one-week dogfood + v0.1.0 release.
