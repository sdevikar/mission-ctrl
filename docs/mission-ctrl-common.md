# Mission Ctrl — Common Specification
## Shared Core: Data Model, Logic, Schemas & Event System
### v1.0 | 2026-08-04

> This document covers all components that are **shared** between the Claude Code plugin and Pi package.
> See [`mission-ctrl-claude-plugin.md`](./mission-ctrl-claude-plugin.md) and [`mission-ctrl-pi-package.md`](./mission-ctrl-pi-package.md) for agent-specific details.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Repository Layout](#2-repository-layout)
3. [Data Model & Schemas](#3-data-model--schemas)
4. [Meta Event Log](#4-meta-event-log)
5. [Core Library](#5-core-library)
6. [Skill Reference v1](#6-skill-reference-v1)
7. [Build & Distribution](#7-build--distribution)
8. [Testing Strategy](#8-testing-strategy)
9. [Phase-by-Phase Rollout (Core Only)](#9-phase-by-phase-rollout-core-only)
10. [Appendix A: JSON Schemas](#appendix-a-json-schemas)
11. [Appendix B: Event Catalog](#appendix-b-event-catalog)

---

## 1. Architecture Overview

### 1.1 Design Principles

1. **Repo-local state.** All intent artifacts live in `.intent/` at the repository root. No cloud backend, no auth, no network dependency.
2. **Skills are the API.** Every user-facing operation is a skill. The agent never edits `.intent/` files directly.
3. **Hooks guarantee behavior.** Session-start hooks enforce the workflow contract without relying on agent obedience.
4. **Adaptive, not noisy.** The recap hook always fires but adapts its verbosity to session gap and state changes.
5. **One core, multiple surfaces.** `@mission-ctrl/core` is shared. Claude plugin and Pi package are thin wrappers.

### 1.2 Component Diagram

```
+-------------------------------------------------------------+
|              @mission-ctrl/core (npm package)               |
|  +------------------+  +------------------+                 |
|  |   Store Layer    |  |   Logic Layer    |                 |
|  |  IntentStore     |  |  recap.ts        |                 |
|  |  MissionStore    |  |  planner.ts      |                 |
|  |  BacklogStore    |  |  alignment.ts    |                 |
|  |  SpecStore       |  |  design.ts       |                 |
|  |  MetaStore       |  |                  |                 |
|  +------------------+  +------------------+                 |
|  +------------------+  +------------------+                 |
|  |   Schemas        |  |   EventBuilder   |                 |
|  |  *.schema.json   |  |  All v1 events   |                 |
|  |  AJV validation  |  |                  |                 |
|  +------------------+  +------------------+                 |
+-----------------------------+-------------------------------+
                              |
             +----------------+----------------+
             |                                 |
   +---------+---------+           +-----------+----------+
   | claude-plugin      |           |  pi-package           |
   | (Claude Code)      |           |  (Pi Agent)           |
   +--------------------+           +----------------------+
```

---

## 2. Repository Layout

### 2.1 Monorepo Structure

```
mission-ctrl/
├── packages/
│   ├── core/                    # @mission-ctrl/core
│   │   ├── src/
│   │   │   ├── index.ts
│   │   │   ├── schemas/         # JSON Schema definitions
│   │   │   │   ├── mission.schema.json
│   │   │   │   ├── mvp.schema.json
│   │   │   │   ├── backlog.schema.json
│   │   │   │   ├── specs.schema.json
│   │   │   │   ├── constraints.schema.json
│   │   │   │   └── meta.schema.json
│   │   │   ├── models/          # TypeScript types + validators
│   │   │   │   ├── mission.ts
│   │   │   │   ├── mvp.ts
│   │   │   │   ├── backlog.ts
│   │   │   │   ├── specs.ts
│   │   │   │   ├── constraints.ts
│   │   │   │   └── meta.ts
│   │   │   ├── store/           # File I/O + validation
│   │   │   │   ├── IntentStore.ts
│   │   │   │   ├── MissionStore.ts
│   │   │   │   ├── BacklogStore.ts
│   │   │   │   ├── SpecStore.ts
│   │   │   │   ├── MetaStore.ts
│   │   │   │   └── utils.ts
│   │   │   ├── logic/           # Business rules
│   │   │   │   ├── alignment.ts
│   │   │   │   ├── planner.ts
│   │   │   │   ├── recap.ts
│   │   │   │   └── design.ts
│   │   │   └── events/          # Event generation
│   │   │       └── EventBuilder.ts
│   │   ├── tests/
│   │   │   ├── store/
│   │   │   ├── logic/
│   │   │   └── fixtures/
│   │   │       ├── empty-project/
│   │   │       ├── mid-flight/
│   │   │       └── complex-graph/
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── claude-plugin/           # See mission-ctrl-claude-plugin.md
│   └── pi-package/              # See mission-ctrl-pi-package.md
│
├── docs/
│   ├── mission-ctrl-common.md         # This file
│   ├── mission-ctrl-claude-plugin.md
│   └── mission-ctrl-pi-package.md
│
├── .github/
│   └── workflows/
│       ├── test.yml
│       └── release.yml
│
├── package.json                 # Root monorepo config
├── pnpm-workspace.yaml
└── README.md
```

### 2.2 Runtime Layout (Inside User's Project)

```
user-project/
├── src/
├── .intent/
│   ├── mission.json
│   ├── mvp.json
│   ├── backlog.json
│   ├── specs.json
│   ├── constraints.json
│   ├── meta.jsonl
│   └── schemas/                 # Copied from core on init
│       ├── mission.schema.json
│       ├── mvp.schema.json
│       ├── backlog.schema.json
│       ├── specs.schema.json
│       ├── constraints.schema.json
│       └── meta.schema.json
├── CLAUDE.md                    # Auto-generated (Claude plugin)
├── AGENTS.md                    # Auto-generated (Pi package)
├── .gitignore
└── ...
```

> **Important:** `.intent/` is **NOT** gitignored. These files are meant to be committed and shared.

---

## 3. Data Model & Schemas

### 3.1 Design Decisions (Locked)

| Decision | Value | Rationale |
|---|---|---|
| Storage format | JSON files + JSONL | Human-readable, diffable, no binary lock-in |
| Validation | JSON Schema + runtime AJV | Fail fast, prevent agent hallucination of structure |
| IDs | Global canonical (mis_001, spec_042) | Stable linking across files and events |
| State vs. History | Separate | *.json = current truth; meta.jsonl = why it changed |
| Timestamps | ISO 8601 UTC | Sortable, unambiguous |

### 3.2 File: mission.json

Purpose: The north star. Every feature is judged against this statement.

**Fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| id | string | Yes | Global canonical ID, format `mis_001` |
| version | string | Yes | Semver-ish, e.g. `v1.0` |
| statement | string | Yes | 1-3 sentence mission statement |
| success_criteria | string[] | No | Concrete outcomes that prove mission success |
| created_at | ISO string | Yes | Initial creation |
| updated_at | ISO string | Yes | Last modification |

### 3.3 File: mvp.json

Purpose: Concrete must-haves. "Product stands up" means all items are done.

**Fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| version | string | Yes | Tracks MVP revision |
| items | MVPItem[] | Yes | Ordered list of must-haves |
| items[].id | string | Yes | Format `mvp_001` |
| items[].title | string | Yes | Short name |
| items[].description | string | Yes | What "done" means |
| items[].linked_specs | string[] | No | Traceability to specs |
| created_at | ISO string | Yes | |
| updated_at | ISO string | Yes | |

### 3.4 File: constraints.json

Purpose: Guardrails that shape implementation choices.

**Fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| version | string | Yes | |
| constraints | Constraint[] | Yes | |
| constraints[].id | string | Yes | Format `con_001` |
| constraints[].rule | string | Yes | The guardrail text |
| constraints[].rationale | string | Yes | Why this constraint exists |
| constraints[].severity | enum | Yes | `low`, `medium`, `high`, `critical` |
| constraints[].scope | string[] | No | Tags like `backend`, `frontend`, `testing`, `infrastructure` |

### 3.5 File: backlog.json

Purpose: Single inventory of all ideas. Enforces backlog-first workflow.

**Fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| items | BacklogItem[] | Yes | |
| items[].id | string | Yes | Format `idea_001` |
| items[].title | string | Yes | |
| items[].description | string | Yes | |
| items[].bucket | enum | Yes | `untriaged`, `mvp_critical`, `parked`, `archived` |
| items[].alignment.mission | enum | Yes | `strong`, `weak`, `neutral`, `not_aligned` |
| items[].alignment.mvp | enum | Yes | `required`, `not_required`, `extends` |
| items[].alignment.constraints | string[] | No | IDs of constraints that apply |
| items[].links.specs | string[] | No | Linked spec IDs |
| items[].links.mvp_items | string[] | No | Linked MVP item IDs |
| items[].created_at | ISO string | Yes | |
| items[].updated_at | ISO string | Yes | |

**Bucket Semantics:**
- `untriaged` — Just captured, not yet evaluated
- `mvp_critical` — Required for MVP. Prioritize.
- `parked` — Potentially valuable, but defer until MVP stable
- `archived` — Misaligned or obsolete. Kept for audit trail.

### 3.6 File: specs.json

Purpose: The canonical dependency graph. The source of truth for what can be worked on next.

**Fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| nodes | SpecNode[] | Yes | |
| nodes[].id | string | Yes | Format `spec_001` |
| nodes[].title | string | Yes | |
| nodes[].status | enum | Yes | `draft`, `design_proposed`, `design_approved`, `in_progress`, `done`, `blocked` |
| nodes[].depends_on | string[] | No | IDs of specs that must complete first |
| nodes[].links.ideas | string[] | No | Source backlog ideas |
| nodes[].links.mvp_items | string[] | No | Linked MVP items |
| updated_at | ISO string | Yes | Last structural change |

**Status Lifecycle:**
```
draft -> design_proposed -> design_approved -> in_progress -> done
   ^______________|
   (can loop back on revision)
```

**Dependency Rules (Enforced by Core):**
1. No cycles in `depends_on` graph.
2. A spec cannot transition to `in_progress` unless all `depends_on` specs are `done`.
3. A spec cannot transition to `design_proposed` unless it has a title and at least one linked idea or MVP item.

### 3.7 File: meta.jsonl

Purpose: Append-only decision log. Answers "why is it true?"

Each line is a valid JSON object. No wrapping array.

**Fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| event_id | string | Yes | Format `evt_000001` |
| timestamp | ISO string | Yes | When the decision was recorded |
| event_type | enum | Yes | See Appendix B for full catalog |
| actor.type | enum | Yes | `human`, `agent` |
| actor.name | string | Yes | Identifier (e.g. `owner`, `intent-skill`) |
| affected_entities | EntityRef[] | Yes | What changed |
| linked_intent | object | Yes | Intent snapshot at time of decision |
| decision | object | Yes | The actual decision payload (shape varies by event_type) |
| reasoning | string | Yes | Human-readable rationale. Must be concise. |
| depends_on | string[] | No | Previous event IDs this decision depends on |
| git_refs | string[] | No | Commit hashes, branch names |
| tags | string[] | No | Classification tags |
| session.id | string | Yes | Session identifier |

---

## 4. Meta Event Log

### 4.1 Why JSONL

- **Append-only:** O(1) write, no read-modify-write
- **Stream-friendly:** Can tail, filter, grep
- **Git-friendly:** Line-oriented diffs
- **Recoverable:** Corrupt line doesn't break the whole file

### 4.2 Event Catalog (v1 Subset)

| Event Type | When Emitted | Decision Payload |
|---|---|---|
| INTENT_CREATED | Project bootstrap | `{ mission_version, mvp_version, constraints_version }` |
| BACKLOG_ADDED | New idea captured | `{ title, bucket: "untriaged" }` |
| BACKLOG_TRIAGE | Idea classified | `{ bucket, priority?, alignment }` |
| BACKLOG_MERGED | Duplicate consolidated | `{ into_idea_id, from_idea_ids[] }` |
| BACKLOG_ARCHIVED | Idea retired | `{ reason }` |
| SPEC_CREATED | Spec node added | `{ spec_title, status: "draft", links }` |
| SPEC_STATUS_UPDATED | Lifecycle transition | `{ from, to }` |
| SPEC_DEPENDENCY_UPDATED | Graph rewired | `{ added?: string[], removed?: string[] }` |
| DESIGN_PROPOSED | Digest generated | `{ digest_id, key_choices[], risks[], open_questions[] }` |
| DESIGN_APPROVED | Human approves | `{ digest_id, approval: "approved"/"rejected"/"revised", notes? }` |
| DESIGN_REVISED | Digest updated | `{ digest_id, changes[] }` |
| INTENT_UPDATED | Mission/MVP/Constraints change | `{ field, from, to }` |
| OVERRIDE_ACCEPTED | User bypasses guardrail | `{ rule_broken, reason }` |
| GIT_COMMIT_ASSOCIATED | Commit linked to spec | `{ spec_id, commit_hash }` |
| SESSION_STARTED | Auto-onboarding hook fired | `{ gap_hours, verbosity }` |

> Deferred to v2: `BACKLOG_RESURFACED`, `CONSTRAINT_VIOLATION`, `MVP_ITEM_COMPLETED`, `DRIFT_DETECTED`

### 4.3 Event Builder API (Core Library)

The `EventBuilder` class in `packages/core/src/events/EventBuilder.ts`:

- `backlogAdded(idea: BacklogItem) -> MetaEvent`
- `backlogTriage(idea: BacklogItem, oldBucket: string) -> MetaEvent`
- `specCreated(spec: SpecNode, fromIdeaId?: string) -> MetaEvent`
- `specStatusUpdated(specId: string, from: string, to: string) -> MetaEvent`
- `designProposed(digest: DesignDigest) -> MetaEvent`
- `designApproved(specId: string, decision: string, notes?: string) -> MetaEvent`
- `intentUpdated(field: string, from: unknown, to: unknown) -> MetaEvent`
- `overrideAccepted(rule: string, reason: string) -> MetaEvent`

Each method:
1. Generates the next `event_id` (sequential counter)
2. Sets `timestamp` to now
3. Injects `actor`, `linked_intent`, and `session` from constructor options
4. Appends to `meta.jsonl` via `MetaStore`
5. Returns the complete event object

---

## 5. Core Library

### 5.1 Responsibilities

The core library is stateless between calls and **agent-agnostic**. It:
1. Reads/writes `.intent/` files
2. Validates all writes against JSON Schema
3. Enforces business rules (no cycles, status transitions, etc.)
4. Generates meta events
5. Computes recaps, plans, and alignment checks
6. Exposes a clean TypeScript API

### 5.2 Store API

**`IntentStore`** (`packages/core/src/store/IntentStore.ts`):
- Constructor takes `{ intentDir: string }`
- Exposes: `mission`, `mvp`, `backlog`, `specs`, `constraints`, `meta` (sub-stores)
- `init()`: Creates `.intent/` dir and schema files if missing. Generates templates.
- `getCurrentIntent()`: Returns `{ mission, mvp, constraints }`
- `validateAll()`: Runs all schemas against all files, returns errors with file/line context
- `exists(intentDir)`: Static method, checks if `.intent/` directory exists

**Sub-stores (one per domain file):**
| Store | Methods |
|---|---|
| MissionStore | `read()`, `write()`, `nextId()` |
| MvpStore | `read()`, `write()`, `nextId()` |
| BacklogStore | `read()`, `write()`, `add(item)`, `update(item)`, `get(id)`, `nextId()`, `search(query)` |
| SpecStore | `read()`, `write()`, `add(node)`, `update(node)`, `get(id)`, `nextId()`, `validateNoCycles()` |
| ConstraintsStore | `read()`, `write()` |
| MetaStore | `append(event)`, `readSince(timestamp)`, `nextId()`, `readAll()` |

### 5.3 Key Operations (Logic Layer)

**`recap.ts` — `generateRecap(store, options)`**
- Input: `IntentStore`, `{ lastSessionTime?: Date, verbosity: "brief" | "full" }`
- Output: `RecapResult { mission, mvpStatus, lastFocus, sinceLastSession, recommendedNext }`
- Reads mission, MVP, specs, meta.jsonl, git log — formats output by verbosity

**`planner.ts` — `suggestNext(store, options)`**
- Input: `IntentStore`, `{ respectDependencies: boolean }`
- Output: `NextSuggestion[]` ranked by value
- Ranking: MVP-critical first → unblocked → fewest deps → continuity with in_progress

**`alignment.ts` — `checkAlignment(store, title, description)`**
- Input: `IntentStore`, idea title, idea description
- Output: `AlignmentCheck { mission, mvp, constraintViolations }`
- Uses LLM call (or heuristic rules in v1) to evaluate alignment

**`design.ts` — `generateDesignDigest(store, specId, options)`**
- Input: `IntentStore`, specId, `{ includeGitHistory: boolean }`
- Output: `DesignDigest { digestId, specId, keyChoices, risks, openQuestions, impactedModules }`
- Uses LLM + git history to generate structured architectural digest

### 5.4 Validation Layer

Every write to `.intent/` passes through AJV with bundled JSON Schemas.

`validateWrite(data, schema, filePath)`:
- Compiles AJV validator from schema
- If invalid: throws `ValidationError` with `filePath` + all error messages
- If valid: returns typed data

> **Enforcement rule:** If validation fails, the skill returns an error to the agent. The agent must fix the input or ask the user. No silent corrections.

---

## 6. Skill Reference v1

These skill definitions are **shared** — both Claude plugin and Pi package implement the same operations:

| Skill | Trigger | Input | Output | Side Effects |
|---|---|---|---|---|
| `intent:recap` | Manual or hook | `verbosity?: "brief" or "full"` | Formatted status message | None |
| `intent:add-idea` | Manual | `title: string, description: string` | Confirmation + idea ID | Writes `backlog.json`, appends meta event |
| `intent:triage` | Manual | `ideaId: string, bucket: enum, overrideAlignment?: boolean` | Classification result | Updates `backlog.json`, appends meta event |
| `intent:next` | Manual | `count?: number` | Ranked spec suggestions | None (read-only) |
| `intent:design-propose` | Manual (or auto-triggered) | `specId: string` | Design digest | Updates spec status, appends meta event |
| `intent:design-approve` | Manual | `specId: string, decision: enum, notes?: string` | Approval confirmation | Updates spec status, appends meta event |
| `intent:status` | Manual | — | Full project dashboard | None (read-only) |

> Deferred to v2: `spec.create`, `spec.update-status`, `git.associate-commit`, `intent.update`, `backlog.merge`, `backlog.archive`

### Skill Logic (Shared Implementation Detail)

**`intent:add-idea`:**
1. Generate next idea ID
2. Create `BacklogItem` with `bucket="untriaged"`
3. Call `store.backlog.add()` + `EventBuilder.backlogAdded()`
4. Return confirmation message

**`intent:triage`:**
1. Look up idea by ID
2. If not `overrideAlignment`: call `checkAlignment()`
3. Update `idea.bucket` and `idea.alignment`
4. Call `store.backlog.update()` + `EventBuilder.backlogTriage()`
5. If bucket is `mvp_critical` but alignment.mvp is not `required`: append warning

**`intent:next`:**
1. Call `suggestNext()` with `respectDependencies=true`
2. Format top N as numbered list with title, ID, MVP alignment, blocked status, rationale

**`intent:design-propose`:**
1. Validate spec is in `draft` or `design_proposed` status
2. Call `generateDesignDigest()`
3. Update spec.status to `design_proposed` + `EventBuilder.designProposed()`

**`intent:design-approve`:**
1. Validate spec is in `design_proposed` status
2. `approved` => `design_approved`; `rejected` => `draft`; `revised` => keep `design_proposed`
3. Call `EventBuilder.designApproved()`

**`intent:status`:**
1. Count MVP completion (items where all linked_specs are `done`)
2. List active specs (`in_progress` or `design_approved`)
3. List unblocked specs, count backlog buckets

---

## 7. Build & Distribution

### 7.1 Package Structure

| Package | Description |
|---|---|
| `@mission-ctrl/core` | npm package, pure TypeScript, no IDE deps |
| `@mission-ctrl/claude-plugin` | Claude Code plugin, depends on core |
| `@mission-ctrl/pi-package` | Pi package, depends on core |
| `@mission-ctrl/mcp-server` | Standalone MCP server (optional), depends on core |

### 7.2 Build Pipeline

GitHub Actions workflow (`release.yml`):
- Trigger: Push tags matching `v*`
- Steps:
  1. Checkout code
  2. Install pnpm dependencies
  3. Run tests
  4. Build all packages
  5. Publish `@mission-ctrl/core` to npm

### 7.3 Project Bootstrap (Shared `intent:init`)

**`intent:init`** skill:
1. Creates `.intent/` directory
2. Copies JSON Schema files from core package
3. Generates template `mission.json`, `mvp.json`, `constraints.json`
4. Creates empty `backlog.json`, `specs.json`, `meta.jsonl`
5. Generates initial context file (`CLAUDE.md` or `AGENTS.md` depending on agent)
6. Records `INTENT_CREATED` event in `meta.jsonl`

---

## 8. Testing Strategy

### 8.1 Core Library Tests

| Test Category | Coverage Target | Tools |
|---|---|---|
| Schema validation | 100% of fields | AJV + jest |
| Business rules | All transitions | jest |
| Store I/O | All CRUD ops | jest + memfs |
| Recap generation | All verbosity modes | jest + fixtures |
| Planner logic | Dependency graphs | jest + graph fixtures |
| Event builder | All event types | jest |

### 8.2 Fixture Repos

Maintain 3 fixture repos in `packages/core/test/fixtures/`:
1. `empty-project/` — Just initialized, no specs
2. `mid-flight/` — 2/3 MVP done, active spec, parked ideas
3. `complex-graph/` — 10+ specs with branching dependencies

---

## 9. Phase-by-Phase Rollout (Core Only)

### Phase 0: Foundation (Week 1)

**Goal:** Core library can read/write/validate all `.intent/` files.

**Deliverables:**
- `packages/core/` scaffolded with TypeScript, pnpm, jest
- JSON Schema files for all 5 domain files + meta
- AJV validation layer with error formatting
- Store classes: `MissionStore`, `MvpStore`, `BacklogStore`, `SpecStore`, `ConstraintsStore`, `MetaStore`
- `IntentStore` orchestrator with `init()`, `validateAll()`
- `EventBuilder` with all v1 event types
- Unit tests for all stores and validation

**Files:**
```
packages/core/src/schemas/*.schema.json
packages/core/src/models/*.ts
packages/core/src/store/*.ts
packages/core/src/events/EventBuilder.ts
packages/core/tests/store/*.test.ts
packages/core/tests/fixtures/
```

**Acceptance criteria:**
- Can create `.intent/` from scratch
- Can read/write all files with validation
- Invalid writes throw with clear error messages
- All schemas pass self-validation

### Phase 1: Logic Layer (Week 2)

**Goal:** Core library can compute recaps, plans, alignment, and design digests.

**Deliverables:**
- `recap.ts` — `generateRecap()` with adaptive verbosity
- `planner.ts` — `suggestNext()` with dependency resolution
- `alignment.ts` — `checkAlignment()` using mission/MVP/constraints
- `design.ts` — `generateDesignDigest()` with git history integration
- Git integration utilities

**Files:**
```
packages/core/src/logic/recap.ts
packages/core/src/logic/planner.ts
packages/core/src/logic/alignment.ts
packages/core/src/logic/design.ts
packages/core/src/utils/git.ts
packages/core/tests/logic/*.test.ts
```

**Acceptance criteria:**
- `generateRecap()` returns correct structure for all 3 fixture repos
- `suggestNext()` never suggests blocked specs
- `checkAlignment()` correctly flags constraint violations
- `generateDesignDigest()` includes real git commits when available

---

## Appendix A: JSON Schemas

### A.1 mission.schema.json
- `id`: string, pattern `^mis_\d{3}$`
- `version`: string, pattern `^v\d+\.\d+$`
- `statement`: string, minLength 10, maxLength 500
- `success_criteria`: array of strings, each minLength 5

### A.2 mvp.schema.json
- `items[].id`: string, pattern `^mvp_\d{3}$`
- `items[].linked_specs`: array of strings (spec IDs)

### A.3 constraints.schema.json
- `constraints[].id`: string, pattern `^con_\d{3}$`
- `constraints[].severity`: enum `["low", "medium", "high", "critical"]`

### A.4 backlog.schema.json
- `items[].id`: string, pattern `^idea_\d{3}$`
- `items[].bucket`: enum `["untriaged", "mvp_critical", "parked", "archived"]`
- `items[].alignment.mission`: enum `["strong", "weak", "neutral", "not_aligned"]`
- `items[].alignment.mvp`: enum `["required", "not_required", "extends"]`

### A.5 specs.schema.json
- `nodes[].id`: string, pattern `^spec_\d{3}$`
- `nodes[].status`: enum `["draft", "design_proposed", "design_approved", "in_progress", "done", "blocked"]`

### A.6 meta.schema.json
- `event_id`: string, pattern `^evt_\d{6}$`
- `actor.type`: enum `["human", "agent"]`
- `affected_entities[].type`: enum `["mission", "mvp", "constraint", "idea", "spec", "digest"]`

---

## Appendix B: Event Catalog

### v1 Required Events

| Event Type | Description | Decision Payload Fields |
|---|---|---|
| INTENT_CREATED | Initial project setup | `mission_version, mvp_version, constraints_version` |
| BACKLOG_ADDED | New idea captured | `title, bucket (always "untriaged")` |
| BACKLOG_TRIAGE | Idea classified | `bucket, priority?, alignment {mission, mvp, constraints}` |
| BACKLOG_MERGED | Duplicate consolidated | `into_idea_id, from_idea_ids[]` |
| BACKLOG_ARCHIVED | Idea retired | `reason` |
| SPEC_CREATED | Spec node added | `spec_title, status: "draft", links {ideas, mvp_items}` |
| SPEC_STATUS_UPDATED | Lifecycle transition | `from, to` |
| SPEC_DEPENDENCY_UPDATED | Graph rewired | `added?: string[], removed?: string[]` |
| DESIGN_PROPOSED | Digest generated | `digest_id, key_choices[], risks[], open_questions[]` |
| DESIGN_APPROVED | Human decision on digest | `digest_id, approval, notes?` |
| DESIGN_REVISED | Digest updated | `digest_id, changes[]` |
| INTENT_UPDATED | Mission/MVP/Constraints change | `field, from, to` |
| OVERRIDE_ACCEPTED | User bypasses guardrail | `rule_broken, reason` |
| GIT_COMMIT_ASSOCIATED | Commit linked to spec | `spec_id, commit_hash` |
| SESSION_STARTED | Auto-onboarding hook fired | `gap_hours, verbosity` |

### v2 Deferred Events

| Event Type | Description |
|---|---|
| BACKLOG_RESURFACED | Parked idea becomes relevant again |
| CONSTRAINT_VIOLATION | Agent detects constraint breach |
| MVP_ITEM_COMPLETED | All linked specs for an MVP item are done |
| DRIFT_DETECTED | System suggests intent update after repeated overrides |

---

*End of Common Specification*
