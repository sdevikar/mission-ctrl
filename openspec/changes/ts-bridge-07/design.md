# Design: TypeScript ↔ Python Bridge

## Protocol (v1, NDJSON over stdio)

Client spawns `python -m mission_ctrl_bridge --cwd <project>` (cwd may also
ride per-request) and exchanges single-line JSON messages (`json.dumps`
output never contains raw newlines).

Request: `{"id": "<n>", "protocol": 1, "op": "<op>", "input": {...}, "cwd": "<abs>"}`

Response: `{"id": "<n>", "ok": true, "result": {...}}`
Error: `{"id": "<n>", "ok": false, "code": "<SKILL_ERROR_CODE|INTERNAL|UNKNOWN_OP|BAD_PROTOCOL>", "message": "<str>"}`

### Op set (mirrors the Python API 1:1)

| Op | Input | Result |
|---|---|---|
| `skill/init` … `skill/log-feedback` | skill input object | skill result object |
| `hook/session-start` | `{}` | `RecapResult` or `null` (absent/skip) |
| `hook/before-send` | `{"message": "<str>"}` | `BeforeSendResult` |
| `sync/agents-md` | `{}` | `{"path": "<abs>"}` |

Pydantic models serialize with `mode="json"`. `RecapResult`/`Suggestion`/
`datetime` all reduce to plain JSON — the client does no transformation
beyond parsing. SkillError codes (`NOT_FOUND`, `ILLEGAL_TRANSITION`,
`NOTES_REQUIRED`, …) pass through verbatim so hosts can branch on them.

## Python server (`mission_ctrl_pi/bridge_server.py`)

- `main()`: argparse (`--cwd`), reads stdin lines, per-line try/except —
  one bad request never kills the server; unknown op → `UNKNOWN_OP`.
- Dispatch table maps op → (input model, function). Hook ops reuse
  `on_session_start` / `on_before_send` directly (typed contracts already
  exist); `cwd` resolves the store root per request.
- Any unexpected exception → `INTERNAL` with a one-line message (no
  traceback over the wire).
- Unit-tested by driving `main()` with `io.StringIO` stdio (no subprocess
  in unit tests); one subprocess smoke test asserts real spawn works.

## TS client (`packages/bridge/src/`)

- `spawnServer(python?, cwd)` — resolves interpreter (`python3` → `python`
  fallback, overridable for tests), `client.request(op, input)` with
  incrementing ids, per-request timeout (default 30s → `TIMEOUT` error).
- Zero runtime dependencies; tested with Node's built-in `node:test` runner
  (no vitest/jest toolchain).
- `packages/bridge/package.json` ships types alongside JS (`tsc` build,
  `allowJs` off, `strict` on).

## Pi adapter (`packages/pi-extension/`)

- `package.json` with `pi.extensions: ["./src/index.ts"]`; `index.ts`
  subscribes to `session_start` (injects `sessionStart` recap text or skips
  on `null`) and `input` (runs `beforeSend`; on `redirect` prepends the
  hook message; on `bypass` surfaces it), and registers custom tools
  `intent-*` delegating to `runSkill`.
- Verified by `pi install ./packages/pi-extension` in a scratch project
  (manual, documented in the change handoff) — automated tests stop at the
  bridge boundary.

## Constraints

- Python stays the system of record: any behavior needed by a host MUST be
  added to core/skills first, then exposed as an op — never implemented in TS.
- Server is stdlib-only; client is dependency-free.
- Message size cap 1MB per line (larger payloads → `BAD_REQUEST`, protects
  the pipe); request timeout enforced client-side.
