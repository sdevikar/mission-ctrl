---
description: Capture a raw idea into the untriaged backlog. Use when the user mentions something to build, a feature request, a TODO, or any notion worth tracking before it is scoped.
---

# intent:add-idea

Append one idea to the backlog (`UNTRIAGED` bucket) and emit its event. This
is the entry point of the intent loop — ideas graduate via
`/mission-ctrl:intent-triage`, never straight to code.

## Input

`title` is required (non-empty); `description` is optional free text.

```json
{
  "title": "Offline mode for the CLI",
  "description": "Cache last-known state so reads work without network."
}
```

## Output

```text
{"idea_id": "idea_001", "status": "added"}
```

Use the returned `idea_id` for follow-up triage.

## Invocation

```bash
mission-ctrl skill add-idea --cwd "<project-dir>" <<'EOF'
{"title": "Offline mode for the CLI"}
EOF
```

## Errors

- `NOT_INITIALIZED` — run `/mission-ctrl:intent-init` first.
- `INVALID_INPUT` — e.g. empty title; fix and retry.
