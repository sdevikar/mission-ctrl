# Tasks: Dogfood & Ship v0.1 (M4) — dogfood-ship-v0-1-05

## Prerequisite: log-feedback skill
- [ ] Confirm log-feedback-06 (intent:log-feedback skill) is applied and
      installed — required for structured dogfood issue capture

## Dogfood (one real week)
- [ ] Set up mission-ctrl's own `.intent/` via `intent:init` in this repo
- [ ] Run daily work through the skills using `intent:log-feedback` to capture
      every issue (category, description, severity) as it happens
- [ ] Verify zero hand-edits of `.intent/` during the week

## Fixes (evidence-based)
- [ ] Run `MetaStore.read_feedback(severity="blocker")` at end of dogfood week
- [ ] Triage all dogfood issues: tag as [blocker | polish | backlog]
- [ ] Fix only [blocker] items in M4; open new OpenSpec changes for [polish] items
- [ ] Reduce `on_before_send` false positives: tune hardcoded pattern list using
      `INTENT_INTERCEPTED` events from meta.jsonl (not anecdotal)
- [ ] Fix planner/recap issues surfaced by [blocker]-tagged feedback events

## Release
- [ ] README: install + quickstart (must match final packaging shape)
- [ ] CHANGELOG.md: at minimum a v0.1.0 entry summarizing what ships
- [ ] CI: GitHub Actions pipeline — lint (ruff) → test (pytest) → build → publish
- [ ] CI: PyPI Trusted Publishing (OIDC) — no long-lived API tokens in secrets
- [ ] CI: `pip-audit` step before publish (catch known dependency vulnerabilities)
- [ ] Clean-install smoke test: install from TestPyPI on a fresh env, run
      `intent:init`, verify `.intent/` created correctly
- [ ] Tag `v0.1.0`
- [ ] Publish `mission_ctrl_core` + `mission_ctrl_pi` to PyPI
