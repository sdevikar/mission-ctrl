# Intent Logic

Deterministic decision support on top of intent state: a dependency-aware
"what's next" recommender and a session recap generator. Pure functions of
`.intent/` state plus read-only git history — no LLM, no network.

## Requirements

### Requirement: Planner ranking
`suggest_next()` MUST rank candidate specs with MVP-linked first, then
unblocked before blocked, then fewer unresolved dependencies first, then
continuity with current focus; it MUST only return specs in
`draft`, `design_proposed`, or `design_approved` status.

#### Scenario: MVP-critical preferred
- GIVEN an unblocked MVP-linked spec and an unblocked non-MVP spec at equal depth
- WHEN `suggest_next()` is called
- THEN the MVP-linked spec ranks first

#### Scenario: Continuity preferred
- GIVEN a spec sharing the current focus's feature area and an equally-ranked unrelated spec
- WHEN `suggest_next()` is called
- THEN the continuity spec ranks first

### Requirement: Blocked specs never suggested
`suggest_next()` MUST exclude any spec whose `depends_on` set contains a spec
that is not `done`, and MUST exclude specs already in `in_progress` or `done`.

#### Scenario: Blocked excluded
- GIVEN a spec with one dependency in `design_approved` status
- WHEN `suggest_next()` is called
- THEN that spec does not appear in the result, regardless of MVP linkage

### Requirement: Recap generation
`generate_recap()` MUST return a payload containing: mission statement, MVP
completion percentage, last focus spec, changes since the last session, and a
ranked next-spec suggestion (delegated to `suggest_next()`), rendered in
verbosity tiers.

#### Scenario: Mid-flight recap
- GIVEN the mid-flight fixture (3 of 5 MVP items linked to done specs, recent events)
- WHEN `generate_recap()` is called after a session gap
- THEN the recap reports 60% MVP completion, names the last focus spec, and lists events since the previous session

#### Scenario: Fresh project recap
- GIVEN the empty-project fixture (init only)
- WHEN `generate_recap()` is called
- THEN the recap states 0% MVP completion, no last focus, and suggests starting triage/backlog work

### Requirement: Read-only git history in recap
The recap MUST compute "what changed" from `git log` since the last session
timestamp and MUST never write to the repository or index.

#### Scenario: Commit summary included
- GIVEN a repo with 4 commits after the last session timestamp
- WHEN `generate_recap()` is called
- THEN the recap's change section reflects those 4 commits and `git status` shows a clean working tree afterwards

### Requirement: Zero network in the logic layer
All logic-layer functions MUST complete with no network access and must not
invoke any LLM.

#### Scenario: Offline run
- GIVEN the network disabled
- WHEN `suggest_next()` and `generate_recap()` run over all three fixtures
- THEN both complete successfully with correct output
