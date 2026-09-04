# mission-ctrl — Claude Code plugin

Intent layer for coding sessions: backlog, specs, design gate, recaps, and
implementation-intent interception, driven inside Claude Code. Prompts and
wiring only — all logic lives in `mission_ctrl_core` / `mission_ctrl_pi`.

## Layout

- `.claude-plugin/plugin.json` — manifest (namespace `mission-ctrl`, so skills
  invoke as `/mission-ctrl:intent-next`)
- `skills/intent-*/SKILL.md` — one per intent skill, JSON I/O contracts
  mirroring the Pydantic schemas 1:1
- `hooks/hooks.json` — `SessionStart` recap injection, `UserPromptSubmit`
  implementation-intent interception
- `bin/mission-ctrl` — runtime wrapper on the Bash tool PATH (stdlib only)

## Prerequisites

- Python 3.11+ with the repo deps installed (`uv sync` from the repo root)
- The plugin directory inside the `mission-ctrl` checkout (the wrapper
  locates `packages/core` and `packages/pi-package` relative to itself, or
  via `MISSION_CTRL_ROOT`)

## Try it locally (no install)

```bash
claude --plugin-dir ./packages/claude-plugin
```

Then `/mission-ctrl:intent-status` (needs a project with `.intent/` — run
`/mission-ctrl:intent-init` first). After edits, `/reload-plugins` picks them
up without a restart. Hook activity is recorded in the debug log
(`claude --debug`).

## Validate

```bash
claude plugin validate ./packages/claude-plugin
```

## Skills

| Skill | Operation |
|---|---|
| `/mission-ctrl:intent-init` | create `.intent/` store |
| `/mission-ctrl:intent-add-idea` | capture untriaged idea |
| `/mission-ctrl:intent-triage` | bucket idea (mvp/later/rejected) |
| `/mission-ctrl:intent-spec-create` | draft spec from triaged idea |
| `/mission-ctrl:intent-spec-status` | move spec (in_progress/done/blocked) |
| `/mission-ctrl:intent-design-propose` | submit design digest |
| `/mission-ctrl:intent-design-approve` | approve/reject design |
| `/mission-ctrl:intent-next` | planner's next suggestion |
| `/mission-ctrl:intent-status` | read-only snapshot |
| `/mission-ctrl:intent-recap` | on-demand recap |
| `/mission-ctrl:intent-log-feedback` | pending `log-feedback-06` |

Invocation pattern (also what each SKILL.md instructs):

```bash
mission-ctrl skill <name> --cwd "<project-dir>" <<'EOF'
{<input JSON>}
EOF
```

Errors: stderr `{"code","message"}` + non-zero exit
(`NOT_INITIALIZED`, `NOT_FOUND`, `INVALID_INPUT`, `ILLEGAL_TRANSITION`,
`NOTES_REQUIRED`, `ALREADY_INITIALIZED`, `NOT_IMPLEMENTED`, `INTERNAL`).

## Hooks

- `SessionStart` → gap-tiered recap injected as context; silent when the
  project has no `.intent/`.
- `UserPromptSubmit` → implementation intent (`implement`, `build`, …) is
  blocked with a redirect to the closest-to-code skill; re-send with the
  phrase `override intent` to proceed (the bypass is logged).

## Contract test

`packages/pi-package/tests/test_claude_plugin_contracts.py` validates every
SKILL.md json input block against its Pydantic schema — doc/schema
drift fails the build.
