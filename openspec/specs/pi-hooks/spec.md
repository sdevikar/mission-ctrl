# Pi Hooks

## Purpose

Automatic session onboarding and drift control for the Pi extension: recap
injection on session start, interception of implementation-intent messages
before they bypass the backlog-first workflow, and continuous synchronization
of the agent's working context file (`AGENTS.md`).

## Requirements

### Requirement: Session-start recap injection
On session start in a project containing `.intent/`, the extension MUST
inject a recap (sized to the session-gap verbosity tier) before the user's
first message and MUST append a `SESSION_STARTED` event.

#### Scenario: Return after a long gap
- GIVEN a project with `.intent/` and a last session 10 days ago
- WHEN a new Pi session starts
- THEN the recap appears before any user message, using the highest verbosity tier, and `SESSION_STARTED` is appended

#### Scenario: No intent directory
- GIVEN a project without `.intent/`
- WHEN a session starts
- THEN no recap is injected and no meta event is written

### Requirement: Implementation-intent interception
`on_before_send` MUST detect implementation-intent messages via its hardcoded
pattern list and redirect the agent to the correct skill path based on current
state: untried new idea → `intent:add-idea`; triaged idea without spec →
`intent:spec-create`; spec without approved design → `intent:design-propose`.

#### Scenario: Fresh idea intercepted
- GIVEN a spec-less idea triaged to `mvp_critical`
- WHEN the user sends "implement the export flow"
- THEN the hook redirects to the spec-create/design flow instead of letting code start

#### Scenario: Approved spec passes through
- GIVEN a spec in `in_progress` that matches the message
- WHEN the user sends "continue with the export flow"
- THEN the message is not intercepted

### Requirement: One-phrase override
The user MUST be able to bypass interception with a one-phrase override; the
override MUST be surfaced in the response so bypasses are never silent.

#### Scenario: Override bypasses
- GIVEN an intercepted "implement X" message
- WHEN the user re-sends with the override phrase
- THEN the message proceeds unblocked and the response notes the bypass

### Requirement: AGENTS.md synchronization
After any skill write to `.intent/`, the extension MUST regenerate `AGENTS.md`
from the maintained template within 1 second, rendering current mission, MVP
status, active specs, and constraints.

#### Scenario: Regen after write
- GIVEN a project with a generated `AGENTS.md`
- WHEN `intent:triage` updates a backlog item
- THEN `AGENTS.md` is rewritten within 1s reflecting the new bucket and matches the template snapshot

#### Scenario: Template change covered by snapshot
- GIVEN a template edit
- WHEN the snapshot test suite runs
- THEN expected `AGENTS.md` output mismatches fail the build until snapshots are reviewed and updated

### Requirement: Hooks contain no business rules
Hooks MUST only detect, delegate to skills, and format output; all state
rules MUST live in skills/core so hook changes never alter intent semantics.

#### Scenario: Delegation observed
- GIVEN an intercepting hook
- WHEN it handles a matched message
- THEN it invokes the matching skill (no direct `.intent/` writes from hook code)
