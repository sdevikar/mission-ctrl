---
description: Initialize a project's intent store (.intent/ with mission, MVP, constraints). Use when starting Mission Ctrl in a fresh project, when the user asks to set up or initialize intent tracking, or when a skill fails with NOT_INITIALIZED.
---

# intent:init

Create the `.intent/` store for a project: `mission.json`, `mvp.json`,
`constraints.json`, plus empty backlog/specs and the meta event log. Run
once per project; afterwards every other skill requires the store to exist.

## Input

`project_name` is required; `mission` is optional (defaults to a placeholder
statement the user should refine).

```json
{
  "project_name": "my-project",
  "mission": "Ship a fast CLI for log triage."
}
```

## Output

Result JSON on stdout:

```text
{"status": "created", "intent_dir": "<abs path>/.intent"}
```

## Invocation

```bash
mission-ctrl skill init --cwd "<project-dir>" <<'EOF'
{"project_name": "my-project", "mission": "Ship a fast CLI for log triage."}
EOF
```

`mission-ctrl` is on PATH while the plugin is enabled. Never write to
`.intent/` directly — always go through this skill.

## Errors

Errors arrive on stderr as `{"code": "message"}` with a non-zero exit:

- `ALREADY_INITIALIZED` — store exists; do not re-run, use
  `/mission-ctrl:intent-status` to inspect.
- `INVALID_INPUT` — input failed validation (e.g. missing `project_name`);
  fix the input and retry.
