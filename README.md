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
- [Claude Code](https://code.claude.com/docs/en/quickstart) 2.x (for the
  plugin; core works standalone)

## Installation

```bash
git clone <repo> && cd mission-ctrl
uv sync --all-packages
```

For Pi, install the extension from the local path (project-local config with `-l`):

```bash
pi install ./packages/pi-package
```

For Claude Code, load the plugin from the local path (no install step; local
copy wins over same-named marketplace copies for that session):

```bash
claude --plugin-dir ./packages/claude-plugin
```

Then invoke skills namespaced, e.g. `/mission-ctrl:intent-status` (run
`/mission-ctrl:intent-init` first in projects without `.intent/`). After
editing the plugin, `/reload-plugins` picks up changes without a restart.
The plugin needs the repo's Python env: run `uv sync` once from the repo
root (the bundled `bin/mission-ctrl` wrapper re-execs through `uv`
automatically when the system python lacks the deps; set `MISSION_CTRL_ROOT`
if the plugin ever lives outside this checkout). Validate with:

```bash
claude plugin validate ./packages/claude-plugin
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

In Claude Code the same skills are namespaced (`/mission-ctrl:intent-init`,
`/mission-ctrl:intent-add-idea`, … — all 10 loop skills plus a pending
`intent-log-feedback`, see `packages/claude-plugin/README.md`). Hooks behave
identically on both hosts: session open injects a gap-tiered recap,
"implement X" is intercepted with the same redirect ladder and the
**"override intent"** bypass.

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
- `packages/claude-plugin` — Claude Code plugin (skills, hooks, `bin/`
  wrapper); prompts + wiring only, executes through the Python packages.
- `docs/` — `design.md` (source of truth), `architecture.md`, `kanban.md`
  (build status), `handoff.md` (session log), `examples/`.
- `openspec/` — spec changes (active) and synced capability specs.

Status: M0–M3 implemented and archived (core, logic, Pi extension, hooks).
Claude plugin (`claude-plugin-08`) implemented 14/16 — pending a live
`--plugin-dir` dogfood pass and `intent:log-feedback` (`log-feedback-06`).
Next: feedback-logging skill, then a one-week dogfood + v0.1.0 release.
