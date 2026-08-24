# Mission Ctrl — Build Kanban (Ship v0.1: Pure Python Core + Pi Extension)

Goal: dogfoodable end-to-end loop in Pi, shortest path. One language, no bridge, no Claude plugin, no MCP, no LLM-in-core.

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

- [ ] Scaffold `packages/core` as `mission_ctrl_core` (Python, pyproject.toml, pytest)
- [ ] pydantic models: mission, mvp, constraints, backlog, specs, meta
- [ ] Validation layer with clear field-level error formatting
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
- [ ] Git read utility: `git log` since timestamp (read-only, no writes)
- [ ] Skip alignment/design as LLM modules — Pi supplies structured input instead
- [ ] Unit tests: planner never suggests blocked specs; recap correct on all 3 fixtures

**Done when:** `suggest_next()` and `generate_recap()` produce correct output against fixtures with zero network calls.

---

## M2 — Pi Extension Shell (10 skills, direct import — no bridge milestone needed)

- [ ] Scaffold `packages/pi-package` (Python, pyproject.toml, depends on `mission_ctrl_core`)
- [ ] `extension.py`: manifest registering hooks + 10 skills
- [ ] `intent:init` — creates `.intent/`, copies schemas, templates, `INTENT_CREATED`
- [ ] `intent:recap` — on-demand recap (session hook auto-injects; this is the user-invoked form)
- [ ] `intent:add-idea`
- [ ] `intent:triage` (takes Pi-supplied alignment verdict)
- [ ] `intent:spec-create` (idea → spec node) — **fixes core-loop gap**
- [ ] `intent:spec-status` (lifecycle transitions) — **fixes core-loop gap**
- [ ] `intent:design-propose` (takes Pi-supplied digest text)
- [ ] `intent:design-approve`
- [ ] `intent:next`
- [ ] `intent:status`
- [ ] Local install test: `pi install ./packages/pi-package`

**Done when:** full lifecycle — init → add-idea → triage → spec-create → design-propose → design-approve → spec-status(done) → status — runs manually via Pi skills, state correct in `.intent/`.

---

## M3 — Hooks & Auto-Onboarding

- [ ] `on_session_start` hook: detect `.intent/` presence, last session gap, verbosity tier
- [ ] Inject recap before user's first message
- [ ] Append `SESSION_STARTED` event
- [ ] `on_before_send` hook: hardcoded pattern list for implementation-intent detection
- [ ] `on_before_send`: redirect to backlog-add / triage / design-propose depending on state
- [ ] `on_before_send`: one-phrase override to bypass (avoid productivity blocker)
- [ ] Post-skill hook: regenerate `AGENTS.md` after any `.intent/` write
- [ ] AGENTS.md template + snapshot tests

**Done when:** opening a project with `.intent/` auto-shows recap; saying "implement X" gets intercepted correctly; any skill write updates `AGENTS.md` within 1s.

---

## M4 — Dogfood & Ship v0.1

- [ ] Run this exact project (mission-ctrl) through its own workflow in Pi for one real week
- [ ] Fix whatever breaks, especially `on_before_send` false positives
- [ ] README with install + quickstart (`pi install npm:@mission-ctrl/pi-package` — packaging still npm-distributed even though pure Python inside; confirm this works or switch to PyPI distribution)
- [ ] Tag `v0.1.0`, publish `mission_ctrl_core` + `mission_ctrl_pi` to PyPI

**Done when:** you personally use it in Pi for a week without hand-editing `.intent/` files.

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

## Note: Distribution Mechanism Needs a Decision

Original Pi docs assumed npm distribution (`pi install npm:@mission-ctrl/pi-package`) even for what's now a pure-Python package. Confirm whether Pi's install mechanism requires an npm wrapper regardless of implementation language, or whether PyPI/pip distribution is natively supported. This changes packaging in M4 — flag before Phase 5 polish work starts.
