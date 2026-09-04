# Handoff Log — Mission Ctrl

> Newest entry first. Append a new entry at the top after every session.
> Never delete old entries. See `AGENTS.md` for the entry format.

---

## [2026-09-04] Session Summary — M2b design-gate skills implemented + spec drift fixed

**OpenSpec change:** `pi-extension-shell-03b` (M2b) — in progress, not archived.

- Previous session's uncommitted work verified: `recap.py`, `design_propose.py`,
  `design_approve.py`, schemas, `spec-status` extension, manifest wiring,
  `EventBuilder.design_proposed/design_approved` — all present, 19/19 tests
  in `test_design_gate.py` pass, 98 pass repo-wide, ruff clean (fixed 12 lint
  errors + 1 format drift in the new test file).
- Spec fix (per original intent in `docs/design.md` §4 + shipped M0 core):
  reject emits `DESIGN_APPROVED` with `approval=false` — removed the
  `DESIGN_REJECTED` drift from 03b `proposal.md`, `design.md`, `tasks.md`.
  Implementation already matched; spec was updated, not code.
- `tasks.md`: schemas, 3 skills, state-machine ext, illegal-transition test
  checked off. Still open: recap on all 3 fixtures × verbosity tiers, full
  E2E lifecycle script (init → … → design-approve → done → status).
- Kanban: 03b → 🔄 In Progress. Committed + pushed (see log).

**Next:** write the full E2E lifecycle test + fixture-matrix recap tests,
then archive 03b.

## [2026-09-04] Session Summary — logic-layer-02 complete + pi-extension-shell-03a complete

**OpenSpec changes:** `logic-layer-02` (M1) — **all tasks complete**; `pi-extension-shell-03a` (M2a) — **all tasks complete**.

### logic-layer-02 (M1) — shipped
- `planner.py`: `suggest_next()` — ranks by MVP-critical → unblocked → fewest deps → continuity
- `RecapResult` Pydantic model as typed output contract
- `recap.py`: `generate_recap()` → `RecapResult` (mission, MVP %, last focus, changes since, next suggestion)
- `gitutil.py`: `git_log_since()` read-only git log utility (fallback to `[]` if no history)
- Unit tests: planner never suggests blocked specs; recap correct on all 3 fixtures; 46+ tests pass, ruff clean
- Change archived to `openspec/changes/archive/`; spec synced to `openspec/specs/intent-logic/`

### pi-extension-shell-03a (M2a) — shipped
- Scaffolded `packages/pi-package` as `mission_ctrl_pi` (Python, depends on `mission_ctrl_core`)
- `schemas.py`: all SkillInput/SkillOutput Pydantic models (InitInput, AddIdeaInput, TriageInput, SpecCreateInput, SpecStatusInput, NextResult, StatusResult, SkillError)
- `extension.py`: manifest with `on_session_start` + `on_before_send` hook stubs + 7 core-loop skills
- All 7 skills implemented: `intent:init`, `intent:add-idea`, `intent:triage`, `intent:spec-create`, `intent:spec-status`, `intent:next`, `intent:status`
- `intent:spec-status` enforces M2a state machine only; raises `SkillError(ILLEGAL_TRANSITION)` for design-gate states
- Tests: schema validation, transition legality, E2E lifecycle — **79 tests pass total**
- `.pi/settings.json`: extension wired to `mission_ctrl_pi.extension`
- Distribution: pure-Python local install via `pip install -e ./packages/pi-package`

**Key decisions:**
- Skills use `IntentStore` directly (no bridge, no subprocess, no LLM in core)
- `SkillError` is returned (not raised) for user-visible errors; Python exceptions propagate for bugs
- `intent:spec-status` guards design-gate transitions explicitly, making M2b purely additive
- Distribution confirmed as pure-Python PyPI/pip (no npm wrapper needed)

**Next:** Start `pi-extension-shell-03b` (M2b) — design-gate skills (intent:recap, intent:design-propose, intent:design-approve) + extend spec-status for design_approved → in_progress.

## [2026-08-29] Session Summary — core-foundation-01 stores + fixtures

**OpenSpec change:** `core-foundation-01` (M0) — now **all 14 tasks complete**.

- Implemented `packages/core/mission_ctrl_core/stores/`:
  - `base.py` — generic `Store` (single-doc JSON read/write), `atomic_write_json`, `utcnow`.
  - `data_stores.py` — `MissionStore`, `MvpStore`, `ConstraintsStore`, `BacklogStore`
    (add/update/get/search/next_id), `SpecStore` (add/update/set_status/
    `validate_no_cycles` via `graphlib.TopologicalSorter`; enforces in_progress
    dep-gating + unknown-dep rejection), append-only `MetaStore` (append/
    read_all/read_since/next_id, JSONL per line, duplicate-id-safe).
  - `events.py` — `EventBuilder` for all 8 v1 event types incl. `SPEC_CREATED`,
    `SPEC_STATUS_UPDATED`; auto-assigns `event_id`.
  - `intent.py` — `IntentStore` orchestrator: `init()`, `get_current_intent()`
    (returns `CurrentIntent`: current in-progress spec + design-approved ready
    next-ups), `validate_all()` (returns list of all error strings).
- Errors raise `MissionCtrlError` with `file: field: message` (reuses
  `render_validation_error`).
- 3 shared fixtures generated via committed `tests/generate_fixtures.py`
  (empty-project, mid-flight [in_progress+draft specs, 3 events], complex-graph
  [multiple chains, done+blocked specs, cycle-free]) — each re-validated to pass
  `validate_all()`.
- Tests: `tests/test_stores.py` (CRUD + cycle/gating/malformed/dup coverage) +
  `tests/test_fixtures.py` (all 3 fixtures read back through the stores). **46
  tests pass; `ruff check` clean.**

**Key decisions:**
- Generic `Store[ModelT]` base keeps the five JSON files uniform; `MetaStore`
  is separate (JSONL, append-only).
- `IntentStore` roots at `<root>/.intent/`, owns all file stores + `EventBuilder`
  (linked_intent derived from current mission/mvp/constraints versions).
- Fixtures generated by a committed script (deterministic, regeneratable) rather
  than hand-written JSON.

**Next:** archive `core-foundation-01` + sync its delta specs → `openspec/specs/`,
then start `logic-layer-02` (planner + recap).

## Status — 2026-08-29

### Active OpenSpec changes (progress)
- ~~`core-foundation-01`~~ — **✅ complete & archived** to `openspec/changes/archive/2026-08-29-core-foundation-01`; delta spec synced to `openspec/specs/intent-store/spec.md` (first main spec). (implemented this session; `openspec status` = all artifacts done). Implementation lives in `packages/core/mission_ctrl_core/stores/` (`Store` base, per-type stores, `SpecStore.validate_no_cycles` via `graphlib`, `MetaStore` append-only JSONL, `IntentStore` orchestrator, `EventBuilder`) + 3 fixtures under `tests/fixtures/`. 46 tests pass, ruff clean. **Next: archive change + sync delta specs → main, then start `logic-layer-02`.**
- `logic-layer-02` — 0/9 (not started; **next implementation target**)
- `pi-extension-shell-03a` / `03b` — not started
- `hooks-auto-onboarding-04` — 0/16
- `dogfood-ship-v0-1-05` — 0/17
- `log-feedback-06` — 0/11 (in-progress status)

### Archived
- ✅ `core-foundation-01` — completed & archived to `openspec/changes/archive/2026-08-29-core-foundation-01`; spec synced to `openspec/specs/intent-store/spec.md`.
- ✅ `pi-extension-shell-03` — completed & archived to `openspec/changes/archive/2026-08-29-pi-extension-shell-03` (superseded by split 03a/03b; its delta specs not synced to main specs since 03a/03b specs replace them).

## [2026-08-28 22:35] Session Summary — Scaffold core-foundation-01

**OpenSpec change in progress:** `core-foundation-01` (M0 — Core Foundation)
**Tasks completed this session:**
- ✅ Updated `AGENTS.md` — condensed from 160→72 lines; added greenfield status,
  uv workspaces toolchain, and the `.pi/skills/` vs `mission_ctrl_pi` distinction
- ✅ Scaffolded `packages/core` as `mission_ctrl_core` (pyproject.toml,
  `__init__.py`, tests package, pytest config)
- ✅ Root `pyproject.toml` — uv workspace with `members = ["packages/*"]`,
  dev dependency group (pytest, ruff)
- ✅ Verified: `uv sync --all-packages` installs all 6 packages (pydantic,
  pydantic-core, typing-extensions, typing-inspection, annotated-types,
  mission_ctrl_core); `uv run pytest` collects successfully; `uv run ruff check`
  passes clean
- ✅ Committed both changes atomically with format `<change-id>: <description>`

**Key decisions made:**
- Using `hatchling` as the build backend for the core package (simple, no
  extra config needed for a pure-Python package)
- Root project uses `package = false` so it's not installed as a package
  itself — only workspace members are
- Added pytest/ruff as root dev dependencies (via `[dependency-groups]`)
  so `uv sync --all-packages` brings up the full toolchain

**Next session should start with:**
- The first unchecked task in `core-foundation-01/tasks.md` under "Models &
  validation" — Pydantic models for mission, mvp, constraints, backlog, specs,
  meta event (using the data model reference in `docs/design.md` §3–4 and
  live samples in `docs/examples/`)

---

## [2026-08-24 22:43] Session Summary — Proposal Review & Restructure

**OpenSpec change in progress:** N/A — this session was meta/planning work  
**What we did:** Reviewed all 5 existing OpenSpec proposals with web-informed
analysis, then applied all agreed recommendations.

**Tasks completed this session:**
- Reviewed `core-foundation-01` through `dogfood-ship-v0-1-05` against industry patterns (event sourcing, monorepo tooling, plugin architecture, AGENTS.md best practices, dogfood methodology)
- Split `pi-extension-shell-03` → `03a` (7 core-loop skills) + `03b` (3 design-gate skills)
- Created `design.md` for both 03a and 03b with full skill I/O schemas and state machine diagrams
- Created `hooks-auto-onboarding-04/design.md` with session gap tiers, redirect logic, sanitization requirement
- Added `INTENT_INTERCEPTED` / `INTENT_BYPASS_USED` event logging to hooks tasks
- Created new `log-feedback-06` proposal: `intent:log-feedback` skill for structured dogfood feedback
- Moved distribution decision from M4 to M2a prerequisite
- Updated `dogfood-ship-v0-1-05/tasks.md` with full launch checklist (CHANGELOG, PyPI OIDC, pip-audit, smoke test)
- Populated `openspec/config.yaml` with project context, per-artifact rules, and operation guidance
- Rewrote `docs/kanban.md` with OpenSpec Change Index (status table) and updated all milestone sections
- Created `AGENTS.md` (this project's agent context file)
- Created `docs/handoff.md` (this file)
- Deleted `todo.md` (its one item — skill I/O contracts — is now captured in `pi-extension-shell-03a/design.md` and `pi-extension-shell-03b/design.md`)

**Key decisions made:**
- **M2 split (03a/03b):** Core-loop skills first so there's a usable product before the design-gate is built. 03b depends on 03a.
- **log-feedback-06 as a separate change (not a task in M4):** Makes dogfood feedback a first-class skill with structured data, so M4 fix prioritization is evidence-based not anecdotal. Implemented before M4 dogfood week.
- **Distribution decision urgency moved to M2a:** `pi install ./packages/pi-package` is M2a's done-when criterion — this must be resolved before M2a starts, not in M4.
- **uv workspaces:** Recommended for monorepo wiring (root pyproject.toml + single uv.lock). Noted in M0 kanban and config.yaml context.
- **Session gap tiers (M3):** Four tiers defined in design.md — skip (<1h), brief (1–8h), standard (8–48h), full (>48h). Thresholds are constants in source, not config.
- **AGENTS.md sanitization:** User-supplied fields (spec titles, descriptions, alignment verdicts) must be escaped before Jinja2 template renders to prevent prompt injection.
- **Spec state machine (M2a vs M2b):** M2a supports `draft → in_progress → done → blocked` only. M2b extends to include design-gate states. `spec-status` in M2a raises `SkillError(ILLEGAL_TRANSITION)` for design-gate states.

**Assumptions:**
- `graphlib.TopologicalSorter` (Python 3.9+ stdlib) is the implementation for `validate_no_cycles` — no extra dependency.
- Pydantic v2 discriminated unions are used for `meta.jsonl` multi-event-type deserialization.
- `RecapResult` is defined in `mission_ctrl_core` and imported (not redefined) in `mission_ctrl_pi`.
- All skill schemas live in a single `mission_ctrl_pi/schemas.py` module.

**Noticed / Deferred (not in scope but worth tracking):**
- `logic-layer-02` still has no `design.md`. The planner ranking priority order (MVP-critical > unblocked > fewest deps > continuity > stable sort by spec_id) was defined in the review artifact but not yet written into a `design.md` file for that change.
- M0 `core-foundation-01` design.md could mention the discriminated union pattern explicitly — currently only in kanban notes.

**Next session should start with:**
- Resolve the Pi distribution mechanism question (npm wrapper vs native PyPI/pip) — this unblocks M2a
- Then: begin `core-foundation-01` — scaffold `packages/core` with uv workspace config
