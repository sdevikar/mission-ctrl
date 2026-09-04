# Proposal: Hooks & Auto-Onboarding (M3)

## Why

The passive half of the vision: returning developers get a recap without
asking (quick-recap onboarding), off-mission work gets intercepted before it
starts (minimalist enforcer with one-phrase override), and the agent's context
stays current via auto-generated `AGENTS.md`. Without hooks, users must
manually drive every intent action.

## What Changes

- `on_session_start` hook: detect `.intent/` presence, compute session gap,
  pick a verbosity tier, inject the recap before the user's first message, and
  append `SESSION_STARTED`.
- `on_before_send` hook: hardcoded pattern list for implementation-intent
  detection ("implement X", "add feature Y", …); redirect to the correct
  skill path (add-idea / triage / design-propose) based on current state.
- One-phrase override to bypass interception, so the enforcer is never a
  productivity blocker; bypasses are never silent (the override is surfaced
  in the response).
- Post skill hook: regenerate `AGENTS.md` after any `.intent/` write, from a
  versioned template, with snapshot tests.

## Non-goals

- No configurable pattern matching (v1 ships a hardcoded list — kanban backlog).
- No hooks that contain business rules: hooks fire skills; skills and core own
  the rules.

## Impact

- Extends `packages/pi-package` (hooks + AGENTS.md sync); depends on M2 skills
  and M1 recap.

**Done when:** opening a project with `.intent/` auto-shows the recap; saying
"implement X" gets intercepted and redirected correctly; any skill write updates
`AGENTS.md` within 1s.
