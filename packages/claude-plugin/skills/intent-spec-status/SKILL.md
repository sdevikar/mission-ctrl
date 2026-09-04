---
description: Transition a spec between in_progress, done, and blocked. Use when starting work on a design-approved spec, finishing it, or when work stalls. Respects dependency order and the design gate.
---

# intent:spec-status

Move a spec to `in_progress`, `done`, or `blocked` (a note is required when
blocking). Only `design_approved` specs may move to `in_progress`, only one
spec may be `in_progress` at a time, and a spec cannot start while its
dependencies are unfinished.

## Input

- `spec_id` (required)
- `new_status` (required): one of `in_progress`, `done`, `blocked`
- `note` (optional, required when blocking): why it is blocked

```json
{
  "spec_id": "spec_001",
  "new_status": "in_progress"
}
```

## Output

```text
{"spec_id": "spec_001", "previous_status": "design_approved", "new_status": "in_progress"}
```

## Invocation

```bash
mission-ctrl skill spec-status --cwd "<project-dir>" <<'EOF'
{"spec_id": "spec_001", "new_status": "in_progress"}
EOF
```

## Errors

- `NOT_INITIALIZED` — run `/mission-ctrl:intent-init` first.
- `NOT_FOUND` — unknown `spec_id`.
- `INVALID_INPUT` — e.g. blocking without a note; add the note and retry.
- `ILLEGAL_TRANSITION` — gate or dependency rule refused the move (spec not
  design-approved, another spec in progress, unfinished dependency). The
  message says which rule fired — route back through the gate instead of
  forcing it.
