# Delta for Pi Skills

## Purpose

The Pi extension's skill surface: the only write path into `.intent/` state.
Each skill parses agent input, enforces status-transition legality, delegates
persistence to `mission_ctrl_core`, and appends the corresponding meta event.

## ADDED Requirements

### Requirement: Extension installation and registration
The extension MUST install locally (`pi install ./packages/pi-package`) and
register its manifest with hooks and all 10 `intent:*` skills in a single
package.

#### Scenario: Local install
- GIVEN a fresh clone with both packages built
- WHEN `pi install ./packages/pi-package` is run in a test project
- THEN all 10 `intent:*` skills are invokable in a Pi session

### Requirement: Idea capture and triage
`intent:add-idea` MUST create a backlog entry and return its ID; `intent:triage`
MUST update the entry's bucket and alignment fields from a Pi-supplied verdict
and emit `BACKLOG_ADDED` / `BACKLOG_TRIAGE` events respectively.

#### Scenario: Add then triage
- GIVEN an initialized project
- WHEN the agent calls add-idea(title, description) then triage(idea_id, bucket=parked, alignment)
- THEN backlog.json holds one `parked` item and meta.jsonl contains both events in order

### Requirement: Spec creation from idea
`intent:spec-create` MUST convert a backlog idea into a spec node linked to
that idea, and MUST refuse creation without a title and at least one linked
idea or MVP item.

#### Scenario: Create spec from idea
- GIVEN a triaged idea `idea_001`
- WHEN spec-create(idea_001) is called
- THEN a new spec node in status `draft` links `idea_001` and a `SPEC_CREATED` event is appended

#### Scenario: Unlinked spec refused
- GIVEN an idea with no title
- WHEN spec-create is called for it
- THEN no spec is created and the skill returns the validation reason

### Requirement: Spec lifecycle transitions
`intent:spec-status` MUST accept only legal transitions along
`draft → design_proposed → design_approved → in_progress → done` (looping back
on revision) and MUST reject illegal ones with the current status named.

#### Scenario: Legal transition
- GIVEN a spec in `design_approved`
- WHEN spec-status(spec_id, in_progress) is called with all dependencies done
- THEN the spec updates and a `SPEC_STATUS_UPDATED` event is appended

#### Scenario: Illegal transition rejected
- GIVEN a spec in `draft`
- WHEN spec-status(spec_id, in_progress) is called
- THEN the spec is unchanged and the error names `draft` as the current status

### Requirement: Design gate
`intent:design-propose` MUST store the Pi-supplied design digest text and move
the spec to `design_proposed` (`DESIGN_PROPOSED`); `intent:design-approve` MUST
move it to `design_approved` with the decision and notes
(`DESIGN_APPROVED`), or send it back to `design_proposed` on rejection.

#### Scenario: Propose then approve
- GIVEN a draft spec
- WHEN design-propose(spec_id, digest) then design-approve(spec_id, approved, notes) are called
- THEN the spec ends in `design_approved`, the digest is stored, and both events are appended

#### Scenario: Design rejection loops back
- GIVEN a spec in `design_proposed`
- WHEN design-approve(spec_id, rejected, "too complex") is called
- THEN the spec's digest is updated with the rejection notes and it remains/reverts to `design_proposed`

### Requirement: Read-only skills
`intent:recap` MUST return the formatted recap from the core logic layer;
`intent:next` MUST return the planner's ranked unblocked specs; `intent:status`
MUST return a dashboard view over all stores. None of the three MUST modify
`.intent/` state.

#### Scenario: Read-only guarantee
- GIVEN any initialized project
- WHEN recap, next, and status are each invoked once
- THEN no file in `.intent/` changes (checksums identical) and no meta event is appended

### Requirement: All writes through core
No skill MAY persist `.intent/` state directly; every mutation MUST go through
`mission_ctrl_core` stores so validation, ID generation, and event logging
cannot be bypassed.

#### Scenario: Store-mediated write
- GIVEN a skill creating an idea
- WHEN the write is inspected
- THEN the backlog entry and its `BACKLOG_ADDED` event both carry core-generated IDs, not skill-constructed ones
