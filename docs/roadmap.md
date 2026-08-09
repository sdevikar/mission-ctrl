# Mission Ctrl — Roadmap
## Ship v0.1: Pure Python Core + Pi Extension
Status: current source of truth. Supersedes `mission-ctrl-technical-roadmap.md` and the
phase-6/7 rollout in `mission-ctrl-pi-package.md` (both deleted).

---

## Backlog (explicitly not v1)

- Claude Code plugin — needs a Node↔Python bridge or a TS port of core; not scheduled (see architecture.md §6)
- MCP visual spec graph server
- MCP dashboard server
- `backlog.merge`, `backlog.archive`, `intent.update` skills
- Git commit auto-inference (`GIT_COMMIT_ASSOCIATED`)
- Schema/model versioning and migration tooling
- Configurable `on_before_send` pattern matching (v1 ships hardcoded)

---

## M0 — Core Foundation (Python, agent-agnostic)

- [ ] Scaffold `packages/core` as `mission_ctrl_core` (pyproject.toml, pytest)
- [ ] pydantic models: mission, mvp, constraints, backlog, specs, meta
- [ ] `MissionStore`, `MvpStore`, `ConstraintsStore` (read/write/next_id)
- [ ] `BacklogStore` (add/update/get/next_id/search)
- [ ] `SpecStore` (add/update/get/next_id/**validate_no_cycles**)
- [ ] `MetaStore` (append/read_since/read_all/next_id)
- [ ] `IntentStore` orchestrator: `init()`, `get_current_intent()`, `validate_all()`
- [ ] `EventBuilder`: all v1 event types incl. `SPEC_CREATED`, `SPEC_STATUS_UPDATED`
- [ ] Unit tests: 100% model field coverage
- [ ] 3 fixture repos: empty-project, mid-flight, complex-graph

**Done when:** can init, read, write, validate all 5 files + meta.jsonl from a script, no agent involved.

---

## M1 — Logic Layer (No LLM calls)

- [ ] `planner.py`: `suggest_next()` — MVP-critical first, unblocked, fewest deps, continuity
- [ ] `recap.py`: `generate_recap()` — mission, MVP %, last focus, changes since, next suggestion
- [ ] Git read utility: `git log` since timestamp (read-only)
- [ ] Unit tests: planner never suggests blocked specs; recap correct on all 3 fixtures

**Done when:** `suggest_next()` and `generate_recap()` produce correct output against fixtures with zero network calls.

---

## M2 — Pi Extension Shell (9 skills, direct import)

- [ ] Scaffold `packages/pi-package` (depends on `mission_ctrl_core`)
- [ ] `extension.py`: manifest registering hooks + 9 skills
- [ ] `intent:init`, `intent:add-idea`, `intent:triage`
- [ ] `intent:spec-create`, `intent:spec-status`
- [ ] `intent:design-propose`, `intent:design-approve`
- [ ] `intent:next`, `intent:status`
- [ ] Local install test: `pi install ./packages/pi-package`

**Done when:** full lifecycle — init → add-idea → triage → spec-create → design-propose → design-approve → spec-status(done) → status — runs manually, state correct in `.intent/`.

---

## M3 — Hooks & Auto-Onboarding

- [ ] `on_session_start`: gap detection, adaptive verbosity, recap injection, `SESSION_STARTED` event
- [ ] `on_before_send`: hardcoded pattern list, redirect to backlog/design steps, one-phrase override
- [ ] Post-skill hook: regenerate `AGENTS.md` after any `.intent/` write
- [ ] AGENTS.md template + snapshot tests

**Done when:** opening a project auto-shows recap; "implement X" gets intercepted correctly; `AGENTS.md` updates within 1s of any write.

---

## M4 — Dogfood & Ship v0.1

- [ ] Run this exact project through its own workflow in Pi for one real week
- [ ] Fix what breaks, especially `on_before_send` false positives
- [ ] Resolve distribution mechanism (see note below) before publishing
- [ ] README with install + quickstart
- [ ] Tag `v0.1.0`, publish `mission_ctrl_core` + `mission_ctrl_pi`

**Done when:** used in Pi for a week without hand-editing `.intent/` files.

---

## Testing Strategy

| Category | Coverage target | Tools |
|---|---|---|
| Model validation | 100% of fields | pydantic + pytest |
| Business rules | All status transitions, cycle detection | pytest |
| Store I/O | All CRUD ops | pytest + tmp_path fixtures |
| Recap generation | All verbosity tiers | pytest + fixtures |
| Planner logic | Dependency graphs | pytest + graph fixtures |
| Hook behavior | Session gap tiers, `on_before_send` patterns | pytest, temp workspace |
| AGENTS.md sync | Snapshot tests | pytest-snapshot |
| End-to-end | Full lifecycle script on temp repo | pytest |

Fixture repos (`empty-project`, `mid-flight`, `complex-graph`) live in `packages/core/tests/fixtures/` and are the source of truth for all deterministic tests.

---

## Build & Distribution

- Packages: `mission_ctrl_core` (pip), `mission_ctrl_pi` (pip, depends on core)
- CI: GitHub Actions — test → build → publish on `v*` tag push

**Open question — resolve before M4 packaging work:** the original Pi docs assumed npm-style install (`pi install npm:@mission-ctrl/pi-package`) even though the package is now pure Python. Confirm whether Pi's install mechanism requires an npm wrapper regardless of language, or whether native PyPI/pip distribution (`pip install mission-ctrl-pi`) is supported. This decides the M4 packaging shape.

---

## Deferred: Claude Code Plugin

Not scheduled. When it is:
- Decide bridge direction (Node calls into Python core via subprocess, or core gets ported to TS) — see architecture.md §6.
- Skill set, event catalog, and `.intent/` file formats carry over unchanged — those are language-agnostic.
- `CLAUDE.md` sync mirrors `AGENTS.md` sync; same trigger, same content shape, different filename.
- Do not resurrect the old `mission-ctrl-claude-plugin.md` as-is — it assumed a TypeScript core with direct import, which is no longer accurate.
