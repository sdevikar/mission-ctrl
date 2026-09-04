# Tasks: Claude Code Plugin — claude-plugin-08 (PRIO #1 for dogfooding)

## Prerequisites (not this change — do first)
- [ ] `ts-bridge-07`: bridge server + client landed (plugin executes through it)
- [ ] `log-feedback-06`: `intent:log-feedback` exists (dogfood issues need it)

## Spike (verify before building)
- [ ] Confirm `plugin.json` / `hooks.json` matcher schema against installed
      Claude Code 2.1.x (`claude --plugin-dir` + `claude --debug` matched-hook
      log); record findings in design.md and close the transport decision
- [ ] Scaffold via `claude plugin init`-equivalent layout manually under
      `packages/claude-plugin/` (repo-owned, not ~/.claude)

## Plugin scaffold
- [ ] `packages/claude-plugin/`: `.claude-plugin/plugin.json` (name
      `mission-ctrl`), `hooks/`, `skills/`, `bin/` layout; loads via
      `claude --plugin-dir` with no install step
- [ ] `bin/mission-ctrl` wrapper: `skill`, `hook/session-start`,
      `hook/before-send`, `sync/agents-md` through the bridge server;
      SkillErrors to stderr JSON + non-zero exit

## Skills (one SKILL.md each, JSON contracts mirroring Pydantic schemas)
- [ ] `intent:init`, `intent:add-idea`, `intent:triage`
- [ ] `intent:spec-create`, `intent:spec-status`
- [ ] `intent:design-propose`, `intent:design-approve`
- [ ] `intent:next`, `intent:status`, `intent:recap`, `intent:log-feedback`

## Hooks
- [ ] `SessionStart` recap injection (skip silently without `.intent/`)
- [ ] `UserPromptSubmit` intercept/redirect/bypass (parity with M3 ladder)

## Contract tests + dogfood
- [ ] Contract test: every SKILL.md input block validates against its Pydantic
      schema (drift fails the build)
- [ ] `claude plugin validate ./packages/claude-plugin` passes (gate; `--strict`
      in CI later)
- [ ] Dogfood pass: load via `claude --plugin-dir`, `/reload-plugins` after
      edits, run a real feature end-to-end in this repo, confirm hooks in the
      `--debug` log, log all issues via `intent:log-feedback`
- [ ] Update kanban (Claude plugin row) + root README (Claude install path)
