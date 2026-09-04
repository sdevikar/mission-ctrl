---
description: Create a draft spec from a triaged idea. Use when an mvp or later idea is ready to be scoped, or when the user asks to spec something out.
---

# intent:spec-create

Create one `draft` spec linked to a triaged idea. The idea must already be
out of `UNTRIAGED` (bucket `mvp` or `later`); triage first otherwise. Specs
start in `draft` and enter the design gate via
`/mission-ctrl:intent-design-propose` — never straight to implementation.

## Input

- `idea_id` (required)
- `title` (optional): overrides the idea title for the spec

```json
{
  "idea_id": "idea_001",
  "title": "Offline reads from local cache"
}
```

## Output

```text
{"spec_id": "spec_001", "status": "draft"}
```

## Invocation

```bash
mission-ctrl skill spec-create --cwd "<project-dir>" <<'EOF'
{"idea_id": "idea_001"}
EOF
```

## Errors

- `NOT_INITIALIZED` — run `/mission-ctrl:intent-init` first.
- `NOT_FOUND` — unknown `idea_id`.
- `INVALID_INPUT` — idea still untriaged or in a rejected bucket; triage it
  into `mvp`/`later` first.
