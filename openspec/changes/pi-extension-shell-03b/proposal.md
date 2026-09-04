# Proposal: Pi Extension Shell — Design Gate (M2b)

## Why

Splits from pi-extension-shell-03 (archived). Adds the three skills that
implement the design-review workflow on top of the core loop delivered in M2a:
on-demand recap, design-propose (Pi drafts; skill validates and stores), and
design-approve (developer approves or rejects with notes). Without these, specs
can't safely advance to in_progress without a design gate.

## Prerequisites

- pi-extension-shell-03a applied (M2a core-loop skills)

## What Changes

- Three additional skills added to `packages/pi-package` (see `design.md` for
  full I/O contracts):
  - `intent:recap` — on-demand recap (auto-injected by M3 session hook; this
    is the user-invoked form); takes optional verbosity override; returns
    `RecapResult`
  - `intent:design-propose` — takes Pi-supplied digest text; transitions spec
    draft → design_proposed; emits `DESIGN_PROPOSED`
  - `intent:design-approve` — approve → design_approved (emits `DESIGN_APPROVED`
    with `approval=true`) or reject → draft (emits `DESIGN_APPROVED` with
    `approval=false`); always requires notes on reject

## Non-goals

- Hook behavior is M3 (hooks-auto-onboarding-04); this change only adds the
  three skills.
- Verbosity tier selection is driven by the session hook in M3; `intent:recap`
  accepts an explicit `verbosity` parameter so it is independently testable.

## Impact

- Additive to `packages/pi-package`; no existing M2a code modified.

**Done when:** the full lifecycle including the design gate — init → add-idea →
triage → spec-create → design-propose → design-approve → spec-status(done) →
status — runs manually via Pi skills with correct state in `.intent/`.
