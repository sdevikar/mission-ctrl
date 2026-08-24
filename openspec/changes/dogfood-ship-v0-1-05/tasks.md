# Tasks: Dogfood & Ship v0.1 (M4) — dogfood-ship-v0-1-05

## Prerequisite: distribution decision
- [ ] Confirm Pi install mechanism for pure-Python packages (npm wrapper required vs native PyPI/pip)
- [ ] Record decision in README + update packaging accordingly

## Dogfood (one real week)
- [ ] Set up mission-ctrl's own `.intent/` via `intent:init` in this repo
- [ ] Run daily work (including this roadmap's remaining follow-ups) through the skills
- [ ] Track breakages; triage fixes as new OpenSpec changes
- [ ] Verify zero hand-edits of `.intent/` during the week

## Fixes
- [ ] Reduce `on_before_send` false positives (tune hardcoded pattern list)
- [ ] Fix planner/recap issues surfaced by dogfooding

## Release
- [ ] README: install + quickstart (must match final packaging shape)
- [ ] CI: GitHub Actions — test → build → publish on `v*` tag
- [ ] Tag `v0.1.0`
- [ ] Publish `mission_ctrl_core` + `mission_ctrl_pi`
