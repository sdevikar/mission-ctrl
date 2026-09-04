# Design: Claude Code Plugin

## Layout (`packages/claude-plugin/`)

```
.claude-plugin/plugin.json     # name, version, description
skills/
  intent-init/SKILL.md         # … one dir per skill (10 + log-feedback)
  intent-add-idea/SKILL.md
  …
hooks/hooks.json               # SessionStart + UserPromptSubmit matchers
commands/intent-next.md        # … slash commands for explicit invocation
```

## Skill pattern

Each `SKILL.md` carries `name`, `description` (with Claude-oriented
"use-when" triggers, e.g. "implement/build/add feature" → route through the
gate, never code first), and an `allowed-tools` note. The body states the
JSON input contract (mirroring the Pydantic schema 1:1) and delegates
execution to the bridge:

```bash
echo '<input-json>' | mission-ctrl skill <skill-name> --cwd "$CWD"
```

where `mission-ctrl` is the bridge CLI wrapper (from `ts-bridge-07`;
exit non-zero + `{"code","message"}` stderr on SkillError). Skills never
embed Python and never touch `.intent/` directly.

## Hooks

| Claude hook | Behavior (parity with Pi hooks, M3) |
|---|---|
| `SessionStart` | Run session recap for `$CWD` (gap-tiered verbosity); inject output as context; skip silently when no `.intent/` |
| `UserPromptSubmit` | Run before-send check on the prompt; on `redirect`, prepend the redirect message + block the original prompt from seeding implementation; on `bypass`, annotate visibly |

Hook scripts are thin shell over the bridge (`hook/session-start`,
`hook/before-send` ops) so matcher semantics stay identical across hosts.

## State ownership (unchanged)

`.intent/` files remain the only state; `AGENTS.md` sync runs post-skill via
the bridge's `sync/agents-md` op (same template + sanitization as M3 — the
plugin reuses it, does not reimplement it).

## Constraints

- Plugin contains prompts + wiring only; any new behavior lands in
  core/skills/bridge first.
- Input contracts pin to the Python schema field names; schema drift fails
  the contract test (see tasks).
- Local-path install until dogfood passes; marketplace file afterwards.

## Open questions (spike first)

1. Exact `plugin.json` / `hooks.json` schema for Claude Code 2.1.x (verify
   against installed CLI, not memory).
2. Whether hook scripts should call the Python server directly (fewer moving
   parts, needs `python3` + installed packages) or via the Node client
   (uniform errors, needs `node`) — spike decides, design records it.
