# Design: Core Foundation (M0)

Full architecture: `docs/architecture.md`; data model + event catalog:
`docs/design.md` §3–4; live samples: `docs/examples/`. This change implements
that design for `packages/core` only.

## Key decisions

- **Pydantic models** are the single validation point; stores validate on
  read and write. AJV/JSON-Schema is no longer relevant (core is Python).
- **IDs**: global canonical (`mis_001`, `spec_042`, `evt_000391`), zero-padded
  counters derived from existing state.
- **Timestamps**: ISO 8601 UTC everywhere.
- **Store layering** (per design.md §1): single-file stores do read/write +
  ID generation only; `IntentStore` orchestrates; `SpecStore` owns cycle
  detection; status-transition *legality* policy lives in the skill layer
  (change 03), while dependency enforcement lives in core.
- **meta.jsonl**: one JSON object per line, no wrapping array; writes are
  append-only.
- **Fixtures**: `packages/core/tests/fixtures/{empty-project,mid-flight,complex-graph}/`
  are the source of truth for all deterministic tests (all three milestones
  reuse them).

## Constraints

- No network, no subprocess, no LLM, no writes outside `.intent/`.
- 100% pydantic field coverage in unit tests; clear field-level error
  formatting (file → array index → field → value).
