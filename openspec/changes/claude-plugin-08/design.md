# Design: Claude Code Plugin

> Source: https://code.claude.com/docs/en/plugins (verified 2026-09-04).
> Key facts applied: `commands/` is legacy (skills only for new plugins);
> plugin skills invoke as `/<plugin-name>:<skill>`; local testing via
> `claude --plugin-dir` + `/reload-plugins`; gate via
> `claude plugin validate`; `bin/` executables land on the Bash tool PATH;
> hook input arrives as JSON on stdin; matched hooks/exit codes appear in
> the debug log (`claude --debug`).

## Layout (`packages/claude-plugin/`)

```
.claude-plugin/plugin.json     # name: mission-ctrl (namespace for all skills)
skills/
  intent-init/SKILL.md         # … one dir per skill (10 + log-feedback)
  intent-add-idea/SKILL.md
  …
hooks/hooks.json               # SessionStart + UserPromptSubmit matchers
bin/mission-ctrl               # CLI wrapper on the Bash tool PATH (see below)
```

Only `plugin.json` lives inside `.claude-plugin/`; everything else sits at
the plugin root. No `commands/` directory (legacy per upstream docs).

## Skill pattern

Skills are model-invoked: each `SKILL.md` frontmatter `description` carries
`use-when` triggers (e.g. "implement/build/add feature" → route through the
gate, never code first) so Claude reaches for them by task context; explicit
invocation works as `/mission-ctrl:intent-next` with `$ARGUMENTS` passthrough.

The body states the JSON input contract (mirroring the Pydantic schema 1:1)
and delegates execution to the bundled wrapper (on PATH while the plugin is
enabled — no `python3`-on-PATH assumption in skill text):

```bash
mission-ctrl skill <skill-name> --cwd "$CWD" <<'EOF'
<input-json>
EOF
```

`mission-ctrl` shells out to the bridge server (`ts-bridge-07`); exit
non-zero + `{"code","message"}` on stderr for SkillErrors. Skills never embed
Python and never touch `.intent/` directly.

## Hooks

| Claude hook | Behavior (parity with Pi hooks, M3) |
|---|---|
| `SessionStart` | Run session recap for `$CWD` (gap-tiered verbosity); inject output as context; skip silently when no `.intent/` |
| `UserPromptSubmit` | Run before-send check on the stdin-JSON prompt; on `redirect`, prepend the redirect message + block the original prompt from seeding implementation; on `bypass`, annotate visibly |

Hook commands are `{"type": "command"}` entries calling the same `bin/`
wrapper (`hook/session-start`, `hook/before-send` ops), so matcher semantics
stay identical across hosts. Hook input arrives as JSON on stdin; wrapper
parses it (no `jq` dependency — Python stdlib). Verification via the debug
log, which records matched hooks and exit codes.

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
  (`bin/` executables are fine for marketplace distribution; only the
  claude.ai organization-settings route forbids top-level `bin/` — not our
  path.)

## Transport decision (spike pre-resolved from docs)

`bin/mission-ctrl` is a shell wrapper that execs the Python bridge server
directly — no Node runtime needed in plugin scope, no `jq` needed (stdin
JSON parsed with Python stdlib). The remaining spike item is confirming the
exact `hooks.json` matcher schema against the installed 2.1.x CLI.

## Local verification loop (from upstream docs)

1. `claude --plugin-dir ./packages/claude-plugin` (no install step needed;
   repeatable per session; local copy wins over same-named marketplace copies)
2. `/reload-plugins` after every edit — no restart
3. Invoke as `/mission-ctrl:intent-next`; trigger hooks and confirm via
   `claude --debug` matched-hook log
4. Gate with `claude plugin validate ./packages/claude-plugin` (add
   `--strict` in CI later)
