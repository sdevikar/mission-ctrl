# Tasks: Core Foundation (M0) — core-foundation-01

## Scaffold
- [x] `packages/core` as `mission_ctrl_core` (pyproject.toml, pytest config, local editable install)

## Models & validation
- [x] Pydantic models: mission, mvp, constraints, backlog, specs, meta event
- [x] Validation layer with field-level error formatting (file → index → field → value)
- [x] Unit tests: 100% model field coverage

## Stores
- [x] `MissionStore`, `MvpStore`, `ConstraintsStore` (read/write/next_id)
- [x] `BacklogStore` (add/update/get/next_id/search)
- [x] `SpecStore` (add/update/get/next_id/validate_no_cycles)
- [x] `MetaStore` (append/read_since/read_all/next_id)
- [x] `IntentStore` orchestrator: `init()`, `get_current_intent()`, `validate_all()`
- [x] `EventBuilder`: all v1 event types incl. `SPEC_CREATED`, `SPEC_STATUS_UPDATED`
- [x] Store I/O tests: all CRUD ops via tmp_path fixtures

## Shared fixtures
- [x] `tests/fixtures/empty-project`
- [x] `tests/fixtures/mid-flight` (partial lifecycle state, some events)
- [x] `tests/fixtures/complex-graph` (multiple dependency chains, blocked and done specs, cycle-free)
