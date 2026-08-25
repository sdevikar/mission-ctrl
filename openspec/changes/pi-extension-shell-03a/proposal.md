# Proposal: Pi Extension Shell — Core Loop (M2a)

## Why

Splits from pi-extension-shell-03 (archived). The intent loop can be delivered
in two steps: the seven skills that close the core lifecycle (init → add-idea →
triage → spec-create → spec-status → next → status) ship first, without the
design-gate workflow. This gives a usable, testable product sooner and makes
each milestone smaller and more independently verifiable.

## Prerequisites

- core-foundation-01 applied (M0 stores + models)
- logic-layer-02 applied (planner, recap, RecapResult)
- **Distribution decision resolved:** confirm whether Pi's install mechanism
  requires an npm wrapper for a pure-Python package before this change starts —
  M2a's done-when criterion depends on `pi install ./packages/pi-package`.

## What Changes

- New package `packages/pi-package` (Python, pyproject.toml, depends on
  `mission_ctrl_core`).
- `extension.py` manifest registering hook stubs (for M3) + 7 core-loop skills.
- Skill implementations (see `design.md` for full I/O contracts):
  - `intent:init` — creates `.intent/`, copies schemas/templates, emits `INTENT_CREATED`
  - `intent:add-idea` — appends idea to backlog, emits `BACKLOG_ADDED`
  - `intent:triage` — updates backlog bucket + alignment, emits `BACKLOG_TRIAGE`
  - `intent:spec-create` — promotes idea → spec node (draft), emits `SPEC_CREATED`
  - `intent:spec-status` — drives spec through draft → in_progress → done (and
    blocked); rejects illegal transitions
  - `intent:next` — read-only; returns planner suggestion
  - `intent:status` — read-only; returns mission, MVP %, active specs, next suggestion

## Non-goals

- Design-gate skills (`recap`, `design-propose`, `design-approve`) are
  pi-extension-shell-03b (M2b).
- Hook behavior (session recap injection, send interception, AGENTS.md sync)
  is hooks-auto-onboarding-04 (M3); M2a ships stub-free manifest entries only.
- No MCP, no Node.js, no TS bridge.

## Impact

- New `packages/pi-package/` tree; depends on M0/M1.
- Installed locally via `pi install ./packages/pi-package` for testing.

**Done when:** the core lifecycle — init → add-idea → triage → spec-create →
spec-status(in_progress) → spec-status(done) → next → status — runs manually
via Pi skills with correct state in `.intent/`, zero hand-editing of files.
