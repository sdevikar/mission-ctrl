# Delta for V0.1 Release

## Purpose

Distribution and usability of the shipped v0.1.0: an honest README
quickstart that works end-to-end, resolved packaging for both Python
packages, and a tagged, published release.

## ADDED Requirements

### Requirement: Quickstart works end-to-end
The README quickstart MUST take a fresh repository from install to a
completed init → add-idea → triage → spec-create cycle without manual file
edits or undocumented steps.

#### Scenario: Fresh-repo quickstart
- GIVEN a brand-new empty git repository
- WHEN a developer follows the README quickstart exactly
- THEN all 10 skills are invokable and the lifecycle above completes without hand-editing any `.intent/` file

### Requirement: Resolved distribution mechanism
Before the release tag, the distribution mechanism MUST be decided and
documented (npm wrapper via `pi install npm:@mission-ctrl/pi-package` vs
native PyPI/pip), and both documented install paths in the README MUST match
how the packages are actually published.

#### Scenario: README matches reality
- GIVEN the published v0.1.0 artifacts
- WHEN the README's install commands are run verbatim in a clean environment
- THEN the packages install and the extension loads in Pi without error

### Requirement: Reproducible release
The `v0.1.0` tag MUST be produced from a CI pipeline that runs the full test
suite (unit + fixture + snapshot + e2e lifecycle) before allowing publish, so
a broken release cannot be tagged.

#### Scenario: Failed tests block publish
- GIVEN a test failure in the suite
- WHEN the CI release pipeline runs
- THEN publishing is blocked until the suite is green

### Requirement: Dogfood without hand edits
During the one-week dogfood of mission-ctrl in Pi, intent state MUST be
maintained exclusively through skills and hooks.

#### Scenario: Week of dogfooding
- GIVEN the dogfood period starting at v0.1.0-rc
- WHEN mission-ctrl is driven through its own workflow for one week
- THEN git history shows no direct hand-edits of `.intent/` files outside of skill/hook-generated writes
