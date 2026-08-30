# Tasks: Logic Layer (M1) — logic-layer-02

## Planner
- [x] `planner.py`: `suggest_next()` ranking — MVP-critical first, unblocked, fewest deps, focus continuity
- [x] Unit tests: blocked specs never suggested; ranking ties broken per rule order (graph fixtures)

## Recap
- [x] `recap.py`: `generate_recap()` — mission, MVP %, last focus, changes since, next suggestion
- [x] Verbosity tiers
- [x] Unit tests: recap correct on all 3 fixtures (empty-project, mid-flight, complex-graph)

## Git
- [x] Git read utility: `git log` since timestamp (read-only, no writes, no index mutation)
- [x] Test: recap working tree left clean

## Decisions & guards
- [x] Document: alignment/design reasoning intentionally NOT in core — Pi supplies structured inputs to skills
- [x] Test: logic layer runs with network disabled
