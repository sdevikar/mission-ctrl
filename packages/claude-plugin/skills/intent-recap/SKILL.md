---
description: Render a recap of intent state (mission, MVP progress, focus, changes, recommendations). Use when resuming work, after a break, or when context was compacted. Verbosity defaults to standard.
---

# intent:recap

On-demand recap of the current intent state. Same engine as the SessionStart
hook: omit the input for the default `standard` recap, or request `brief`
for a one-glance summary and `full` for changes-since plus event trail.

## Input

All fields optional. `verbosity` is one of `brief`, `standard`, `full`;
`since_iso` is a UTC timestamp bounding the changes window.

```json
{}
```

Example with options:

```text
{"verbosity": "full", "since_iso": "2026-09-01T00:00:00Z"}
```

## Output

Result JSON including the human-readable `rendered` recap text (also what the
SessionStart hook injects). Key fields: `mission`, `mvp_completed`,
`mvp_total`, `mvp_percent`, `last_focus`, `changes`, `recommendations`,
`rendered`.

## Invocation

```bash
mission-ctrl skill recap --cwd "<project-dir>" <<'EOF'
{}
EOF
```

## Errors

- `NOT_INITIALIZED` — run `/mission-ctrl:intent-init` first.
- `INVALID_INPUT` — bad verbosity or timestamp; fix and retry.
