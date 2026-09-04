# Delta for Bridge Protocol

## Purpose

Versioned Node ↔ Python contract letting any Node host (Pi extension,
OpenSpec integrations, future tooling) drive the intent loop without
duplicating core logic.

## ADDED Requirements

### Requirement: JSON protocol v1 over stdio
Client and server MUST exchange newline-delimited JSON with `protocol: 1`,
per-request `id`, op dispatch, typed success/error envelopes, a 1MB line
cap, and client-side request timeouts.

#### Scenario: Full skill round-trip
- GIVEN a spawned bridge server on a temp project
- WHEN the client sends `skill/spec-create` with a valid input
- THEN it receives the skill result JSON with the matching request id

#### Scenario: Typed error pass-through
- GIVEN a request that violates skill rules (e.g. illegal transition)
- WHEN the client sends it
- THEN it receives `ok: false` with the original SkillError code and no traceback

### Requirement: Python server dispatch
The server MUST expose all 10 skills plus `hook/session-start`,
`hook/before-send`, and `sync/agents-md` ops, reject unknown ops and
protocol versions with typed errors, and never die on a single bad request.

#### Scenario: Unknown op rejected, server survives
- GIVEN a running server
- WHEN the client sends an unknown op followed by a valid one
- THEN the first gets `UNKNOWN_OP` and the second succeeds

### Requirement: Dependency-free TypeScript client
The TS client MUST spawn the server, resolve the interpreter, multiplex
requests by id, enforce timeouts, and carry zero runtime dependencies.

#### Scenario: Timeout enforced
- GIVEN a server that never replies
- WHEN a request exceeds the timeout
- THEN the client raises a timeout error instead of hanging

### Requirement: Pi adapter on the bridge
The Pi adapter MUST implement `session_start` recap injection, `input`
intercept/redirect/bypass surfacing, and one custom tool per skill —
all through the bridge client, with no intent logic in TypeScript.

#### Scenario: Session start injects recap in Pi
- GIVEN the adapter installed via `pi install` on a project with `.intent/`
- WHEN a Pi session starts after a long gap
- THEN a recap is injected before the first message
