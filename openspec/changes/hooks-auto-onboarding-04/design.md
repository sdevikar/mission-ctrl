# Design: Hooks & Auto-Onboarding (M3)

Component contracts: `docs/architecture.md` §2. This file covers the three
hook behaviors and AGENTS.md sync.

## Session Gap Verbosity Tiers

`on_session_start` calculates the gap between `now` and the timestamp of the
last `SESSION_STARTED` event in meta.jsonl (or `INTENT_CREATED` if no prior
session). The gap drives verbosity tier selection:

| Gap | Tier | Recap content |
|---|---|---|
| < 1 hour | `skip` | No recap injected (same session, context intact) |
| 1h – 8h | `brief` | Last focused spec + next suggestion only |
| 8h – 48h | `standard` | Mission, MVP %, last focus, changes since, next suggestion |
| > 48h | `full` | All standard fields + full git log summary since last session |

The tier thresholds are constants in `on_session_start.py`; they are the single
source of truth for both the implementation and the tests.

If no `SESSION_STARTED` or `INTENT_CREATED` event exists → treat as `full`.

## on_before_send — Pattern Matching & Redirect Logic

Pattern matching runs on the raw user message before it reaches Pi's reasoning.

**Detection:** A message matches if it contains any phrase from the hardcoded
implementation-intent list (e.g. "implement", "add feature", "build", "code up",
"write the", "create the"). Case-insensitive, full-word match only (not substrings).

**Redirect target** depends on current `.intent/` state:
- No spec in `design_approved` → redirect to `intent:add-idea` or `intent:triage`
- Spec in `design_approved` → redirect to `intent:spec-status(in_progress)` prompt
- No `.intent/` present → no redirect (hook no-ops)

**Override:** Any message containing the bypass phrase (configurable constant,
default: `"override intent"`) skips pattern matching entirely. The bypass is
surfaced in Pi's response; it is never silent.

**Logging:** Every interception and every bypass is written to meta.jsonl:
- `INTENT_INTERCEPTED`: pattern matched, redirect target, matched phrase
- `INTENT_BYPASS_USED`: bypass phrase detected, original user message

## AGENTS.md Template & Sanitization

AGENTS.md is regenerated from a versioned Jinja2 template
(`packages/pi-package/templates/agents_md.jinja2`) after any `.intent/` write.

**Sanitization requirement:** All user-supplied text fields (spec titles,
descriptions, backlog item text, alignment verdicts, design digests) MUST be
escaped before rendering into the template. Specifically:
- Strip or escape any Markdown that could be interpreted as headings, code
  fences, or link definitions.
- Reject (raise `SanitizationError`) any field value containing `<!--`,
  `-->`, or backtick-fenced blocks that begin with a language identifier —
  these are the primary prompt-injection vectors in Markdown contexts.

The template regeneration must complete in ≤1s from the time the skill write
returns.

## Constraints

- Hooks fire skills; hooks contain no business logic of their own.
- `on_session_start` no-ops gracefully if `.intent/` is absent (project not
  yet initialized).
- Pattern list and tier thresholds are constants, not config files — they are
  changed by editing source and shipping a new version.
