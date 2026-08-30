# Proposal: Logic Layer (M1)

## Why

The planner ("what next") and recap ("catch me up") are the two pieces of
product value that don't need an LLM and are fully testable. Building them on
the M0 stores — with zero network calls against the shared fixtures — locks in
the deterministic core of the product before any Pi integration exists.

## What Changes

- `planner.py`: `suggest_next()` — ranks specs by MVP-criticality, unblocked
  status, fewest dependencies, current-focus continuity.
- `recap.py`: `generate_recap()` — mission, MVP completion %, last focus,
  changes since last session, next-spec suggestion; verbosity tiers.
- Git read utility: `git log` since timestamp (read-only, never writes).
- Explicit decision: NO alignment or design-digest LLM modules in core —
  Pi supplies those as structured skill inputs instead.

## Non-goals

- No LLM calls anywhere in this package (no alignment, no digest generation).
- No skills, hooks, or packaging (`packages/pi-package` is change 03).
- No auto git-commit association (deferred in kanban backlog).

## Impact

- Additive to `packages/core` (new `planner.py`, `recap.py`, git util + tests).
- Consumes M0 stores and the three fixture repos — depends on
  core-foundation-01.

**Done when:** `suggest_next()` and `generate_recap()` produce correct output
against all three fixtures with zero network calls.
