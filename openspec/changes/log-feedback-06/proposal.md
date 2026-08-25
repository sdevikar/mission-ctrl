# Proposal: Feedback Logging Skill (M5-prep)

## Why

Dogfooding produces observations — false positives, planner misses, verbosity
complaints — that disappear into memory unless captured immediately and
structurally. "Fix whatever breaks" is too vague to drive targeted fixes.
Adding `intent:log-feedback` as a first-class skill turns the dogfood week into
a structured data-collection exercise: every issue is tagged by category and
severity and written to meta.jsonl, making M5 (post-ship fixes) evidence-based
rather than anecdotal.

## Prerequisites

- pi-extension-shell-03b applied (M2b — pi-package exists and is installable)

## What Changes

- New skill `intent:log-feedback` added to `packages/pi-package`.
- Input schema (see `design.md`):
  - `category`: one of `false_positive | planner_miss | recap_verbosity | hook_behavior | bug | ux | other`
  - `description`: free-form text (what happened, what was expected)
  - `severity`: one of `blocker | polish | backlog`
  - `related_spec_id` (optional): spec the issue is associated with
- Emits `FEEDBACK_LOGGED` event to meta.jsonl (new event type added to `EventBuilder`).
- New query helper: `MetaStore.read_feedback(severity=None)` — returns all
  `FEEDBACK_LOGGED` events, optionally filtered by severity, for M5 triage.

## Non-goals

- No UI, no GitHub issue creation, no external integrations.
- Feedback is stored only in meta.jsonl; it is queryable but not actionable
  within the skill itself.

## Impact

- Additive to `packages/pi-package` and `packages/core` (new event type + read helper).
- Used during the M4 dogfood week; feeds directly into M5 fix prioritization.

**Done when:** `intent:log-feedback` writes a correctly structured
`FEEDBACK_LOGGED` event to meta.jsonl, and `MetaStore.read_feedback()` returns
it correctly filtered.
