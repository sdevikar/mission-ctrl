# Design: Pi Extension Shell — Design Gate (M2b)

Builds on pi-extension-shell-03a/design.md. This file covers only the three
additional skills and the full spec state machine including design-gate states.

## Full Spec State Machine (M2a + M2b)

```
draft ──► design_proposed ──► design_approved ──► in_progress ──► done
  ▲               │                                     ▲
  └───────────────┘ (reject)                            │
                                                        │
any state ──────────────────────────────────────► blocked ─┘
```

Transition rules:
- `draft → design_proposed`: via `intent:design-propose`
- `design_proposed → design_approved`: via `intent:design-approve` (decision=approved)
- `design_proposed → draft`: via `intent:design-approve` (decision=rejected); notes required
- `design_approved → in_progress`: via `intent:spec-status`
- `in_progress → done`: via `intent:spec-status`
- `any → blocked`: via `intent:spec-status` (note required)
- `blocked → in_progress`: via `intent:spec-status`

The skill layer is the sole enforcer of transition legality; `SpecStore` stores
whatever the skill passes after validation.

## Skill Input/Output Contracts

---

### `intent:recap`
| | Type | Notes |
|---|---|---|
| **Input** | `RecapInput` | |
| `verbosity` | `Literal["brief", "standard", "full"] \| None` | `None` = auto (hook picks tier) |
| **Output** | `RecapResult` | Defined in `mission_ctrl_core.logic.recap` |
| `mission` | `str` | |
| `mvp_completion_pct` | `float` | |
| `last_focus_spec` | `SpecSummary \| None` | |
| `changes_since` | `list[str]` | Git commit subjects since last session |
| `next_suggestion` | `NextResult` | |
| `verbosity_used` | `Literal["brief", "standard", "full"]` | |
| **Side effects** | None (read-only) |

---

### `intent:design-propose`
| | Type | Notes |
|---|---|---|
| **Input** | `DesignProposeInput` | Pi supplies the digest |
| `spec_id` | `str` | Must exist; current status must be `draft` |
| `digest` | `str` | Pi's design reasoning (stored verbatim, min 10 chars) |
| **Output** | `DesignProposeResult` | |
| `spec_id` | `str` | |
| `status` | `Literal["design_proposed"]` | |
| **Error** | `SkillError(ILLEGAL_TRANSITION)` if spec not in `draft` |
| **Side effects** | Updates `specs.json`; emits `DESIGN_PROPOSED` |

---

### `intent:design-approve`
| | Type | Notes |
|---|---|---|
| **Input** | `DesignApproveInput` | |
| `spec_id` | `str` | Must exist; current status must be `design_proposed` |
| `decision` | `Literal["approved", "rejected"]` | |
| `notes` | `str \| None` | Required when `decision == "rejected"` |
| **Output** | `DesignApproveResult` | |
| `spec_id` | `str` | |
| `decision` | `str` | |
| `new_status` | `Literal["design_approved", "draft"]` | |
| **Error** | `SkillError(NOTES_REQUIRED)` if rejected without notes |
| **Side effects** | Updates `specs.json`; emits `DESIGN_APPROVED` or `DESIGN_REJECTED` |

## Constraints

- `RecapResult` is imported from `mission_ctrl_core` — not redefined here.
- Skills never hand-craft IDs, timestamps, or events.
