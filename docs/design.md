# Mission Ctrl — Design Doc
## Components, Skill Contracts, Data Model Reference
Status: current source of truth. Supersedes the skill/data-model sections of
`mission-ctrl-common.md`, `mission-ctrl-pi-package.md` (both deleted).

---

## 1. Component Responsibility Matrix

| Component | Responsibility | Depends on | Never does |
|---|---|---|---|
| `IntentStore` | Orchestrates all sub-stores, `init()`, `validate_all()` | Sub-stores | Business logic |
| `MissionStore` / `MvpStore` / `ConstraintsStore` | Read/write single JSON file, validate | pydantic models | Cross-file logic |
| `BacklogStore` | CRUD backlog items, ID generation | pydantic models | Alignment reasoning |
| `SpecStore` | CRUD spec nodes, cycle detection | pydantic models | Status-transition legality (owned by skill) |
| `MetaStore` | Append-only event log I/O | pydantic models | Interpreting events |
| `EventBuilder` | Build valid MetaEvent objects | MetaStore | Decide *what* to log (caller decides) |
| `planner.py` | Rank unblocked specs | SpecStore, MvpStore | Talk to an LLM |
| `recap.py` | Assemble recap payload | All stores, git log (read-only) | Talk to an LLM |
| Pi Skills | Parse Pi input, call core directly, format output | `mission_ctrl_core` | Persist without going through core |
| `on_session_start` hook | Fire recap on session open | Skills | Contain business rules |
| `on_before_send` hook | Intercept implementation-intent messages | Skills, backlog state | Silently allow bypass of backlog-first |
| AGENTS.md Sync | Regenerate context file | Store reads | Get edited manually |

**Rule:** Core is deterministic and network-free. All reasoning (alignment judgment, design digest content) happens in Pi's own context before calling a skill. Core validates and stores; it does not generate.

---

## 2. v1 Skill Set (10)

| Skill | Input | Output | Side Effects | Core call |
|---|---|---|---|---|
| `intent:init` | — | Confirmation | Creates `.intent/`, templates, `INTENT_CREATED` | `IntentStore.init()` |
| `intent:recap` | verbosity? | Formatted recap | None | `recap.generate_recap()` |
| `intent:add-idea` | title, description | idea ID | Writes `backlog.json`, `BACKLOG_ADDED` | `BacklogStore.add()` |
| `intent:triage` | idea_id, bucket, **alignment (Pi-supplied)** | Classification | Updates `backlog.json`, `BACKLOG_TRIAGE` | `BacklogStore.update()` |
| `intent:spec-create` | idea_id | spec ID | Writes `specs.json`, `SPEC_CREATED` | `SpecStore.add()` |
| `intent:spec-status` | spec_id, to-status | Confirmation | Updates `specs.json`, `SPEC_STATUS_UPDATED` | `SpecStore.update()` |
| `intent:design-propose` | spec_id, **digest text (Pi-supplied)** | Stored digest | Status → `design_proposed`, `DESIGN_PROPOSED` | `SpecStore.update()` (validate/store only) |
| `intent:design-approve` | spec_id, decision, notes? | Confirmation | Status transition, `DESIGN_APPROVED` | `SpecStore.update()` |
| `intent:next` | count? | Ranked specs | None | `planner.suggest_next()` |
| `intent:status` | — | Dashboard | None | reads all stores |

`spec-create` and `spec-status` are required in v1 — without them ideas have nowhere to go and specs never reach `done`.

---

## 3. Data Model Reference

Format: JSON files + JSONL. Validation: pydantic models (replaces earlier AJV/JSON-Schema plan — irrelevant once core is Python). IDs: global canonical (`mis_001`, `spec_042`, `evt_000391`). Timestamps: ISO 8601 UTC. Live samples in `docs/examples/domain/` and `docs/examples/meta.jsonl` — unchanged, still valid.

### mission.json
| Field | Type | Required |
|---|---|---|
| id | string (`mis_001`) | Yes |
| version | string (`v1.0`) | Yes |
| statement | string, 1–3 sentences | Yes |
| success_criteria | string[] | No |
| created_at / updated_at | ISO string | Yes |

### mvp.json
| Field | Type | Required |
|---|---|---|
| version | string | Yes |
| items[].id | string (`mvp_001`) | Yes |
| items[].title / description | string | Yes |
| items[].linked_specs | string[] | No |

### constraints.json
| Field | Type | Required |
|---|---|---|
| constraints[].id | string (`con_001`) | Yes |
| constraints[].rule / rationale | string | Yes |
| constraints[].severity | enum: low, medium, high, critical | Yes |
| constraints[].scope | string[] | No |

### backlog.json
| Field | Type | Required |
|---|---|---|
| items[].id | string (`idea_001`) | Yes |
| items[].bucket | enum: untriaged, mvp_critical, parked, archived | Yes |
| items[].alignment.mission | enum: strong, weak, neutral, not_aligned | Yes |
| items[].alignment.mvp | enum: required, not_required, extends | Yes |
| items[].links.specs / links.mvp_items | string[] | No |

### specs.json
| Field | Type | Required |
|---|---|---|
| nodes[].id | string (`spec_001`) | Yes |
| nodes[].status | enum: draft, design_proposed, design_approved, in_progress, done, blocked | Yes |
| nodes[].depends_on | string[] | No |
| nodes[].links.ideas / links.mvp_items | string[] | No |

Status lifecycle: `draft → design_proposed → design_approved → in_progress → done` (can loop back on revision).

Dependency rules (enforced by core):
1. No cycles in `depends_on`.
2. Cannot transition to `in_progress` unless all `depends_on` specs are `done`.
3. Cannot transition to `design_proposed` without a title and ≥1 linked idea or MVP item.

### meta.jsonl
One JSON object per line, no wrapping array.

| Field | Required |
|---|---|
| event_id (`evt_000001`) | Yes |
| timestamp, event_type, actor {type, name} | Yes |
| affected_entities[] {type, id} | Yes |
| linked_intent {mission_id, mvp_version, constraints_version} | Yes |
| decision (shape varies by event_type) | Yes |
| reasoning | Yes |
| depends_on[], git_refs[], tags[] | No |
| session.id | Yes |

---

## 4. Event Catalog (v1)

| Event Type | Emitted by | Decision Payload |
|---|---|---|
| INTENT_CREATED | `intent:init` | mission_version, mvp_version, constraints_version |
| BACKLOG_ADDED | `intent:add-idea` | title, bucket ("untriaged") |
| BACKLOG_TRIAGE | `intent:triage` | bucket, alignment {mission, mvp, constraints} |
| SPEC_CREATED | `intent:spec-create` | spec_title, status "draft", links |
| SPEC_STATUS_UPDATED | `intent:spec-status` | from, to |
| DESIGN_PROPOSED | `intent:design-propose` | digest_id, key_choices[], risks[], open_questions[] |
| DESIGN_APPROVED | `intent:design-approve` | digest_id, approval, notes? |
| SESSION_STARTED | `on_session_start` hook | gap_hours, verbosity |

Deferred to v2: BACKLOG_MERGED, BACKLOG_ARCHIVED, SPEC_DEPENDENCY_UPDATED, DESIGN_REVISED, INTENT_UPDATED, OVERRIDE_ACCEPTED, GIT_COMMIT_ASSOCIATED, BACKLOG_RESURFACED, CONSTRAINT_VIOLATION, MVP_ITEM_COMPLETED, DRIFT_DETECTED.

---

## 5. Hook Behavior

### on_session_start
Fires every time Pi opens a workspace with `.intent/`.

| Gap since last `meta.jsonl` event | Verbosity | Content |
|---|---|---|
| < 1 hour | Ultra-brief | "Welcome back. spec_001 still in progress." |
| 1–24 hours | Brief | Mission one-liner + last focus + next step |
| > 24 hours or first session | Full | Mission + MVP progress + last focus + changes since + recommended next + constraints reminder |

Also appends `SESSION_STARTED`.

### on_before_send (Pi-only, no Claude equivalent)
Fires before every outgoing message.

1. Scan for implementation-intent patterns ("implement X", "build X", "add X feature") — **hardcoded list in v1**.
2. If feature not in backlog → prepend prompt to `add-idea` first.
3. If in backlog but untriaged → prompt to `triage`.
4. If spec exists but design not approved → prompt to `design-propose`.
5. One-phrase override required (e.g. "skip backlog check") to avoid becoming a productivity blocker.

### AGENTS.md sync
Fires after any skill writes to `.intent/`. Regenerates `AGENTS.md` from template below. Never commits — user handles git. File stays < 2KB, regen < 10ms.

```markdown
<!-- Auto-generated by Mission Ctrl. Do not edit manually. -->
<!-- Last updated: {timestamp} -->

# Project Intent

## Mission
{mission.statement}

## MVP ({mvp.version}) — {done}/{total} Complete
- [x] {mvp item 1}
- [ ] {mvp item 2}

## Constraints
- [{severity}] {constraint rule}

## Current Focus
{spec_id} — {spec title} ({status})

## Next Up
- {spec_id} — {spec title} (blocked by {deps} or unblocked)

## Backlog Summary
- MVP-critical: {count} / Parked: {count} / Untriaged: {count}

---
## Agent Instructions
1. All new ideas go to backlog first (intent:add-idea).
2. No implementation before design is approved (intent:design-propose -> intent:design-approve).
3. Prefer MVP items over parked ideas unless explicitly overridden.
4. Respect constraints; if one must be broken, explain why via intent:next.
```

---

## 6. State Ownership Matrix

| File | Written by | Read by |
|---|---|---|
| mission/mvp/constraints.json | Human via `intent:init` / manual edit | All skills, AGENTS.md sync |
| backlog.json | `add-idea`, `triage` | `next`, `status`, AGENTS.md sync |
| specs.json | `spec-create`, `spec-status`, `design-propose`, `design-approve` | `next`, `recap`, `status` |
| meta.jsonl | `EventBuilder` (every skill) | `recap` only |
| AGENTS.md | Sync hook (derived) | Pi's native context loader |

---

## 7. Failure Handling

- Validation fails (pydantic) → typed exception with field-level errors → skill surfaces to Pi verbatim.
- Cycle detected in `depends_on` → reject, name the two spec IDs.
- Illegal status transition → reject with the blocking spec ID.
- `on_before_send` false positive → one-phrase override, documented to the user.
- No silent auto-repair, ever.

---

## 8. Open Decisions

1. `on_before_send` pattern matching: hardcoded list for v1, configurable later.
2. Session boundary: wall-clock gap only, or explicit start/end marker?
3. `.intent/` merge conflict recovery across branches — undocumented.
4. `git_refs`: free-text manual field in v1, or skip until v2?
5. `mission_ctrl_core` packaging: single pip package now; split later only if reuse actually demands it.
