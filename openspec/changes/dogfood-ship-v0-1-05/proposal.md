# Proposal: Dogfood & Ship v0.1 (M4)

## Why

The design is only as good as a week of real use. M4 dogfoods mission-ctrl on
mission-ctrl — the strictest possible correctness test of the intent loop —
then resolves the one open infrastructure question (distribution mechanism)
and publishes v0.1.0.

## What Changes

- One-week dogfood of this repository through its own workflow in Pi:
  real usage, no hand-editing `.intent/`.
- Fixes driven by real use — especially `on_before_send` false positives,
  planner ranking misses, and recap verbosity.
- **Distribution decision (open, must resolve before packaging):** confirm
  whether Pi's install mechanism requires an npm wrapper even for a
  pure-Python package (`pi install npm:@mission-ctrl/pi-package`) or natively
  supports PyPI/pip. This decides the M4 packaging shape.
- README with install + quickstart.
- Tag `v0.1.0`; publish `mission_ctrl_core` + `mission_ctrl_pi`.

## Non-goals

- No Claude Code plugin, no MCP servers, no schema migration tooling — all
  remain in the kanban backlog.
- No feature work beyond fixes revealed by dogfooding.

## Impact

- Affects both packages; publishes to the public index once packaging shape
  is confirmed. Dogfood fixes feed back into specs via normal change flow.

**Done when:** personally used in Pi for one week without hand-editing
`.intent/` files, and v0.1.0 is tagged and published.

## Prerequisites

- core-foundation-01, logic-layer-02, pi-extension-shell-03,
  hooks-auto-onboarding-04 all applied and archived.
