# Design: Pi Extension Shell (M2)

Component contracts: `docs/design.md` §1–2 (responsibility matrix and the 10
skill rows). This change implements the `packages/pi-package` half of that
design; core behavior already specified in changes 01/02.

## Key decisions

- **Direct import, in-process**: skills call `mission_ctrl_core` via normal
  Python imports — no subprocess, no JSON-RPC, no bridge.
- **Reasoning stays in Pi**: alignment verdicts and design digests are
  Pi-produced structured inputs; skills validate and store only. Status
  transition legality is enforced in the skill layer (core enforces
  dependency rules); the skill owns the transition state machine.
- **Skill naming**: `intent:<verb>` namespace; manifest in `extension.py`.
- **Testing**: skill-level tests use a temp workspace + `pi install` of the
  local package; the M2 done-when lifecycle is itself an end-to-end script.
- **Hook stubs**: manifest registers `on_session_start` / `on_before_send`
  entry points now so M3 (change 04) doesn't touch the extension wiring.

## Constraints

- No Node.js in the dependency graph; depends only on `mission_ctrl_core`.
- Skills never hand-craft IDs, timestamps, or events.
