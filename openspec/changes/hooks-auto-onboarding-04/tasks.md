# Tasks: Hooks & Auto-Onboarding (M3) — hooks-auto-onboarding-04

## on_session_start
- [ ] Detect `.intent/` presence
- [ ] Session-gap detection + verbosity tier selection
- [ ] Inject recap before the user's first message
- [ ] Append `SESSION_STARTED` event

## on_before_send
- [ ] Hardcoded implementation-intent pattern list
- [ ] Redirect to backlog-add / triage / design-propose depending on state
- [ ] One-phrase override to bypass (surfaced, never silent)

## AGENTS.md sync
- [ ] Post-skill hook: regenerate `AGENTS.md` after any `.intent/` write (≤1s)
- [ ] `AGENTS.md` template
- [ ] Snapshot tests for template output

## Tests
- [ ] Hook behavior tests: session-gap tiers, pattern matches/non-matches, override (temp workspace)
- [ ] E2E: session open shows recap; "implement X" intercepted on the mid-flight fixture
- [ ] E2E: skill write updates `AGENTS.md` within 1s
