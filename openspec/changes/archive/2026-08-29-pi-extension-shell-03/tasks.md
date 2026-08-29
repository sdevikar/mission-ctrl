# Tasks: Pi Extension Shell (M2) — pi-extension-shell-03

## Scaffold
- [ ] `packages/pi-package` (Python, pyproject.toml, depends on `mission_ctrl_core`)
- [ ] `extension.py`: manifest registering hooks (stubs) + 10 skills

## Skills
- [ ] `intent:init` — creates `.intent/`, copies schemas, templates, `INTENT_CREATED`
- [ ] `intent:recap` — on-demand recap (session hook auto-injects; this is the user-invoked form)
- [ ] `intent:add-idea`
- [ ] `intent:triage` (takes Pi-supplied alignment verdict)
- [ ] `intent:spec-create` (idea → spec node) — fixes core-loop gap
- [ ] `intent:spec-status` (lifecycle transitions; rejects illegal)
- [ ] `intent:design-propose` (takes Pi-supplied digest text)
- [ ] `intent:design-approve` (approve / reject-with-notes)
- [ ] `intent:next`
- [ ] `intent:status`

## Tests & install
- [ ] Skill tests: transition legality, store-mediated writes, read-only skills leave `.intent/` untouched
- [ ] Local install test: `pi install ./packages/pi-package`
- [ ] E2E lifecycle script: init → add-idea → triage → spec-create → design-propose → design-approve → spec-status(done) → status, asserting `.intent/` state at each step
