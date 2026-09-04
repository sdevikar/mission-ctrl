# Tasks: Pi Extension Shell — Core Loop (M2a) — pi-extension-shell-03a

## Prerequisite: Distribution Decision
- [x] Confirm Pi install mechanism: does a pure-Python extension require an npm
      wrapper (`pi install npm:@mission-ctrl/pi-package`) or is PyPI/pip native?
- [x] Record decision in README stub + update packaging accordingly before
      proceeding to skill implementation

## Scaffold
- [x] `packages/pi-package` (Python, pyproject.toml, depends on `mission_ctrl_core`)
- [x] `extension.py`: manifest registering hook stubs (on_session_start,
      on_before_send) + 7 core-loop skills
- [x] `mission_ctrl_pi/schemas.py`: all SkillInput/SkillOutput Pydantic models
      (InitInput, AddIdeaInput, TriageInput, SpecCreateInput, SpecStatusInput,
      NextResult, StatusResult, SkillError)

## Skills
- [x] `intent:init` — creates `.intent/`, copies schemas + templates, emits `INTENT_CREATED`
- [x] `intent:add-idea` — appends to backlog.json, emits `BACKLOG_ADDED`
- [x] `intent:triage` — updates backlog bucket + alignment, emits `BACKLOG_TRIAGE`
- [x] `intent:spec-create` — idea → spec node (draft), emits `SPEC_CREATED`
- [x] `intent:spec-status` — M2a state machine only (draft/in_progress/done/blocked);
      raises SkillError(ILLEGAL_TRANSITION) for design-gate states
- [x] `intent:next` — read-only; returns planner NextResult
- [x] `intent:status` — read-only; returns StatusResult

## Tests & Install
- [x] Unit tests: all skill I/O schemas validated against design.md contracts
- [x] Skill tests: transition legality (M2a states), illegal transition rejection,
      read-only skills leave `.intent/` untouched
- [x] Local install test: `pi install ./packages/pi-package`
- [x] E2E lifecycle script: init → add-idea → triage → spec-create →
      spec-status(in_progress) → spec-status(done) → next → status,
      asserting `.intent/` state at each step
