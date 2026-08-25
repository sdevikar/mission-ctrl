# Tasks: Pi Extension Shell — Design Gate (M2b) — pi-extension-shell-03b

## Schemas
- [ ] Add to `mission_ctrl_pi/schemas.py`: RecapInput, DesignProposeInput,
      DesignApproveInput, DesignProposeResult, DesignApproveResult (import
      RecapResult from mission_ctrl_core — do not redefine)

## Skills
- [ ] `intent:recap` — on-demand recap; accepts optional verbosity override;
      returns RecapResult from mission_ctrl_core.logic.recap
- [ ] `intent:design-propose` — spec draft → design_proposed; validates
      spec is in draft; digest min 10 chars; emits `DESIGN_PROPOSED`
- [ ] `intent:design-approve` — design_proposed → design_approved (approved)
      or draft (rejected); notes required on reject; emits `DESIGN_APPROVED`
      or `DESIGN_REJECTED`

## State Machine Extension
- [ ] Update `intent:spec-status` (from M2a) to permit
      `design_approved → in_progress` transition now that design-gate states
      exist in the store

## Tests
- [ ] Skill tests: design-propose rejects non-draft specs; design-approve
      rejects missing notes on rejection; recap returns correct RecapResult
      on all 3 fixtures at all verbosity tiers
- [ ] E2E lifecycle script (full): init → add-idea → triage → spec-create →
      design-propose → design-approve → spec-status(in_progress) →
      spec-status(done) → status, asserting `.intent/` state at each step
- [ ] Test: spec-status still rejects illegal transitions end-to-end
