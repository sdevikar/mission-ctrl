# Proposal: Pi Extension Shell (M2) — ⚠️ SUPERSEDED

> **This proposal has been split into two separate changes:**
> - **pi-extension-shell-03a** — Core Loop (7 skills: init, add-idea, triage,
>   spec-create, spec-status, next, status)
> - **pi-extension-shell-03b** — Design Gate (3 skills: recap, design-propose,
>   design-approve)
>
> This file is retained for historical reference. Do not implement from this
> document — use 03a and 03b instead.

---

## Why

The intent loop (add-idea → triage → spec → design gate → status → next) only
exists for users through Pi skills. M2 is the surface that makes the M0/M1 core
usable inside the agent workflow: one Python extension, direct in-process
import of `mission_ctrl_core`, no bridge, no Node.

## What Changes

- New package `packages/pi-package` (Python, pyproject.toml, depends on
  `mission_ctrl_core`).
- `extension.py` manifest registering hooks (stubs for M3) + 10 skills:
  `intent:init`, `intent:recap`, `intent:add-idea`, `intent:triage`,
  `intent:spec-create`, `intent:spec-status`, `intent:design-propose`,
  `intent:design-approve`, `intent:next`, `intent:status`.
- `spec-create` and `spec-status` close the core-loop gap: ideas now have a
  path into specs, and specs can reach `done`.
- Triage and design-propose take Pi-supplied structured inputs (alignment
  verdict, digest text) — core only validates and stores.

## Non-goals

- Hook behavior (session recap injection, send interception, AGENTS.md sync)
  is change 04; M2 ships stub-free manifest entries only.
- No status-transition legality relaxed: transitions follow the spec lifecycle
  exactly (draft → design_proposed → design_approved → in_progress → done).
- No MCP, no Node.js, no TS bridge.

## Impact

- New `packages/pi-package/` tree; depends on M0/M1.
- Installed locally via `pi install ./packages/pi-package` for testing.

**Done when:** the full lifecycle — init → add-idea → triage → spec-create →
design-propose → design-approve → spec-status(done) → status — runs manually
via Pi skills with correct state in `.intent/`.
