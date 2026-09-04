# Tasks: Hooks & Auto-Onboarding (M3) — hooks-auto-onboarding-04

## on_session_start
- [x] Detect `.intent/` presence; no-op gracefully if `.intent/` is absent
- [x] Session-gap detection + verbosity tier selection (thresholds in design.md)
- [x] Inject recap before the user's first message
- [x] Append `SESSION_STARTED` event
- [x] Test: on_session_start no-ops cleanly when `.intent/` is absent (uninitialized project)

## on_before_send
- [x] Hardcoded implementation-intent pattern list (full-word, case-insensitive — see design.md)
- [x] Redirect to backlog-add / triage / design-propose depending on current state
- [x] One-phrase override to bypass (surfaced in response, never silent)
- [x] Log every interception: emit `INTENT_INTERCEPTED` event to meta.jsonl
      (fields: pattern_matched, redirect_target, original_message_excerpt)
- [x] Log every bypass: emit `INTENT_BYPASS_USED` event to meta.jsonl
      (fields: bypass_phrase, original_message_excerpt)
- [x] Add `INTENT_INTERCEPTED` and `INTENT_BYPASS_USED` to `EventBuilder`
      (requires core-foundation-01 extension)

## AGENTS.md sync
- [x] Post-skill hook: regenerate `AGENTS.md` after any `.intent/` write (≤1s)
- [x] Jinja2 template: `packages/pi-package/templates/agents_md.jinja2`
- [x] Sanitization: escape/strip all user-supplied text fields before rendering;
      raise `SanitizationError` on prompt-injection patterns (`<!--`, `-->`,
      backtick-fenced blocks with language identifier) — see design.md
- [x] Snapshot tests for template output

## Tests
- [x] Hook behavior tests: all 4 session-gap tier thresholds, pattern matches/
      non-matches, override, bypass logging (temp workspace)
- [x] E2E: session open shows recap; "implement X" intercepted on mid-flight fixture;
      `INTENT_INTERCEPTED` event present in meta.jsonl
- [x] E2E: bypass detected; `INTENT_BYPASS_USED` event present in meta.jsonl
- [x] E2E: skill write updates `AGENTS.md` within 1s
- [x] Sanitization test: spec with injection-attempt title renders safely in AGENTS.md
