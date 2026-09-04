# Mission Ctrl — Build Kanban (Ship v0.1: Pure Python Core + Pi Extension)

Goal: dogfoodable end-to-end loop in Pi, shortest path. One language, no bridge, no Claude plugin, no MCP, no LLM-in-core.

---

## OpenSpec Change Index

Lightweight status tracking. Update `Status` as each change is applied and archived.

| Change | Title | Milestone | Status |
|---|---|---|---|
| `core-foundation-01` | Core Foundation | M0 | 📦 Archived |
| `logic-layer-02` | Logic Layer | M1 | 🔲 Planned |
| ~~`pi-extension-shell-03`~~ | ~~Pi Extension Shell~~ | ~~M2~~ | ⚠️ Superseded (split → 03a/03b) |
| `pi-extension-shell-03a` | Pi Extension Shell — Core Loop | M2a | 🔲 Planned |
| `pi-extension-shell-03b` | Pi Extension Shell — Design Gate | M2b | 🔄 In Progress |
| `hooks-auto-onboarding-04` | Hooks & Auto-Onboarding | M3 | 🔲 Planned |
| `dogfood-ship-v0-1-05` | Dogfood & Ship v0.1 | M4 | 🔲 Planned |
| `log-feedback-06` | Feedback Logging Skill | M5-prep | 🔲 Planned |

> **Status key:** 🔲 Planned · 🔄 In Progress · ✅ Applied · 📦 Archived · ⚠️ Superseded

---

## Backlog (not this milestone)

- [ ] Claude Code plugin (Node/TS, or Python-to-Node bridge — decide when scheduled)
- [ ] MCP visual spec graph server
- [ ] MCP dashboard server
- [ ] `backlog.merge`, `backlog.archive`, `intent.update` skills
- [ ] Git commit auto-inference
- [ ] Schema versioning / migration tooling
- [ ] Configurable `on_before_send` pattern matching (v1 ships hardcoded)

---

## M0 — Core Foundation (Python, agent-agnostic)
> OpenSpec: `core-foundation-01` | Status: 📦 Archived (spec synced to openspec/specs/intent-store)

- [x] Scaffold `packages/core` as `mission_ctrl_core` (Python, pyproject.toml, pytest)
- [x] Root pyproject.toml: uv workspace config (members: packages/*), single uv.lock
- [x] pydantic models: mission, mvp, constraints, backlog, specs, meta (with discriminated unions for meta.jsonl)
- [x] Validation layer with clear field-level error formatting
- [x] `MissionStore`, `MvpStore`, `ConstraintsStore` (read/write/next_id)
- [x] `BacklogStore` (add/update/get/next_id/search)
- [x] `SpecStore` (add/update/get/next_id/**validate_no_cycles** via `graphlib.TopologicalSorter`)
- [x] `MetaStore` (append/read_since/read_all/next_id) — append-only; discriminated-union deserialization
- [x] `IntentStore` orchestrator: `init()`, `get_current_intent()`, `validate_all()`
- [x] `EventBuilder`: all v1 event types incl. `SPEC_CREATED`, `SPEC_STATUS_UPDATED`
- [x] Unit tests: 100% model field coverage
- [x] 3 fixture repos: empty-project, mid-flight, complex-graph

**Done when:** can init, read, write, validate all 5 files + meta.jsonl from a script, no agent involved.

---

## M1 — Logic Layer (No LLM calls)
> OpenSpec: `logic-layer-02` | Status: 📦 Archived (spec synced to openspec/specs/intent-logic)

- [x] `planner.py`: `suggest_next()` — MVP-critical first, unblocked, fewest deps, continuity (priority order in design.md)
- [x] `RecapResult` Pydantic model (typed output contract consumed by M2b)
- [x] `recap.py`: `generate_recap()` → `RecapResult` — mission, MVP %, last focus, changes since, next suggestion
- [x] Git read utility: `git log` since timestamp (read-only, no writes; fallback to empty list if no history)
- [x] Skip alignment/design as LLM modules — Pi supplies structured input instead
- [x] Unit tests: planner never suggests blocked specs; recap correct on all 3 fixtures

**Done when:** `suggest_next()` and `generate_recap()` produce correct output against fixtures with zero network calls.

---

## M2a — Pi Extension Shell: Core Loop (7 skills)
> OpenSpec: `pi-extension-shell-03a` | Status: 🔲 Planned
> **Prerequisite:** Resolve Pi distribution mechanism (npm wrapper vs PyPI/pip) before starting

- [ ] Scaffold `packages/pi-package` (Python, pyproject.toml, depends on `mission_ctrl_core`)
- [ ] `mission_ctrl_pi/schemas.py`: all skill input/output Pydantic models
- [ ] `extension.py`: manifest registering hook stubs + 7 core-loop skills
- [ ] `intent:init` — creates `.intent/`, copies schemas, templates, `INTENT_CREATED`
- [ ] `intent:add-idea`
- [ ] `intent:triage` (takes Pi-supplied alignment verdict)
- [ ] `intent:spec-create` (idea → spec node) — **fixes core-loop gap**
- [ ] `intent:spec-status` (M2a state machine: draft/in_progress/done/blocked) — **fixes core-loop gap**
- [ ] `intent:next`
- [ ] `intent:status`
- [ ] Local install test: `pi install ./packages/pi-package`
- [ ] E2E lifecycle: init → add-idea → triage → spec-create → spec-status(done) → next → status

**Done when:** core lifecycle runs manually via Pi skills, correct state in `.intent/`, zero hand-edits.

---

## M2b — Pi Extension Shell: Design Gate (3 skills)
> OpenSpec: `pi-extension-shell-03b` | Status: 🔄 In Progress

- [ ] Add design-gate schemas to `schemas.py` (RecapInput, DesignProposeInput, DesignApproveInput, etc.)
- [ ] `intent:recap` — on-demand recap; optional verbosity override; returns `RecapResult`
- [ ] `intent:design-propose` (takes Pi-supplied digest text)
- [ ] `intent:design-approve` (approve / reject-with-required-notes)
- [ ] Extend `intent:spec-status` to allow `design_approved → in_progress`
- [ ] E2E full lifecycle: init → add-idea → triage → spec-create → design-propose → design-approve → spec-status(done) → status

**Done when:** full lifecycle including design gate runs manually via Pi skills with correct state.

---

## M3 — Hooks & Auto-Onboarding
> OpenSpec: `hooks-auto-onboarding-04` | Status: 🔲 Planned

- [ ] `on_session_start` hook: detect `.intent/` presence; no-op if absent; session-gap → verbosity tier (4 tiers per design.md)
- [ ] Inject recap before user's first message; append `SESSION_STARTED` event
- [ ] `on_before_send` hook: hardcoded pattern list (full-word, case-insensitive)
- [ ] `on_before_send`: redirect to backlog-add / triage / design-propose depending on state
- [ ] `on_before_send`: one-phrase override to bypass (surfaced, never silent)
- [ ] Log interceptions: `INTENT_INTERCEPTED` event to meta.jsonl
- [ ] Log bypasses: `INTENT_BYPASS_USED` event to meta.jsonl
- [ ] Post-skill hook: regenerate `AGENTS.md` after any `.intent/` write (≤1s)
- [ ] Jinja2 AGENTS.md template + sanitization (escape user-supplied fields; reject injection patterns)
- [ ] Snapshot tests for AGENTS.md template output

**Done when:** opening a project with `.intent/` auto-shows recap; "implement X" gets intercepted correctly with event logged; any skill write updates `AGENTS.md` within 1s.

---

## M5-prep — Feedback Logging Skill
> OpenSpec: `log-feedback-06` | Status: 🔲 Planned
> *(Implemented before M4 dogfood week begins)*

- [ ] `FEEDBACK_LOGGED` event type in `EventBuilder`
- [ ] `MetaStore.read_feedback(severity=None)` query helper
- [ ] `intent:log-feedback` skill (category, description, severity, related_spec_id)
- [ ] Unit + integration tests

**Done when:** `intent:log-feedback` writes a correctly structured event; `read_feedback()` filters by severity.

---

## M4 — Dogfood & Ship v0.1
> OpenSpec: `dogfood-ship-v0-1-05` | Status: 🔲 Planned

- [ ] Run this exact project (mission-ctrl) through its own workflow in Pi for one real week
- [ ] Use `intent:log-feedback` to capture every issue during dogfood (not just memory)
- [ ] Triage feedback: fix [blocker] in M4; open new OpenSpec changes for [polish]
- [ ] Fix `on_before_send` false positives using `INTENT_INTERCEPTED` event data
- [ ] Fix planner/recap issues surfaced by [blocker]-tagged feedback
- [ ] README with install + quickstart
- [ ] CHANGELOG.md (v0.1.0 entry)
- [ ] CI: lint → test → build → publish; PyPI Trusted Publishing (OIDC); pip-audit
- [ ] Clean-install smoke test from TestPyPI
- [ ] Tag `v0.1.0`, publish `mission_ctrl_core` + `mission_ctrl_pi` to PyPI

**Done when:** personally used in Pi for a week without hand-editing `.intent/` files, and v0.1.0 is tagged and published.

---

## Explicit Non-Goals This Milestone

- No Claude Code plugin
- No MCP servers
- No LLM calls inside core
- No auto git-commit association
- No backlog merge/archive
- No configurable `on_before_send` matching (hardcoded list only)
- No Node.js anywhere in the v1 dependency graph

---

## Note: Distribution Mechanism Needs a Decision (Before M2a)

Original Pi docs assumed npm distribution (`pi install npm:@mission-ctrl/pi-package`) even for what's now a pure-Python package. Confirm whether Pi's install mechanism requires an npm wrapper regardless of implementation language, or whether PyPI/pip distribution is natively supported. **This must be resolved before M2a starts** — `pi install ./packages/pi-package` is M2a's done-when criterion.


