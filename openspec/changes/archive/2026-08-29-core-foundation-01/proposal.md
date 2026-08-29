# Proposal: Core Foundation (M0)

## Why

Nothing exists yet. Every later milestone (planner/recap logic, Pi skills, hooks)
depends on a deterministic, network-free Python data layer that owns the `.intent/`
artifacts (mission, mvp, constraints, backlog, specs, meta.jsonl) with pydantic
validation and canonical event logging. Building it first, with zero agent
involvement, keeps the whole system testable before any LLM is in the loop.

## What Changes

- New package `packages/core` (`mission_ctrl_core`, pyproject.toml, pytest).
- Pydantic models for all 6 artifact types + field-level validation errors.
- Stores: `MissionStore`, `MvpStore`, `ConstraintsStore`, `BacklogStore`,
  `SpecStore` (with `validate_no_cycles`), `MetaStore` (append/read_since).
- `IntentStore` orchestrator: `init()`, `get_current_intent()`, `validate_all()`.
- `EventBuilder` for all v1 event types (incl. `SPEC_CREATED`,
  `SPEC_STATUS_UPDATED`).
- 3 fixture repos (empty-project, mid-flight, complex-graph) as the source of
  truth for all deterministic tests.

## Non-goals

- No recommender/recap logic (that is change logic-layer-02).
- No Pi package, no skills, no hooks.
- No LLM calls, no network access, no subprocesses — core is pure library code.
- No schema versioning/migration tooling (explicitly deferred in kanban backlog).

## Impact

- New `packages/core/` tree; no existing code affected (greenfield).
- Data contracts defined in `docs/design.md` §3–4 and `docs/examples/`.

**Done when:** a script can init, read, write, and validate all 5 files +
meta.jsonl with no agent involved.
