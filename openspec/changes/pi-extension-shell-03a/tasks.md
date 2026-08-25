# Tasks: Pi Extension Shell — Core Loop (M2a) — pi-extension-shell-03a

## Prerequisite: Distribution Decision
- [ ] Confirm Pi install mechanism: does a pure-Python extension require an npm
      wrapper (`pi install npm:@mission-ctrl/pi-package`) or is PyPI/pip native?
- [ ] Record decision in README stub + update packaging accordingly before
      proceeding to skill implementation

## Scaffold
- [ ] `packages/pi-package` (Python, pyproject.toml, depends on `mission_ctrl_core`)
- [ ] `extension.py`: manifest registering hook stubs (on_session_start,
      on_before_send) + 7 core-loop skills
- [ ] `mission_ctrl_pi/schemas.py`: all SkillInput/SkillOutput Pydantic models
      (InitInput, AddIdeaInput, TriageInput, SpecCreateInput, SpecStatusInput,
      NextResult, StatusResult, SkillError)

## Skills
- [ ] `intent:init` — creates `.intent/`, copies schemas + templates, emits `INTENT_CREATED`
- [ ] `intent:add-idea` — appends to backlog.json, emits `BACKLOG_ADDED`
- [ ] `intent:triage` — updates backlog bucket + alignment, emits `BACKLOG_TRIAGE`
- [ ] `intent:spec-create` — idea → spec node (draft), emits `SPEC_CREATED`
- [ ] `intent:spec-status` — M2a state machine only (draft/in_progress/done/blocked);
      raises SkillError(ILLEGAL_TRANSITION) for design-gate states
- [ ] `intent:next` — read-only; returns planner NextResult
- [ ] `intent:status` — read-only; returns StatusResult

## Tests & Install
- [ ] Unit tests: all skill I/O schemas validated against design.md contracts
- [ ] Skill tests: transition legality (M2a states), illegal transition rejection,
      read-only skills leave `.intent/` untouched
- [ ] Local install test: `pi install ./packages/pi-package`
- [ ] E2E lifecycle script: init → add-idea → triage → spec-create →
      spec-status(in_progress) → spec-status(done) → next → status,
      asserting `.intent/` state at each step
