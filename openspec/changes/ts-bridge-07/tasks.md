# Tasks: TypeScript ↔ Python Bridge — ts-bridge-07

## Protocol
- [ ] Freeze protocol v1: request/response/error shapes, op table, `SkillError`
      code pass-through, 1MB line cap, 30s client timeout (in design.md)

## Python server
- [ ] `mission_ctrl_pi/bridge_server.py`: stdio loop, dispatch table for
      10 skills + `hook/session-start` + `hook/before-send` + `sync/agents-md`,
      typed errors (`UNKNOWN_OP`, `BAD_PROTOCOL`, `INTERNAL` without tracebacks)
- [ ] Unit tests: drive `main()` over `StringIO` stdio (all ops incl. error paths)
- [ ] Subprocess smoke test: real `python -m mission_ctrl_bridge` spawn round-trip

## TS client (`packages/bridge/`)
- [ ] `package.json` + `tsconfig` (strict), zero runtime deps, built types
- [ ] `spawnServer` (interpreter resolution) + `request()` with ids + timeout
- [ ] Tests with `node:test` runner: full skill lifecycle on a temp project
      through the client (init → … → design-approve → done)

## Pi adapter (`packages/pi-extension/`)
- [ ] `package.json` (`pi.extensions` entry) + `index.ts`: `session_start`
      recap injection, `input` intercept/redirect/bypass surfacing, `intent-*`
      custom tools via `runSkill`
- [ ] Manual verification: `pi install ./packages/pi-extension` in a scratch
      project, session start injects recap (record transcript in handoff)

## Docs
- [ ] Bridge README (protocol + client API + adding a new op)
- [ ] Update root README install section + kanban backlog (bridge available)
