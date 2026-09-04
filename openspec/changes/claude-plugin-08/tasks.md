# Tasks: Claude Code Plugin — claude-plugin-08 (PRIO #1 for dogfooding)

## Prerequisites (not this change — do first)
- [ ] `ts-bridge-07`: bridge server + client landed (plugin executes through it)
- [ ] `log-feedback-06`: `intent:log-feedback` exists (dogfood issues need it)

## Spike (verify before building)
- [x] Confirm `plugin.json` / `hooks.json` matcher schema against installed
      Claude Code 2.1.x (`claude --plugin-dir` + `claude --debug` matched-hook
      log); record findings in design.md and close the transport decision
      → done via hooks reference + official examples; transport = direct
      in-process import, bridge-compatible op shape
- [x] Scaffold via `claude plugin init`-equivalent layout manually under
      `packages/claude-plugin/` (repo-owned, not ~/.claude)

## Plugin scaffold
- [x] `packages/claude-plugin/`: `.claude-plugin/plugin.json` (name
      `mission-ctrl`), `hooks/`, `skills/`, `bin/` layout; loads via
      `claude --plugin-dir` with no install step
- [x] `bin/mission-ctrl` wrapper: `skill`, `hook/session-start`,
      `hook/before-send`, `sync/agents-md` through the bridge server;
      SkillErrors to stderr JSON + non-zero exit
      → implemented direct (bridge pending); smoke-tested init → add-idea →
      intercept/bypass on a temp project

## Skills (one SKILL.md each, JSON contracts mirroring Pydantic schemas)
- [x] `intent:init`, `intent:add-idea`, `intent:triage`
- [x] `intent:spec-create`, `intent:spec-status`
- [x] `intent:design-propose`, `intent:design-approve`
- [x] `intent:next`, `intent:status`, `intent:recap`, `intent:log-feedback`
      → log-feedback SKILL.md pins the planned contract, marked Pending
      (lands in log-feedback-06)

## Hooks
- [x] `SessionStart` recap injection (skip silently without `.intent/`)
- [x] `UserPromptSubmit` intercept/redirect/bypass (parity with M3 ladder)

## Contract tests + dogfood
- [x] Contract test: every SKILL.md input block validates against its Pydantic
      schema (drift fails the build)
      → `test_claude_plugin_contracts.py`, 7 tests green
- [x] `claude plugin validate ./packages/claude-plugin` passes (gate; `--strict`
      in CI later) → passed on Claude Code 2.1.59
- [ ] Dogfood pass: load via `claude --plugin-dir`, `/reload-plugins` after
      edits, run a real feature end-to-end in this repo, confirm hooks in the
      `--debug` log, log all issues via `intent:log-feedback`
      (blocked: needs log-feedback-06 + an interactive Claude Code session)
- [ ] Update kanban (Claude plugin row) + root README (Claude install path)
