# Tasks: Core Foundation (M0) — core-foundation-01

## Scaffold
- [ ] `packages/core` as `mission_ctrl_core` (pyproject.toml, pytest config, local editable install)

## Models & validation
- [ ] Pydantic models: mission, mvp, constraints, backlog, specs, meta event
- [ ] Validation layer with field-level error formatting (file → index → field → value)
- [ ] Unit tests: 100% model field coverage

## Stores
- [ ] `MissionStore`, `MvpStore`, `ConstraintsStore` (read/write/next_id)
- [ ] `BacklogStore` (add/update/get/next_id/search)
- [ ] `SpecStore` (add/update/get/next_id/validate_no_cycles)
- [ ] `MetaStore` (append/read_since/read_all/next_id)
- [ ] `IntentStore` orchestrator: `init()`, `get_current_intent()`, `validate_all()`
- [ ] `EventBuilder`: all v1 event types incl. `SPEC_CREATED`, `SPEC_STATUS_UPDATED`
- [ ] Store I/O tests: all CRUD ops via tmp_path fixtures

## Shared fixtures
- [ ] `tests/fixtures/empty-project`
- [ ] `tests/fixtures/mid-flight` (partial lifecycle state, some events, git history)
- [ ] `tests/fixtures/complex-graph` (multiple dependency chains, blocked and done specs, cycle-free)
