# Proposal: Claude Code Plugin (dogfood vehicle #1)

## Why

The primary dogfood target is Claude Code (installed: 2.1.59) — not Pi. M4
assumes a usable agent loop, and every M0–M3 milestone was validated
in-process only. A Claude Code plugin makes the intent loop (skills + hooks
+ AGENTS.md sync) directly drivable inside Claude Code sessions, which
unblocks real dogfooding and evidence-based M4 fixes.

No prior proposal exists (only kanban-backlog one-liners and a deleted
early draft) — this change is the first concrete design. Priority #1:
nothing else needs the loop in Claude Code first.

## What Changes

- New `packages/claude-plugin/` distributable plugin:
  - `.claude-plugin/plugin.json` + `skills/*/SKILL.md` (one per intent skill:
    init, add-idea, triage, spec-create, spec-status, design-propose,
    design-approve, next, status, recap, log-feedback) with frontmatter and
    JSON I/O contracts matching the Python schemas.
  - `hooks/hooks.json`: `SessionStart` → session recap injection,
    `UserPromptSubmit` → implementation-intent interception with the same
    redirect ladder and one-phrase override as the Pi hooks.
  - `commands/intent-*.md` slash commands for explicit invocation.
- Execution via `ts-bridge-07` (hard prerequisite): plugin shell/JS calls go
  through the bridge client + `mission_ctrl_bridge` server, so the plugin
  contains zero intent logic — prompts and wiring only.
- Dogfood loop closed in this change: install locally, run this repo's own
  backlog through it, capture issues via `intent:log-feedback`.
- Distribution decided here: local path first; git-based marketplace
  (`marketplace.json`) only after the dogfood week passes.

## Non-goals

- No MCP servers (unchanged backlog item).
- No marketplace publication in this change (local install until dogfood passes).
- No Pi parity work — Pi route is `pi-extension/` from `ts-bridge-07`.
- No new core logic; any missing behavior goes through core/skills first.

## Impact

- Additive: `packages/claude-plugin/` only. Depends on `ts-bridge-07`
  (blocked until the bridge server + client land).
- Requires `log-feedback-06` before the dogfood loop (feedback skill must
  exist to capture issues structurally).
- Supersedes the kanban-backlog line "Claude Code plugin (Node/TS, or
  Python-to-Node bridge — decide when scheduled)": decision made — TS plugin
  shell over the Python bridge, no port.

**Done when:** plugin installed in Claude Code 2.x from local path; full
lifecycle (init → … → design-approve → done) runs via plugin skills;
SessionStart injects a recap; "implement X" is intercepted with override
working; one real dogfood pass logged via `intent:log-feedback`.
