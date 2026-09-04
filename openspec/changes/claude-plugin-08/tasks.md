# Tasks: Claude Code Plugin — claude-plugin-08 (PRIO #1 for dogfooding)

## Prerequisites (not this change — do first)
- [ ] `ts-bridge-07`: bridge server + client landed (plugin executes through it)
- [ ] `log-feedback-06`: `intent:log-feedback` exists (dogfood issues need it)

## Spike (verify before building)
- [ ] Confirm `plugin.json` / skills / `hooks.json` / commands schema against
      installed Claude Code 2.1.x (`claude --version`, local docs); record
      findings in design.md Open questions and resolve them
- [ ] Decide hook transport: direct Python server stdio vs Node client
      (document trade-off + pick one)

## Plugin scaffold
- [ ] `packages/claude-plugin/`: `.claude-plugin/plugin.json`, `hooks/`,
      `skills/`, `commands/` layout; local install works in Claude Code

## Skills (one SKILL.md each, JSON contracts mirroring Pydantic schemas)
- [ ] `intent:init`, `intent:add-idea`, `intent:triage`
- [ ] `intent:spec-create`, `intent:spec-status`
- [ ] `intent:design-propose`, `intent:design-approve`
- [ ] `intent:next`, `intent:status`, `intent:recap`, `intent:log-feedback`

## Hooks + commands
- [ ] `SessionStart` recap injection (skip silently without `.intent/`)
- [ ] `UserPromptSubmit` intercept/redirect/bypass (parity with M3 ladder)
- [ ] `commands/intent-*.md` slash commands for explicit invocation

## Contract tests + dogfood
- [ ] Contract test: every SKILL.md input block validates against its Pydantic
      schema (drift fails the build)
- [ ] Dogfood pass: install locally, run a real feature end-to-end in this
      repo, log all issues via `intent:log-feedback`
- [ ] Update kanban (Claude plugin row) + root README (Claude install path)
