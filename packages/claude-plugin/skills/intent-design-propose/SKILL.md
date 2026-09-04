---
description: Propose a design for a draft spec (draft to design_proposed). Use after scoping a spec and before any implementation. The digest is the design itself, written out, not a pointer to it.
---

# intent:design-propose

Submit the design digest for a `draft` spec, moving it to `design_proposed`.
Write the digest as concrete decisions (data shapes, boundaries, failure
modes) — at least 10 characters of real content, not "see code" or "TBD".
The spec cannot move to `in_progress` until the design is approved.

## Input

- `spec_id` (required)
- `digest` (required): design summary, minimum 10 characters

```json
{
  "spec_id": "spec_001",
  "digest": "Cache JSON snapshot at ~/.cache/app/state.json; reads fall back to snapshot on network error; writes queue for replay."
}
```

## Output

```text
{"spec_id": "spec_001", "status": "design_proposed"}
```

## Invocation

```bash
mission-ctrl skill design-propose --cwd "<project-dir>" <<'EOF'
{"spec_id": "spec_001", "digest": "Cache JSON snapshot at ~/.cache/app/state.json; reads fall back to snapshot on network error."}
EOF
```

## Errors

- `NOT_INITIALIZED` — run `/mission-ctrl:intent-init` first.
- `NOT_FOUND` — unknown `spec_id`.
- `INVALID_INPUT` — digest too short; write the actual design.
- `ILLEGAL_TRANSITION` — spec is not in `draft` (already proposed or
  further along); check status with `/mission-ctrl:intent-status`.
