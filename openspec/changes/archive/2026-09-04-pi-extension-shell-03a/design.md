# Design: Pi Extension Shell — Core Loop (M2a)

Component contracts: `docs/design.md` §1–2. This change implements the 7
core-loop skills of `packages/pi-package`. Design-gate skill contracts are
in pi-extension-shell-03b/design.md.

## Key Decisions

- **Direct import, in-process**: skills call `mission_ctrl_core` via normal
  Python imports — no subprocess, no JSON-RPC, no bridge.
- **Reasoning stays in Pi**: alignment verdicts are Pi-produced inputs; skills
  validate and store only.
- **Skill naming**: `intent:<verb>` namespace; manifest in `extension.py`.
- **Hook stubs**: manifest registers `on_session_start` / `on_before_send`
  entry points now so M3 doesn't touch extension wiring.
- **Skills never hand-craft IDs, timestamps, or events** — always via
  `EventBuilder` and store next_id helpers.

## Spec State Machine (M2a subset)

```
draft ──────────────────► in_progress ──► done
  │                            ▲
  └──► blocked ────────────────┘
         ▲
         └── (any state can transition to blocked)
```

The design-gate transitions (draft → design_proposed → design_approved) are
added in M2b. `spec-status` in M2a rejects any attempt to use those states.

## Skill Input/Output Contracts

All inputs and outputs are Pydantic models. Skills return a typed result or
raise `SkillError(code, message)` — never a bare exception.

---

### `intent:init`
| | Type | Notes |
|---|---|---|
| **Input** | `InitInput` | |
| `project_name` | `str` | Used as display name only |
| `mission` | `str \| None` | Optional; can be set later |
| **Output** | `InitResult` | |
| `status` | `Literal["created"]` | |
| `intent_dir` | `str` | Absolute path to `.intent/` |
| **Side effects** | Creates `.intent/`; copies schema templates; emits `INTENT_CREATED` |

---

### `intent:add-idea`
| | Type | Notes |
|---|---|---|
| **Input** | `AddIdeaInput` | |
| `title` | `str` | Required, non-empty |
| `description` | `str \| None` | |
| **Output** | `AddIdeaResult` | |
| `idea_id` | `str` | e.g. `bkl_001` |
| `status` | `Literal["added"]` | |
| **Side effects** | Appends to `backlog.json`; emits `BACKLOG_ADDED` |

---

### `intent:triage`
| | Type | Notes |
|---|---|---|
| **Input** | `TriageInput` | Pi supplies alignment verdict |
| `idea_id` | `str` | Must exist in backlog |
| `bucket` | `Literal["mvp", "later", "rejected"]` | |
| `alignment_verdict` | `str` | Pi's reasoning (stored verbatim) |
| **Output** | `TriageResult` | |
| `idea_id` | `str` | |
| `bucket` | `str` | |
| `status` | `Literal["triaged"]` | |
| **Side effects** | Updates `backlog.json`; emits `BACKLOG_TRIAGE` |

---

### `intent:spec-create`
| | Type | Notes |
|---|---|---|
| **Input** | `SpecCreateInput` | |
| `idea_id` | `str` | Must exist; bucket must be `mvp` or `later` |
| `title` | `str \| None` | Defaults to idea title if omitted |
| **Output** | `SpecCreateResult` | |
| `spec_id` | `str` | e.g. `spec_001` |
| `status` | `Literal["draft"]` | |
| **Side effects** | Appends to `specs.json`; emits `SPEC_CREATED` |

---

### `intent:spec-status`
| | Type | Notes |
|---|---|---|
| **Input** | `SpecStatusInput` | |
| `spec_id` | `str` | Must exist |
| `new_status` | `Literal["in_progress", "done", "blocked"]` | M2a only; design-gate states rejected |
| `note` | `str \| None` | Required when transitioning to `blocked` |
| **Output** | `SpecStatusResult` | |
| `spec_id` | `str` | |
| `previous_status` | `str` | |
| `new_status` | `str` | |
| **Error** | `SkillError(ILLEGAL_TRANSITION)` if transition not in M2a state machine |
| **Side effects** | Updates `specs.json`; emits `SPEC_STATUS_UPDATED` |

---

### `intent:next`
| | Type | Notes |
|---|---|---|
| **Input** | _(none)_ | |
| **Output** | `NextResult` | |
| `spec_id` | `str \| None` | `None` if nothing is actionable |
| `title` | `str` | |
| `reason` | `str` | Human-readable ranking explanation |
| **Side effects** | None (read-only) |

---

### `intent:status`
| | Type | Notes |
|---|---|---|
| **Input** | _(none)_ | |
| **Output** | `StatusResult` | |
| `mission` | `str` | |
| `mvp_completion_pct` | `float` | 0–100 |
| `active_specs` | `list[SpecSummary]` | id, title, status |
| `next_suggestion` | `NextResult` | |
| **Side effects** | None (read-only) |

## Constraints

- No Node.js in the dependency graph; depends only on `mission_ctrl_core`.
- Skills never hand-craft IDs, timestamps, or events.
- All Pydantic models imported from a single `mission_ctrl_pi.schemas` module —
  not redefined inline per skill file.
