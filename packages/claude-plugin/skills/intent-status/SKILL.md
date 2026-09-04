---
description: Show mission statement, MVP completion, active specs, and the next suggestion. Use for status check-ins, before planning, or when orienting in a project.
---

# intent:status

Read-only snapshot: mission text, MVP completion percentage, active specs,
and the planner's next suggestion. Takes no input. Never edits state.

## Input

None. Send an empty object:

```json
{}
```

## Output

```text
{"mission": "...", "mvp_completion_pct": 25.0, "active_specs": [{"id": "spec_001", "title": "...", "status": "in_progress"}], "next_suggestion": {"spec_id": "spec_002", "title": "...", "reason": "..."}}
```

## Invocation

```bash
mission-ctrl skill status --cwd "<project-dir>" <<'EOF'
{}
EOF
```

## Errors

- `NOT_INITIALIZED` — run `/mission-ctrl:intent-init` first.
- `INVALID_INPUT` — non-empty input sent; this skill takes none.
