# Tasks: Logic Layer (M1) — logic-layer-02

## Planner
- [ ] `planner.py`: `suggest_next()` ranking — MVP-critical first, unblocked, fewest deps, focus continuity
- [ ] Unit tests: blocked specs never suggested; ranking ties broken per rule order (graph fixtures)

## Recap
- [ ] `recap.py`: `generate_recap()` — mission, MVP %, last focus, changes since, next suggestion
- [ ] Verbosity tiers
- [ ] Unit tests: recap correct on all 3 fixtures (empty-project, mid-flight, complex-graph)

## Git
- [ ] Git read utility: `git log` since timestamp (read-only, no writes, no index mutation)
- [ ] Test: recap working tree left clean

## Decisions & guards
- [ ] Document: alignment/design reasoning intentionally NOT in core — Pi supplies structured inputs to skills
- [ ] Test: logic layer runs with network disabled
