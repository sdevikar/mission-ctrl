---
description: Triage one backlog idea into mvp, later, or rejected with an alignment verdict. Use when untriaged ideas exist, after add-idea, or when the user asks what is in scope.
---

# intent:triage

Move one idea out of `UNTRIAGED` into its bucket. The `alignment_verdict`
is a short human judgment of fit with the mission — write it honestly, it
becomes the audit trail for scope decisions.

## Input

- `idea_id` (required): e.g. `idea_001`
- `bucket` (required): one of `mvp`, `later`, `rejected`
- `alignment_verdict` (required): one sentence on mission fit

```json
{
  "idea_id": "idea_001",
  "bucket": "mvp",
  "alignment_verdict": "Core to the offline-first mission; ship in v1."
}
```

## Output

```text
{"idea_id": "idea_001", "bucket": "mvp", "status": "triaged"}
```

## Invocation

```bash
mission-ctrl skill triage --cwd "<project-dir>" <<'EOF'
{"idea_id": "idea_001", "bucket": "mvp", "alignment_verdict": "Core to the offline-first mission; ship in v1."}
EOF
```

## Errors

- `NOT_INITIALIZED` — run `/mission-ctrl:intent-init` first.
- `NOT_FOUND` — unknown `idea_id`; list ideas via
  `/mission-ctrl:intent-status` first.
- `INVALID_INPUT` — bad bucket or missing verdict; fix and retry.
