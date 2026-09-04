---
description: Approve or reject a proposed design (design_proposed to design_approved or back to draft). Use when reviewing a design digest. Rejections require notes.
---

# intent:design-approve

Decide on a `design_proposed` spec. `approved` moves it to `design_approved`
(unlocks `in_progress`); `rejected` returns it to `draft` and requires
`notes` explaining what must change.

## Input

- `spec_id` (required)
- `decision` (required): `approved` or `rejected`
- `notes` (optional, required on rejection)

```json
{
  "spec_id": "spec_001",
  "decision": "approved"
}
```

## Output

`new_status` is `design_approved` on approval, `draft` on rejection.

```text
{"spec_id": "spec_001", "decision": "approved", "new_status": "design_approved"}
```

## Invocation

```bash
mission-ctrl skill design-approve --cwd "<project-dir>" <<'EOF'
{"spec_id": "spec_001", "decision": "approved"}
EOF
```

## Errors

- `NOT_INITIALIZED` — run `/mission-ctrl:intent-init` first.
- `NOT_FOUND` — unknown `spec_id`.
- `ILLEGAL_TRANSITION` — spec has no proposed design to decide on.
- `NOTES_REQUIRED` — rejection without notes; say what must change.
