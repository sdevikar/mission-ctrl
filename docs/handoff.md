# Handoff Log — Mission Ctrl

> Newest entry first. Append a new entry at the top after every session.
> Never delete old entries. See `AGENTS.md` for the entry format.

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
