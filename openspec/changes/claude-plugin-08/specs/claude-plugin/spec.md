# Delta for Claude Code Plugin

## Purpose

First-class intent loop inside Claude Code (skills + hooks + commands),
executed through the bridge so the plugin holds prompts and wiring only.

## ADDED Requirements

### Requirement: Per-skill SKILL.md with pinned contracts
Every intent skill MUST have a `SKILL.md` whose input block validates
against its Pydantic schema 1:1, delegating execution to the bridge.

#### Scenario: Contract drift fails the build
- GIVEN a SKILL.md whose input block drops a required schema field
- WHEN the contract test suite runs
- THEN it fails until the doc and schema match again

#### Scenario: Full lifecycle through the plugin
- GIVEN the plugin installed from local path
- WHEN a feature runs init → … → design-approve → done via plugin skills
- THEN `.intent/` state is correct with zero hand-edits

### Requirement: SessionStart recap hook
`SessionStart` MUST inject a gap-tiered recap for the opened project and
skip silently when no `.intent/` exists.

#### Scenario: Fresh project stays silent
- GIVEN a project without `.intent/`
- WHEN a Claude Code session starts
- THEN no recap is injected and no event is written

### Requirement: UserPromptSubmit interception
`UserPromptSubmit` MUST intercept implementation intent with the M3 redirect
ladder (spec-status → design-propose → spec-create → triage → add-idea) and
honor the one-phrase override visibly.

#### Scenario: Override proceeds visibly
- GIVEN an intercepted "implement X" prompt
- WHEN the user re-sends with the override phrase
- THEN the prompt proceeds and the response notes the logged bypass

### Requirement: Local-first distribution
The plugin MUST install from a local path for dogfooding; marketplace
publication MUST wait until the dogfood pass succeeds.

#### Scenario: Dogfood gate
- GIVEN a passing local dogfood pass with issues logged via
  `intent:log-feedback`
- WHEN the team reviews the feedback
- THEN marketplace publication is scheduled, not before
