# Mission Ctrl — Technical Roadmap
## Intent-Driven Development Assistant
### v1.0 Implementation Spec | 2026-08-04

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Repository Layout](#2-repository-layout)
3. [Data Model & Schemas](#3-data-model--schemas)
4. [Meta Event Log](#4-meta-event-log)
5. [Core Library](#5-core-library)
6. [Claude Code Plugin](#6-claude-code-plugin)
7. [Skill Reference v1](#7-skill-reference-v1)
8. [Hook Behavior](#8-hook-behavior)
9. [CLAUDE.md Auto-Generation](#9-claudemd-auto-generation)
10. [Build & Distribution](#10-build--distribution)
11. [Testing Strategy](#11-testing-strategy)
12. [Phase-by-Phase Rollout](#12-phase-by-phase-rollout)
13. [Pi Package Migration Path](#13-pi-package-migration-path)
14. [Appendix A: JSON Schemas](#appendix-a-json-schemas)
15. [Appendix B: Event Catalog](#appendix-b-event-catalog)

---

## 1. Architecture Overview

### 1.1 Design Principles

1. **Repo-local state.** All intent artifacts live in `.intent/` at the repository root. No cloud backend, no auth, no network dependency.
2. **Skills are the API.** Every user-facing operation is a skill. The agent never edits `.intent/` files directly.
3. **Hooks guarantee behavior.** Session-start hooks enforce the workflow contract without relying on agent obedience.
4. **Adaptive, not noisy.** The recap hook always fires but adapts its verbosity to session gap and state changes.
5. **One core, multiple surfaces.** `@mission-ctrl/core` is shared. Claude plugin and Pi package are thin wrappers.

### 1.2 High-Level Flow

Developer opens project in Claude Code
        |
        v
  session:start hook (guaranteed by Claude plugin)
        |
        v
  Recap displayed before user types
        |
        v
  Developer works via slash commands:
    /intent:add-idea "progress bar"
    /intent:triage idea_001
    /intent:design-propose spec_001
    /intent:design-approve spec_001
    /intent:next
    /intent:status
        |
        v
  Skills read/write .intent/ via @mission-ctrl/core
        |
        v
  State changes trigger CLAUDE.md auto-regeneration

### 1.3 Component Diagram

+-------------------------------------------------------------+
|                     Claude Code Plugin                         |
|  +--------------+  +--------------+  +----------------------+  |
|  |   Hooks      |  |   Skills     |  |  CLAUDE.md Sync      |  |
|  |  session     |  |  recap       |  |  On state change     |  |
|  |  :start      |  |  add-idea    |  |  Regenerate          |  |
|  |              |  |  triage      |  |  ./CLAUDE.md         |  |
|  |              |  |  next        |  |                      |  |
|  |              |  |  design-     |  |                      |  |
|  |              |  |   propose    |  |                      |  |
|  |              |  |  design-     |  |                      |  |
|  |              |  |   approve    |  |                      |  |
|  |              |  |  status      |  |                      |  |
|  +------+-------+  +------+-------+  +----------+-----------+  |
|         |                 |                     |                |
|         +-----------------+---------------------+                |
|                           |                                    |
|                    +------+------+                             |
|                    |  @mission-  |                             |
|                    |  ctrl/core  |  <- Shared TypeScript lib    |
|                    |  (npm pkg)  |                             |
|                    +------+------+                             |
+---------------------------+------------------------------------+
                            |
                    +-------+-------+
                    |    .intent/    |
                    |  mission.json  |
                    |  mvp.json      |
                    |  backlog.json  |
                    |  specs.json    |
                    |  constraints.  |
                    |    json        |
                    |  meta.jsonl    |
                    |  schemas/      |
+--------------------+----------------

---

## 2. Repository Layout

### 2.1 Monorepo Structure

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
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── claude-plugin/           # Claude Code plugin
│   │   ├── src/
│   │   │   ├── index.ts         # Plugin manifest
│   │   │   ├── hooks/
│   │   │   │   └── sessionStart.ts
│   │   │   ├── skills/
│   │   │   │   ├── recap.ts
│   │   │   │   ├── addIdea.ts
│   │   │   │   ├── triage.ts
│   │   │   │   ├── next.ts
│   │   │   │   ├── designPropose.ts
│   │   │   │   ├── designApprove.ts
│   │   │   │   └── status.ts
│   │   │   ├── sync/
│   │   │   │   └── claudeMdSync.ts
│   │   │   └── types.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── pi-package/              # Pi package (v2)
│       └── ...
│
├── docs/
│   └── concept.md               # Already exists
│
├── .github/
│   └── workflows/
│       ├── test.yml
│       └── release.yml
│
├── package.json                 # Root monorepo config
├── pnpm-workspace.yaml
└── README.md

### 2.2 Runtime Layout (Inside User's Project)

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
├── CLAUDE.md                    # Auto-generated from .intent/
├── .gitignore                   # Should ignore nothing in .intent/
└── ...

Important: .intent/ is NOT gitignored. These files are meant to be committed and shared.

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

Example:
{
  "id": "mis_001",
  "version": "v1.0",
  "statement": "Build an end-to-end export system that allows users to reliably generate and download large datasets.",
  "success_criteria": [
    "User can trigger an export without timeouts",
    "Exports complete asynchronously and are retrievable later",
    "Failures are clearly communicated to the user"
  ],
  "created_at": "2026-03-10T10:15:00Z",
  "updated_at": "2026-03-10T10:15:00Z"
}

Fields:
| Field | Type | Required | Description |
|---|---|---|---|
| id | string | Yes | Global canonical ID, format mis_001 |
| version | string | Yes | Semver-ish, e.g. v1.0 |
| statement | string | Yes | 1-3 sentence mission statement |
| success_criteria | string[] | No | Concrete outcomes that prove mission success |
| created_at | ISO string | Yes | Initial creation |
| updated_at | ISO string | Yes | Last modification |

### 3.3 File: mvp.json

Purpose: Concrete must-haves. "Product stands up" means all items are done.

Example:
{
  "version": "v1.0",
  "items": [
    {
      "id": "mvp_001",
      "title": "Asynchronous export execution",
      "description": "Exports run in the background and do not block user interaction.",
      "linked_specs": ["spec_001"]
    },
    {
      "id": "mvp_002",
      "title": "Export result retrieval",
      "description": "Users can download completed exports after processing.",
      "linked_specs": ["spec_002"]
    },
    {
      "id": "mvp_003",
      "title": "Basic failure reporting",
      "description": "Users receive clear errors when an export fails.",
      "linked_specs": ["spec_003"]
    }
  ],
  "created_at": "2026-03-10T10:20:00Z",
  "updated_at": "2026-03-10T10:20:00Z"
}

Fields:
| Field | Type | Required | Description |
|---|---|---|---|
| version | string | Yes | Tracks MVP revision |
| items | MVPItem[] | Yes | Ordered list of must-haves |
| items[].id | string | Yes | Format mvp_001 |
| items[].title | string | Yes | Short name |
| items[].description | string | Yes | What "done" means |
| items[].linked_specs | string[] | No | Traceability to specs |
| created_at | ISO string | Yes | |
| updated_at | ISO string | Yes | |

### 3.4 File: constraints.json

Purpose: Guardrails that shape implementation choices.

Example:
{
  "version": "v1.0",
  "constraints": [
    {
      "id": "con_001",
      "rule": "Keep architecture simple; avoid introducing new services unless strictly necessary.",
      "rationale": "Early complexity increases maintenance cost and slows iteration.",
      "severity": "high",
      "scope": ["backend", "infrastructure"]
    },
    {
      "id": "con_002",
      "rule": "Avoid elaborate automated tests until core export flows are stable.",
      "rationale": "Optimize for learning speed during early development.",
      "severity": "medium",
      "scope": ["testing"]
    }
  ],
  "created_at": "2026-03-10T10:25:00Z",
  "updated_at": "2026-03-10T10:25:00Z"
}

Fields:
| Field | Type | Required | Description |
|---|---|---|---|
| version | string | Yes | |
| constraints | Constraint[] | Yes | |
| constraints[].id | string | Yes | Format con_001 |
| constraints[].rule | string | Yes | The guardrail text |
| constraints[].rationale | string | Yes | Why this constraint exists |
| constraints[].severity | enum | Yes | low, medium, high, critical |
| constraints[].scope | string[] | No | Tags like backend, frontend, testing, infrastructure |

### 3.5 File: backlog.json

Purpose: Single inventory of all ideas. Enforces backlog-first workflow.

Example:
{
  "items": [
    {
      "id": "idea_001",
      "title": "Show export progress bar",
      "description": "Display progress while export is running.",
      "bucket": "parked",
      "alignment": {
        "mission": "weak",
        "mvp": "not_required",
        "constraints": ["con_001"]
      },
      "links": {
        "specs": [],
        "mvp_items": []
      },
      "created_at": "2026-03-11T09:00:00Z",
      "updated_at": "2026-03-11T09:30:00Z"
    },
    {
      "id": "idea_002",
      "title": "Async export queue",
      "description": "Run exports asynchronously via a job queue.",
      "bucket": "mvp_critical",
      "alignment": {
        "mission": "strong",
        "mvp": "required",
        "constraints": []
      },
      "links": {
        "specs": ["spec_001"],
        "mvp_items": ["mvp_001"]
      },
      "created_at": "2026-03-11T09:05:00Z",
      "updated_at": "2026-03-11T09:05:00Z"
    }
  ]
}

Fields:
| Field | Type | Required | Description |
|---|---|---|---|
| items | BacklogItem[] | Yes | |
| items[].id | string | Yes | Format idea_001 |
| items[].title | string | Yes | |
| items[].description | string | Yes | |
| items[].bucket | enum | Yes | untriaged, mvp_critical, parked, archived |
| items[].alignment | object | Yes | |
| items[].alignment.mission | enum | Yes | strong, weak, neutral, not_aligned |
| items[].alignment.mvp | enum | Yes | required, not_required, extends |
| items[].alignment.constraints | string[] | No | IDs of constraints that apply |
| items[].links.specs | string[] | No | Linked spec IDs |
| items[].links.mvp_items | string[] | No | Linked MVP item IDs |
| items[].created_at | ISO string | Yes | |
| items[].updated_at | ISO string | Yes | |

Bucket Semantics:
- untriaged — Just captured, not yet evaluated
- mvp_critical — Required for MVP. Prioritize.
- parked — Potentially valuable, but defer until MVP stable
- archived — Misaligned or obsolete. Kept for audit trail.

### 3.6 File: specs.json

Purpose: The canonical dependency graph. The source of truth for what can be worked on next.

Example:
{
  "nodes": [
    {
      "id": "spec_001",
      "title": "Async export execution",
      "status": "design_approved",
      "depends_on": [],
      "links": {
        "ideas": ["idea_002"],
        "mvp_items": ["mvp_001"]
      }
    },
    {
      "id": "spec_002",
      "title": "Export download endpoint",
      "status": "draft",
      "depends_on": ["spec_001"],
      "links": {
        "ideas": [],
        "mvp_items": ["mvp_002"]
      }
    },
    {
      "id": "spec_003",
      "title": "Basic export error reporting",
      "status": "draft",
      "depends_on": ["spec_001"],
      "links": {
        "ideas": [],
        "mvp_items": ["mvp_003"]
      }
    }
  ],
  "updated_at": "2026-03-12T14:00:00Z"
}

Fields:
| Field | Type | Required | Description |
|---|---|---|---|
| nodes | SpecNode[] | Yes | |
| nodes[].id | string | Yes | Format spec_001 |
| nodes[].title | string | Yes | |
| nodes[].status | enum | Yes | draft, design_proposed, design_approved, in_progress, done, blocked |
| nodes[].depends_on | string[] | No | IDs of specs that must complete first |
| nodes[].links | object | No | |
| nodes[].links.ideas | string[] | No | Source backlog ideas |
| nodes[].links.mvp_items | string[] | No | Linked MVP items |
| updated_at | ISO string | Yes | Last structural change |

Status Lifecycle:
  draft -> design_proposed -> design_approved -> in_progress -> done
     ^______________|
     (can loop back on revision)

Dependency Rules (Enforced by Core):
1. No cycles in depends_on graph.
2. A spec cannot transition to in_progress unless all depends_on specs are done.
3. A spec cannot transition to design_proposed unless it has a title and at least one linked idea or MVP item.

### 3.7 File: meta.jsonl

Purpose: Append-only decision log. Answers "why is it true?"

Each line is a valid JSON object. No wrapping array.

Example lines:
{"event_id":"evt_000001","timestamp":"2026-03-10T10:15:00Z","event_type":"INTENT_CREATED","actor":{"type":"human","name":"owner"},"affected_entities":[{"type":"mission","id":"mis_001"},{"type":"mvp","id":"mvp_set_v1"},{"type":"constraints","id":"con_set_v1"}],"linked_intent":{"mission_id":"mis_001","mvp_version":"v1.0","constraints_version":"v1.0"},"decision":{"mission_version":"v1.0"},"reasoning":"Initialize project intent so all subsequent work can be evaluated against Mission -> MVP -> Constraints.","depends_on":[],"git_refs":[],"tags":["bootstrap"],"session":{"id":"ses_0001"}}
{"event_id":"evt_000002","timestamp":"2026-03-11T09:05:00Z","event_type":"BACKLOG_ADDED","actor":{"type":"human","name":"owner"},"affected_entities":[{"type":"idea","id":"idea_002"}],"linked_intent":{"mission_id":"mis_001","mvp_version":"v1.0","constraints_version":"v1.0"},"decision":{"title":"Async export queue","bucket":"untriaged"},"reasoning":"Capture idea first to enforce backlog-first and prevent premature implementation.","depends_on":["evt_000001"],"git_refs":[],"tags":["backlog"],"session":{"id":"ses_0002"}}

Fields:
| Field | Type | Required | Description |
|---|---|---|---|
| event_id | string | Yes | Format evt_000001 |
| timestamp | ISO string | Yes | When the decision was recorded |
| event_type | enum | Yes | See Appendix B for full catalog |
| actor | object | Yes | Who/what made the decision |
| actor.type | enum | Yes | human, agent |
| actor.name | string | Yes | Identifier (e.g. owner, intent-skill) |
| affected_entities | EntityRef[] | Yes | What changed |
| affected_entities[].type | enum | Yes | mission, mvp, constraint, idea, spec, digest |
| affected_entities[].id | string | Yes | Global canonical ID |
| linked_intent | object | Yes | Intent snapshot at time of decision |
| linked_intent.mission_id | string | Yes | |
| linked_intent.mvp_version | string | Yes | |
| linked_intent.constraints_version | string | Yes | |
| decision | object | Yes | The actual decision payload (shape varies by event_type) |
| reasoning | string | Yes | Human-readable rationale. Must be concise. |
| depends_on | string[] | No | Previous event IDs this decision depends on |
| git_refs | string[] | No | Commit hashes, branch names |
| tags | string[] | No | Classification tags |
| session | object | Yes | |
| session.id | string | Yes | Session identifier |

---

## 4. Meta Event Log

### 4.1 Why JSONL

- Append-only: O(1) write, no read-modify-write
- Stream-friendly: Can tail, filter, grep
- Git-friendly: Line-oriented diffs
- Recoverable: Corrupt line doesn't break the whole file

### 4.2 Event Catalog (v1 Subset)

Only these event types are required for v1 correctness:

| Event Type | When Emitted | Decision Payload |
|---|---|---|
| INTENT_CREATED | Project bootstrap | { mission_version, mvp_version, constraints_version } |
| BACKLOG_ADDED | New idea captured | { title, bucket: "untriaged" } |
| BACKLOG_TRIAGE | Idea classified | { bucket, priority?, alignment } |
| BACKLOG_MERGED | Duplicate consolidated | { into_idea_id, from_idea_ids[] } |
| BACKLOG_ARCHIVED | Idea retired | { reason } |
| SPEC_CREATED | Spec node added | { spec_title, status: "draft", links } |
| SPEC_STATUS_UPDATED | Lifecycle transition | { from, to } |
| SPEC_DEPENDENCY_UPDATED | Graph rewired | { added?: string[], removed?: string[] } |
| DESIGN_PROPOSED | Digest generated | { digest_id, key_choices[], risks[], open_questions[] } |
| DESIGN_APPROVED | Human approves | { digest_id, approval: "approved" or "rejected" or "revised", notes? } |
| DESIGN_REVISED | Digest updated | { digest_id, changes[] } |
| INTENT_UPDATED | Mission/MVP/Constraints change | { field, from, to } |
| OVERRIDE_ACCEPTED | User bypasses guardrail | { rule_broken, reason } |
| GIT_COMMIT_ASSOCIATED | Commit linked to spec | { spec_id, commit_hash } |

Deferred to v2: BACKLOG_RESURFACED, CONSTRAINT_VIOLATION, MVP_ITEM_COMPLETED, DRIFT_DETECTED

### 4.3 Event Builder API (Core Library)

The EventBuilder class in packages/core/src/events/EventBuilder.ts provides methods for each event type:

- backlogAdded(idea: BacklogItem) -> MetaEvent
- backlogTriage(idea: BacklogItem, oldBucket: string) -> MetaEvent
- specCreated(spec: SpecNode, fromIdeaId?: string) -> MetaEvent
- specStatusUpdated(specId: string, from: string, to: string) -> MetaEvent
- designProposed(digest: DesignDigest) -> MetaEvent
- designApproved(specId: string, decision: string, notes?: string) -> MetaEvent
- intentUpdated(field: string, from: unknown, to: unknown) -> MetaEvent
- overrideAccepted(rule: string, reason: string) -> MetaEvent

Each method:
1. Generates the next event_id (sequential counter)
2. Sets timestamp to now
3. Injects actor, linked_intent, and session from constructor options
4. Appends to meta.jsonl via MetaStore
5. Returns the complete event object

---

## 5. Core Library

### 5.1 Responsibilities

The core library is stateless between calls and agent-agnostic. It:
1. Reads/writes .intent/ files
2. Validates all writes against JSON Schema
3. Enforces business rules (no cycles, status transitions, etc.)
4. Generates meta events
5. Computes recaps, plans, and alignment checks
6. Exposes a clean TypeScript API

### 5.2 Store API

IntentStore (packages/core/src/store/IntentStore.ts)
- Constructor takes { intentDir: string }
- Exposes: mission, mvp, backlog, specs, constraints, meta (sub-stores)
- init(): Creates .intent/ dir and schema files if missing. Generates templates.
- getCurrentIntent(): Returns { mission, mvp, constraints }
- validateAll(): Runs all schemas against all files, returns errors with file/line context
- exists(intentDir): Static method, checks if .intent/ directory exists

Sub-stores (one per domain file):
- MissionStore: read(), write(), nextId()
- MvpStore: read(), write(), nextId()
- BacklogStore: read(), write(), add(item), update(item), get(id), nextId(), search(query)
- SpecStore: read(), write(), add(node), update(node), get(id), nextId(), validateNoCycles()
- ConstraintsStore: read(), write()
- MetaStore: append(event), readSince(timestamp), nextId(), readAll()

### 5.3 Key Operations (Logic Layer)

recap.ts — generateRecap(store, options)
- Input: IntentStore, { lastSessionTime?: Date, verbosity: "brief" | "full" }
- Output: RecapResult { mission, mvpStatus, lastFocus, sinceLastSession, recommendedNext }
- Behavior:
  - Reads mission.json for statement
  - Reads mvp.json, counts items where all linked_specs are "done"
  - Reads specs.json, finds spec with status "in_progress" (last focus)
  - Reads meta.jsonl, filters events since lastSessionTime
  - Reads git log, filters commits since lastSessionTime
  - Calls suggestNext() for recommended next step
  - Formats output based on verbosity

planner.ts — suggestNext(store, options)
- Input: IntentStore, { respectDependencies: boolean }
- Output: NextSuggestion[] ranked by value
- Ranking criteria (in order):
  1. MVP-critical specs first
  2. Unblocked specs (all depends_on are "done")
  3. Fewest remaining dependencies
  4. Linked to current in_progress spec (continuity)
- Never suggests blocked specs unless respectDependencies is false

alignment.ts — checkAlignment(store, title, description)
- Input: IntentStore, idea title, idea description
- Output: AlignmentCheck { mission, mvp, constraintViolations }
- Behavior:
  - Uses LLM call (or heuristic rules in v1) to compare idea text against mission statement
  - Checks if idea title/description matches any MVP item keywords
  - Checks if idea violates any constraint rules (keyword matching)
  - Returns structured alignment assessment

design.ts — generateDesignDigest(store, specId, options)
- Input: IntentStore, specId, { includeGitHistory: boolean }
- Output: DesignDigest { digestId, specId, keyChoices, risks, openQuestions, impactedModules }
- Behavior:
  - Reads spec node and linked ideas/MVP items
  - Reads git history for files touched by recent commits
  - Uses LLM to generate: key architectural choices, risks, open questions, impacted modules
  - Returns structured digest

### 5.4 Validation Layer

Every write to .intent/ passes through AJV with the bundled JSON Schemas.

validateWrite(data, schema, filePath):
- Compiles AJV validator from schema
- If invalid: throws ValidationError with filePath + all error messages
- If valid: returns typed data

Enforcement rule: If validation fails, the skill returns an error to the agent. The agent must fix the input or ask the user. No silent corrections.

---

## 6. Claude Code Plugin

### 6.1 Plugin Manifest

File: packages/claude-plugin/src/index.ts

Exports a plugin object with:
- name: "mission-ctrl"
- version: "1.0.0"
- description: "Intent-driven development assistant for Claude Code"
- hooks: { "session:start": sessionStartHook, "file:write": claudeMdSyncHook }
- skills: [recap, addIdea, triage, next, designPropose, designApprove, status]
- mcpServers: [optional standalone MCP server reference]

### 6.2 Hook: Session Start

File: packages/claude-plugin/src/hooks/sessionStart.ts

Behavior:
1. Check if .intent/ exists in workspace root. If not, inject message suggesting /intent:init.
2. Detect last session time by reading the most recent meta.jsonl event timestamp.
3. Compute gap in hours.
4. Determine verbosity:
   - < 1 hour -> "ultra-brief"
   - 1-24 hours -> "brief"
   - > 24 hours or first session -> "full"
5. Call generateRecap() with detected parameters.
6. Inject formatted recap message into chat before user types.
7. Append SESSION_STARTED event to meta.jsonl.

### 6.3 Skill Specifications

/intent:recap
- Trigger: Manual or hook
- Input: verbosity?: "brief" | "full"
- Output: Formatted status message
- Side Effects: None
- Implementation: Calls generateRecap() from core

/intent:add-idea
- Trigger: Manual
- Input: title: string, description: string
- Output: Confirmation + assigned idea ID
- Side Effects: Writes to backlog.json, appends BACKLOG_ADDED meta event
- Implementation:
  1. Generate next idea ID
  2. Create BacklogItem with bucket="untriaged"
  3. Call store.backlog.add()
  4. Call EventBuilder.backlogAdded()
  5. Return confirmation message

/intent:triage
- Trigger: Manual
- Input: ideaId: string, bucket: "mvp_critical"|"parked"|"archived", overrideAlignment?: boolean
- Output: Classification result with alignment summary
- Side Effects: Updates backlog.json, appends BACKLOG_TRIAGE meta event
- Implementation:
  1. Look up idea by ID
  2. If not overrideAlignment: call checkAlignment() using idea title/description
  3. Update idea.bucket and idea.alignment
  4. Call store.backlog.update()
  5. Call EventBuilder.backlogTriage()
  6. If bucket is mvp_critical but alignment.mvp is not "required": append warning
  7. Return result message

/intent:next
- Trigger: Manual
- Input: count?: number (default 3)
- Output: Ranked list of suggested next specs
- Side Effects: None (read-only)
- Implementation:
  1. Call suggestNext() from core with respectDependencies=true
  2. Take top N results
  3. Format as numbered list with title, ID, MVP alignment, blocked status, rationale
  4. Return formatted message

/intent:design-propose
- Trigger: Manual (or auto-triggered before code generation)
- Input: specId: string
- Output: Design digest with key choices, risks, open questions, impacted modules
- Side Effects: Updates spec status to "design_proposed", appends DESIGN_PROPOSED meta event
- Implementation:
  1. Look up spec by ID
  2. Validate spec is in "draft" or "design_proposed" status
  3. Call generateDesignDigest() from core
  4. Update spec.status to "design_proposed"
  5. Call store.specs.update()
  6. Call EventBuilder.designProposed()
  7. Return formatted digest

/intent:design-approve
- Trigger: Manual
- Input: specId: string, decision: "approved"|"rejected"|"revised", notes?: string
- Output: Approval confirmation with next step guidance
- Side Effects: Updates spec status, appends DESIGN_APPROVED meta event
- Implementation:
  1. Look up spec by ID
  2. Validate spec is in "design_proposed" status
  3. If approved: set status to "design_approved"
  4. If rejected: set status to "draft"
  5. If revised: keep status as "design_proposed"
  6. Call store.specs.update()
  7. Call EventBuilder.designApproved()
  8. Return confirmation with appropriate next step message

/intent:status
- Trigger: Manual
- Input: None
- Output: Full project dashboard
- Side Effects: None (read-only)
- Implementation:
  1. Read all domain state
  2. Count MVP completion (items where all linked_specs are "done")
  3. List active specs (in_progress or design_approved)
  4. List unblocked specs (design_approved with all dependencies done)
  5. Count backlog buckets
  6. Return formatted dashboard

---

## 7. Skill Reference v1

| Skill | Trigger | Input | Output | Side Effects |
|---|---|---|---|---|
| /intent:recap | Manual or hook | verbosity?: "brief" or "full" | Formatted status message | None |
| /intent:add-idea | Manual | title: string, description: string | Confirmation + idea ID | Writes backlog.json, appends meta event |
| /intent:triage | Manual | ideaId: string, bucket: enum, overrideAlignment?: boolean | Classification result | Updates backlog.json, appends meta event |
| /intent:next | Manual | count?: number | Ranked spec suggestions | None (read-only) |
| /intent:design-propose | Manual (or auto-triggered) | specId: string | Design digest | Updates spec status, appends meta event |
| /intent:design-approve | Manual | specId: string, decision: enum, notes?: string | Approval confirmation | Updates spec status, appends meta event |
| /intent:status | Manual | — | Full project dashboard | None (read-only) |

Deferred to v2: spec.create, spec.update-status, git.associate-commit, intent.update, backlog.merge, backlog.archive

---

## 8. Hook Behavior

### 8.1 Session Start Hook

Fires: Every time Claude Code opens a workspace containing .intent/

Behavior:
1. Check .intent/ exists. If not, suggest /intent:init.
2. Detect last session time (from meta.jsonl or CLAUDE.md metadata).
3. Compute time gap.
4. Determine verbosity: brief (< 4h gap) or full (>= 4h gap or first session).
5. Generate and inject recap message.
6. Record SESSION_STARTED event in meta.jsonl.

Adaptive Recap Rules:

| Gap | Verbosity | Content |
|---|---|---|
| < 1 hour | Ultra-brief | "Welcome back. spec_001 still in progress." |
| 1-24 hours | Brief | Mission one-liner + last focus + next step |
| > 24 hours | Full | Mission + MVP progress + last focus + changes since + recommended next + constraints reminder |
| First ever | Full + bootstrap | Full recap + "This project uses Mission Ctrl. Here's how it works..." |

### 8.2 File Write Hook (CLAUDE.md Sync)

Fires: After any skill writes to .intent/

Behavior:
1. Read current .intent/ state.
2. Regenerate ./CLAUDE.md from templates.
3. Write to disk.
4. Do NOT commit — let the user handle git.

---

## 9. CLAUDE.md Auto-Generation

### 9.1 Purpose

CLAUDE.md serves as a cache of intent state in the agent's system prompt. Even when the agent doesn't explicitly call skills, it has mission/MVP/constraints in context. This reduces drift during free-form conversation.

### 9.2 Template Structure

<!-- Auto-generated by Mission Ctrl. Do not edit manually. -->
<!-- Last updated: {timestamp} -->

# Project Intent

## Mission
{mission.statement}

## MVP ({mvp.version}) — {done}/{total} Complete
- [x] {mvp item 1}
- [ ] {mvp item 2}
- [ ] {mvp item 3}

## Constraints
- [{severity}] {constraint rule}
- [{severity}] {constraint rule}

## Current Focus
{spec_id} — {spec title} ({status})

## Next Up
- {spec_id} — {spec title} (blocked by {deps} or unblocked)

## Backlog Summary
- MVP-critical: {count}
- Parked: {count}
- Untriaged: {count}

---

## Agent Instructions

When working on this project:
1. All new ideas must be captured to backlog first (/intent:add-idea).
2. Before implementing any spec, ensure design is approved (/intent:design-propose -> /intent:design-approve).
3. Prefer completing MVP items over parked ideas unless explicitly overridden.
4. Respect constraints. If a constraint must be broken, use /intent:next and explain why.

### 9.3 Sync Strategy

Trigger: After every skill write to .intent/
Performance: File is < 2KB. Regeneration is < 10ms.
Git impact: CLAUDE.md changes appear in git diff alongside intent changes. This is intentional.

---

## 10. Build & Distribution

### 10.1 Package Structure

@mission-ctrl/core        — npm package, pure TypeScript, no IDE deps
@mission-ctrl/claude-plugin — Claude Code plugin, depends on core
@mission-ctrl/pi-package    — Pi package (v2), depends on core
@mission-ctrl/mcp-server    — Standalone MCP server (optional), depends on core

### 10.2 Build Pipeline

GitHub Actions workflow (release.yml):
- Trigger: Push tags matching v*
- Steps:
  1. Checkout code
  2. Install pnpm dependencies
  3. Run tests
  4. Build all packages
  5. Publish @mission-ctrl/core to npm
  6. Publish @mission-ctrl/claude-plugin to npm

### 10.3 Claude Plugin Installation

Via marketplace:
  /plugin install mission-ctrl@claude-plugins-official

Via npm (bleeding edge):
  /plugin install npm:@mission-ctrl/claude-plugin

Local development:
  /plugin install ./packages/claude-plugin

### 10.4 Project Bootstrap

When a user first enables Mission Ctrl in a project:
  /intent:init

This skill:
1. Creates .intent/ directory
2. Copies JSON Schema files from core package
3. Generates template mission.json, mvp.json, constraints.json
4. Creates empty backlog.json, specs.json, meta.jsonl
5. Generates initial CLAUDE.md
6. Records INTENT_CREATED event in meta.jsonl

The user then edits mission.json and mvp.json to define their project.

---

## 11. Testing Strategy

### 11.1 Core Library Tests

| Test Category | Coverage Target | Tools |
|---|---|---|
| Schema validation | 100% of fields | AJV + jest |
| Business rules | All transitions | jest |
| Store I/O | All CRUD ops | jest + memfs |
| Recap generation | All verbosity modes | jest + fixtures |
| Planner logic | Dependency graphs | jest + graph fixtures |
| Event builder | All event types | jest |

### 11.2 Plugin Tests

| Test Category | Approach |
|---|---|
| Skill parameter parsing | Unit tests with mock context |
| Hook behavior | Integration tests with temp directories |
| CLAUDE.md sync | Snapshot tests |
| End-to-end workflow | Script that runs full lifecycle on temp repo |

### 11.3 Fixture Repos

Maintain 3 fixture repos in packages/core/test/fixtures/:
1. empty-project/ — Just initialized, no specs
2. mid-flight/ — 2/3 MVP done, active spec, parked ideas
3. complex-graph/ — 10+ specs with branching dependencies

All tests run against these fixtures for deterministic behavior.

---

## 12. Phase-by-Phase Rollout

### Phase 0: Foundation (Week 1)

Goal: Core library can read/write/validate all .intent/ files.

Deliverables:
- packages/core/ scaffolded with TypeScript, pnpm, jest
- JSON Schema files for all 5 domain files + meta
- AJV validation layer with error formatting
- Store classes: MissionStore, MvpStore, BacklogStore, SpecStore, ConstraintsStore, MetaStore
- IntentStore orchestrator with init(), validateAll()
- EventBuilder with all v1 event types
- Unit tests for all stores and validation

Files to create:
  packages/core/src/schemas/*.schema.json
  packages/core/src/models/*.ts
  packages/core/src/store/*.ts
  packages/core/src/events/EventBuilder.ts
  packages/core/tests/store/*.test.ts
  packages/core/tests/fixtures/*/mission.json (etc.)

Acceptance criteria:
- Can create .intent/ from scratch
- Can read/write all files with validation
- Invalid writes throw with clear error messages
- All schemas pass self-validation

---

### Phase 1: Logic Layer (Week 2)

Goal: Core library can compute recaps, plans, alignment, and design digests.

Deliverables:
- recap.ts — generateRecap() with adaptive verbosity
- planner.ts — suggestNext() with dependency resolution
- alignment.ts — checkAlignment() using mission/MVP/constraints
- design.ts — generateDesignDigest() with git history integration
- Git integration utilities (read log, infer touched specs)
- Unit tests for all logic modules

Files to create:
  packages/core/src/logic/recap.ts
  packages/core/src/logic/planner.ts
  packages/core/src/logic/alignment.ts
  packages/core/src/logic/design.ts
  packages/core/src/utils/git.ts
  packages/core/tests/logic/*.test.ts

Acceptance criteria:
- generateRecap() returns correct structure for all 3 fixture repos
- suggestNext() never suggests blocked specs
- checkAlignment() correctly flags constraint violations
- generateDesignDigest() includes real git commits when available

---

### Phase 2: Claude Plugin Shell (Week 3)

Goal: Plugin installs in Claude Code and exposes skills.

Deliverables:
- packages/claude-plugin/ scaffolded
- Plugin manifest with all 7 skills registered
- Stub skill implementations (read-only, no core integration yet)
- Local installation and manual testing in Claude Code
- README with installation instructions

Files to create:
  packages/claude-plugin/src/index.ts
  packages/claude-plugin/src/skills/*.ts
  packages/claude-plugin/package.json
  packages/claude-plugin/tsconfig.json

Acceptance criteria:
- /plugin install ./packages/claude-plugin succeeds
- All 7 /intent:* commands appear in Claude Code skill palette
- Stub skills return placeholder text

---

### Phase 3: Skill Integration (Week 4)

Goal: All skills wired to core library, full CRUD working.

Deliverables:
- recap skill calls generateRecap()
- add-idea skill writes to backlog.json + meta
- triage skill updates backlog.json + meta
- next skill calls suggestNext()
- design-propose skill generates digest + updates spec status
- design-approve skill updates spec status
- status skill aggregates full project state
- Error handling: validation failures, missing files, invalid IDs
- Integration tests for full workflows

Files modified:
  packages/claude-plugin/src/skills/*.ts

Acceptance criteria:
- Can run full lifecycle: init -> add idea -> triage -> design propose -> design approve -> next -> status
- All state changes are reflected in .intent/ files
- All decisions are recorded in meta.jsonl
- Invalid inputs return clear errors, not silent failures

---

### Phase 4: Hooks & Auto-Onboarding (Week 5)

Goal: Session start hook fires automatically. CLAUDE.md sync works.

Deliverables:
- sessionStartHook implementation
- Last session detection (meta.jsonl timestamp parsing)
- Adaptive recap formatting
- file:write hook for CLAUDE.md regeneration
- CLAUDE.md template and sync logic
- Hook integration tests

Files to create:
  packages/claude-plugin/src/hooks/sessionStart.ts
  packages/claude-plugin/src/sync/claudeMdSync.ts
  packages/claude-plugin/src/hooks/__tests__/sessionStart.test.ts

Acceptance criteria:
- Opening a project with .intent/ auto-injects recap message
- Recap is brief for recent sessions, full for long gaps
- After any skill write, CLAUDE.md updates within 1 second
- CLAUDE.md accurately reflects current mission, MVP, constraints, active specs

---

### Phase 5: Polish & Release (Week 6)

Goal: Plugin is installable from marketplace, documented, tested.

Deliverables:
- README with screenshots/gifs of workflow
- Marketplace submission to claude-plugins-official
- CI/CD pipeline (test -> build -> publish)
- Example project with pre-populated .intent/
- Troubleshooting guide
- Video walkthrough (optional but recommended)

Files:
  README.md
  CHANGELOG.md
  examples/todo-app/.intent/*

Acceptance criteria:
- /plugin install mission-ctrl@claude-plugins-official works for beta testers
- 3+ external users can complete full workflow without assistance
- No critical bugs in 48 hours of real-world usage

---

### Phase 6: Pi Package (Weeks 7-8)

Goal: Same functionality available in Pi.

Deliverables:
- packages/pi-package/ scaffolded
- Pi extension with session:start hook
- Pi skills mapped to same core API
- AGENTS.md template generation
- pi install npm:@mission-ctrl/pi-package works
- Documentation for Pi-specific features

Files:
  packages/pi-package/src/extension.ts
  packages/pi-package/src/skills/*.ts
  packages/pi-package/templates/AGENTS.md

Acceptance criteria:
- Pi auto-loads AGENTS.md from project directory
- All 7 skills work in Pi interactive mode
- Session start hook fires recap automatically

---

### Phase 7: Advanced Features (Weeks 9-12)

Goal: v2 features that deepen the system.

Deliverables:
- spec.create and spec.update-status skills
- git.associate-commit skill + auto-inference
- intent.update skill (collaborative renegotiation)
- backlog.merge and backlog.archive skills
- Standalone MCP server (@mission-ctrl/mcp-server)
- Drift detection: agent suggests intent update after repeated overrides
- Analytics: velocity tracking, constraint violation frequency
- Multi-user: shared intent state for team repos

---

## 13. Pi Package Migration Path

### 13.1 Reuse Strategy

The Pi package reuses @mission-ctrl/core entirely. The wrapper is thin:

| Claude Component | Pi Equivalent |
|---|---|
| Plugin manifest | package.json with pi field |
| Hooks | Extension lifecycle hooks |
| Skills | Pi skill definitions |
| CLAUDE.md sync | AGENTS.md generation |

### 13.2 Pi-Specific Additions

1. AGENTS.md auto-generation — Pi loads this natively from project dir
2. Message interception — Pi extensions can filter/modify agent messages before sending. Use this to enforce backlog-first: intercept "implement X" -> redirect to "add idea X to backlog first?"
3. Tree navigation — Pi's tree-structured history can correlate with meta.jsonl for decision archaeology
4. Context engineering — Pi's minimal system prompt makes intent injection more effective

### 13.3 Pi Extension Structure

File: packages/pi-package/src/extension.ts

Exports an extension object with:
- name: "mission-ctrl"
- version: "1.0.0"
- hooks:
  - onSessionStart: Fires recap auto-onboarding
  - onBeforeSend: Intercepts implementation requests to enforce backlog-first
- skills: Same 7 skills wrapped for Pi's skill API

---

## Appendix A: JSON Schemas

### A.1 mission.schema.json

Required fields: id, version, statement, created_at, updated_at
- id: string, pattern "^mis_\d{3}$"
- version: string, pattern "^v\d+\.\d+$"
- statement: string, minLength 10, maxLength 500
- success_criteria: array of strings, each minLength 5
- created_at: ISO 8601 string
- updated_at: ISO 8601 string

### A.2 mvp.schema.json

Required fields: version, items, created_at, updated_at
- version: string
- items: array of MVPItem objects
  - id: string, pattern "^mvp_\d{3}$"
  - title: string
  - description: string
  - linked_specs: array of strings (spec IDs)
- created_at: ISO 8601 string
- updated_at: ISO 8601 string

### A.3 constraints.schema.json

Required fields: version, constraints, created_at, updated_at
- version: string
- constraints: array of Constraint objects
  - id: string, pattern "^con_\d{3}$"
  - rule: string
  - rationale: string
  - severity: enum ["low", "medium", "high", "critical"]
  - scope: array of strings
- created_at: ISO 8601 string
- updated_at: ISO 8601 string

### A.4 backlog.schema.json

Required fields: items
- items: array of BacklogItem objects
  - id: string, pattern "^idea_\d{3}$"
  - title: string
  - description: string
  - bucket: enum ["untriaged", "mvp_critical", "parked", "archived"]
  - alignment: object
    - mission: enum ["strong", "weak", "neutral", "not_aligned"]
    - mvp: enum ["required", "not_required", "extends"]
    - constraints: array of strings (constraint IDs)
  - links: object
    - specs: array of strings (spec IDs)
    - mvp_items: array of strings (MVP item IDs)
  - created_at: ISO 8601 string
  - updated_at: ISO 8601 string

### A.5 specs.schema.json

Required fields: nodes, updated_at
- nodes: array of SpecNode objects
  - id: string, pattern "^spec_\d{3}$"
  - title: string
  - status: enum ["draft", "design_proposed", "design_approved", "in_progress", "done", "blocked"]
  - depends_on: array of strings (spec IDs)
  - links: object
    - ideas: array of strings (idea IDs)
    - mvp_items: array of strings (MVP item IDs)
- updated_at: ISO 8601 string

### A.6 meta.schema.json

Required fields: event_id, timestamp, event_type, actor, affected_entities, linked_intent, decision, reasoning, session
- event_id: string, pattern "^evt_\d{6}$"
- timestamp: ISO 8601 string
- event_type: enum [all v1 event types listed in Appendix B]
- actor: object
  - type: enum ["human", "agent"]
  - name: string
- affected_entities: array of objects
  - type: enum ["mission", "mvp", "constraint", "idea", "spec", "digest"]
  - id: string
- linked_intent: object
  - mission_id: string
  - mvp_version: string
  - constraints_version: string
- decision: object (shape varies by event_type)
- reasoning: string
- depends_on: array of strings (event IDs)
- git_refs: array of strings
- tags: array of strings
- session: object
  - id: string

---

## Appendix B: Event Catalog

### v1 Required Events

| Event Type | Description | Decision Payload Fields |
|---|---|---|
| INTENT_CREATED | Initial project setup | mission_version, mvp_version, constraints_version |
| BACKLOG_ADDED | New idea captured | title, bucket (always "untriaged") |
| BACKLOG_TRIAGE | Idea classified | bucket, priority?, alignment {mission, mvp, constraints} |
| BACKLOG_MERGED | Duplicate consolidated | into_idea_id, from_idea_ids[] |
| BACKLOG_ARCHIVED | Idea retired | reason |
| SPEC_CREATED | Spec node added | spec_title, status: "draft", links {ideas, mvp_items} |
| SPEC_STATUS_UPDATED | Lifecycle transition | from, to |
| SPEC_DEPENDENCY_UPDATED | Graph rewired | added?: string[], removed?: string[] |
| DESIGN_PROPOSED | Digest generated | digest_id, key_choices[], risks[], open_questions[] |
| DESIGN_APPROVED | Human decision on digest | digest_id, approval: "approved"/"rejected"/"revised", notes? |
| DESIGN_REVISED | Digest updated | digest_id, changes[] |
| INTENT_UPDATED | Mission/MVP/Constraints change | field, from, to |
| OVERRIDE_ACCEPTED | User bypasses guardrail | rule_broken, reason |
| GIT_COMMIT_ASSOCIATED | Commit linked to spec | spec_id, commit_hash |
| SESSION_STARTED | Auto-onboarding hook fired | gap_hours, verbosity |

### v2 Deferred Events

| Event Type | Description |
|---|---|
| BACKLOG_RESURFACED | Parked idea becomes relevant again |
| CONSTRAINT_VIOLATION | Agent detects constraint breach |
| MVP_ITEM_COMPLETED | All linked specs for an MVP item are done |
| DRIFT_DETECTED | System suggests intent update after repeated overrides |

---

*End of Roadmap*
