# Tasks: Hooks & Auto-Onboarding (M3) — hooks-auto-onboarding-04

## on_session_start
- [ ] Detect `.intent/` presence; no-op gracefully if `.intent/` is absent
- [ ] Session-gap detection + verbosity tier selection (thresholds in design.md)
- [ ] Inject recap before the user's first message
- [ ] Append `SESSION_STARTED` event
- [ ] Test: on_session_start no-ops cleanly when `.intent/` is absent (uninitialized project)

## on_before_send
- [ ] Hardcoded implementation-intent pattern list (full-word, case-insensitive — see design.md)
- [ ] Redirect to backlog-add / triage / design-propose depending on current state
- [ ] One-phrase override to bypass (surfaced in response, never silent)
- [ ] Log every interception: emit `INTENT_INTERCEPTED` event to meta.jsonl
      (fields: pattern_matched, redirect_target, original_message_excerpt)
- [ ] Log every bypass: emit `INTENT_BYPASS_USED` event to meta.jsonl
      (fields: bypass_phrase, original_message_excerpt)
- [ ] Add `INTENT_INTERCEPTED` and `INTENT_BYPASS_USED` to `EventBuilder`
      (requires core-foundation-01 extension)

## AGENTS.md sync
- [ ] Post-skill hook: regenerate `AGENTS.md` after any `.intent/` write (≤1s)
- [ ] Jinja2 template: `packages/pi-package/templates/agents_md.jinja2`
- [ ] Sanitization: escape/strip all user-supplied text fields before rendering;
      raise `SanitizationError` on prompt-injection patterns (`<!--`, `-->`,
      backtick-fenced blocks with language identifier) — see design.md
- [ ] Snapshot tests for template output

## Tests
- [ ] Hook behavior tests: all 4 session-gap tier thresholds, pattern matches/
      non-matches, override, bypass logging (temp workspace)
- [ ] E2E: session open shows recap; "implement X" intercepted on mid-flight fixture;
      `INTENT_INTERCEPTED` event present in meta.jsonl
- [ ] E2E: bypass detected; `INTENT_BYPASS_USED` event present in meta.jsonl
- [ ] E2E: skill write updates `AGENTS.md` within 1s
- [ ] Sanitization test: spec with injection-attempt title renders safely in AGENTS.md
