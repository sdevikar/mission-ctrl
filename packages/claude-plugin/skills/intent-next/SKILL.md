---
description: Suggest the single next actionable spec with its reason. Use when asking what to work on next, after finishing a spec, or at session start alongside the recap.
---

# intent:next

Return the top suggestion from the planner (dependency order, design-gate
state, MVP linkage). Takes no input. When the suggestion names a spec that
is not `in_progress`, transition it first with
`/mission-ctrl:intent-spec-status` — one spec in progress at a time.

## Input

None. Send an empty object:

```json
{}
```

## Output

`spec_id` is `null` when nothing is actionable.

```text
{"spec_id": "spec_001", "title": "Offline reads", "reason": "design-approved and unblocked; unblocks spec_002"}
```

## Invocation

```bash
mission-ctrl skill next --cwd "<project-dir>" <<'EOF'
{}
EOF
```

## Errors

- `NOT_INITIALIZED` — run `/mission-ctrl:intent-init` first.
- `INVALID_INPUT` — non-empty input sent; this skill takes none.
