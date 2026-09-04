# Proposal: TypeScript ↔ Python Bridge (generic Node client)

## Why

Pi 0.84 loads TypeScript extensions only (`package.json` + `pi.extensions`
entry, `index.ts` event API) — our pure-Python `extension.py` MANIFEST cannot
load there, which blocks all Pi dogfooding. At the same time `mission_ctrl_core`
must stay the single system of record: porting it to TypeScript duplicates
validation, planner, and recap logic (`docs/architecture.md` §6, option (b)).

The fix is option (a) from that section, built once and shared: a generic
Node client + Python stdio server speaking a versioned JSON protocol. Any
Node host — the Pi extension adapter, OpenSpec CLI integrations, a future
dashboard — drives core through the same client with zero logic duplication.

## What Changes

- New `packages/bridge/` npm package (`mission-ctrl-bridge`): thin TS client
  (`runSkill`, `sessionStart`, `beforeSend`, `syncAgentsMd`, `getStatus`) over
  newline-delimited JSON on stdio. No validation, no ranking, no templates —
  all behavior stays in Python.
- New Python server entry point (`python -m mission_ctrl_bridge`, living in
  `mission_ctrl_pi`): reads `{"id","op","input","cwd"}` requests, dispatches
  to the 10 skills + 3 hook functions + AGENTS.md sync, replies
  `{"id","ok","result"}` or `{"id","ok":false,"code","message"}` (SkillError
  round-trips; Python tracebacks never leak, they map to `INTERNAL`).
- New `packages/pi-extension/` TS adapter: Pi-native `index.ts` (subscribes
  to `session_start` / `input` events, registers one custom tool per skill)
  implemented entirely on the bridge client. `pi install ./packages/pi-extension`
  becomes the supported Pi route; `extension.py` MANIFEST stays as the
  in-process Python API for tests and scripts.
- Protocol versioned (`protocol: 1` in handshake); server rejects unknown ops
  and unknown protocol versions with typed errors.

## Non-goals

- No business logic in TypeScript — client is serialization + spawn only.
- No port of `mission_ctrl_core`; no MCP servers (still backlog).
- No Windows-specific spawn handling beyond portable Node APIs.
- No PyPI/npm publication in this change (local-path install + `uv run` only;
  publishing stays in M4).

## Impact

- Additive: `packages/bridge/`, `packages/pi-extension/`, one server module
  in `mission_ctrl_pi`. No changes to core; no new Python dependencies
  (server uses stdlib `json`/`sys` only).
- Prerequisite for `claude-plugin-08` (Claude hooks/shell call the same
  server) and any OpenSpec-side Node integration.

**Done when:** a Node script runs the full skill lifecycle against a temp
project purely through the bridge; `pi install ./packages/pi-extension`
loads in real Pi and session start injects a recap; per-call overhead
< 500ms locally.
