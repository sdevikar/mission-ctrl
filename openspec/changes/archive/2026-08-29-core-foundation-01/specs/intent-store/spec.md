# Delta for Intent Store

## Purpose

Deterministic persistence layer for mission intent state: reads, writes, and
validates the `.intent/` JSON/JSONL artifacts (mission, mvp, constraints,
backlog, specs, meta) with canonical IDs, append-only event logging, and
field-level error reporting — usable from any process with zero network access.

## ADDED Requirements

### Requirement: Intent initialization
The core MUST provide `IntentStore.init()` that creates all six `.intent/`
artifacts (mission.json, mvp.json, constraints.json, backlog.json, specs.json,
meta.jsonl) with valid template content and records an `INTENT_CREATED` event.

#### Scenario: Init on empty project
- GIVEN a directory with no `.intent/` folder
- WHEN `init()` is called
- THEN all six artifacts exist, pass validation, and meta.jsonl contains exactly one `INTENT_CREATED` event

#### Scenario: Init is idempotent
- GIVEN an existing valid `.intent/` directory
- WHEN `init()` is called again
- THEN existing data is not modified and no duplicate `INTENT_CREATED` event is appended

### Requirement: Field-level model validation
All six artifact types MUST be validated by pydantic models; any invalid value
MUST be rejected with an error that names the file, field, and offending value.

#### Scenario: Invalid constraint severity is rejected
- GIVEN a constraints.json containing `severity: "urgent"` (not in enum)
- WHEN the file is loaded through `ConstraintsStore`
- THEN loading fails with an error naming `constraints[2].severity` and the illegal value

#### Scenario: Invalid spec status is rejected
- GIVEN a specs.json with a node `status: "cancelled"` (not in the lifecycle enum)
- WHEN `SpecStore.get()` is called for that node
- THEN the read fails with a field-level error, not a generic parse error

### Requirement: Canonical ID generation
Each store MUST generate globally unique, canonical IDs (`mis_`, `mvp_`,
`con_`, `idea_`, `spec_`, `evt_` prefixes with zero-padded counters) via
`next_id()` that is monotonic across appends within a session.

#### Scenario: Sequential IDs
- GIVEN a backlog with `idea_001` and `idea_002`
- WHEN `BacklogStore.add()` is called
- THEN the new item receives `idea_003`

### Requirement: Backlog CRUD and search
`BacklogStore` MUST support add, update (bucket and alignment fields), get by
ID, and search; updates MUST preserve the item's original ID and append a
corresponding meta event.

#### Scenario: Triage update
- GIVEN an untriaged backlog item `idea_004`
- WHEN `update()` sets bucket to `parked` with alignment verdicts
- THEN `get("idea_004")` returns the new bucket, the ID is unchanged, and a `BACKLOG_TRIAGE` event is appended

### Requirement: Dependency cycle rejection
`SpecStore` MUST reject any write that would introduce a cycle in
`depends_on` (`validate_no_cycles`), and MUST reject setting a spec to
`in_progress` while any `depends_on` spec is not `done`.

#### Scenario: Cycle rejected
- GIVEN specs A → B → C (A depends on B, B depends on C)
- WHEN a write sets C to depend on A
- THEN the write fails with an error naming the cycle A → B → C → A

#### Scenario: Blocked spec cannot start
- GIVEN spec D depends on spec E (status `design_approved`)
- WHEN a write sets D to `in_progress`
- THEN the write fails naming E as an unmet dependency

### Requirement: Append-only meta event log
`MetaStore` MUST append events (never rewrite history) and support
`read_all()` and `read_since(timestamp)`; `EventBuilder` MUST produce events
whose shape matches the v1 event catalog (required fields: event_id,
timestamp, event_type, actor, affected_entities, linked_intent, decision,
reasoning, session.id).

#### Scenario: Read since timestamp
- GIVEN a meta.jsonl with events at t1 < t2 < t3
- WHEN `read_since(t2)` is called
- THEN only the t3 event is returned, in order

#### Scenario: Malformed event rejected
- GIVEN an event payload missing `reasoning`
- WHEN `EventBuilder` builds it
- THEN construction fails; nothing is appended to meta.jsonl
