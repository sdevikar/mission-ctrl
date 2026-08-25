# AGENTS.md — Mission Ctrl

> This file is the first thing you read. It tells you what this project is, how
> to work on it, and how to hand off to the next session. Read it fully before
> touching any code or docs.

---

## What This Project Is

**Mission Ctrl** is a developer productivity tool that acts as a structured
"intent layer" between a developer and an AI coding agent (Pi, Claude Code, etc.). It prevents
the agent from going off-mission by keeping a local, git-tracked record of:
- The project's mission, MVP scope, and constraints
- A backlog of ideas and a spec graph with dependency tracking
- A session event log (meta.jsonl) that gives the agent full context on return

The developer interacts entirely through **skills** (`intent:init`,
`intent:add-idea`, `intent:triage`, etc.). The agent never edits `.intent/`
files directly — it calls skills, and skills call the core Python library.

**The architecture in one sentence:**  
Agent reasons → calls a skill → skill calls `mission_ctrl_core` → core validates
and persists to `.intent/` → AGENTS.md is auto-regenerated.

**Key docs to read next (in order):**
1. [`docs/architecture.md`](docs/architecture.md) — system diagram and component layout
2. [`docs/design.md`](docs/design.md) — data model and skill responsibility matrix
3. [`docs/kanban.md`](docs/kanban.md) — current milestone status and OpenSpec change index
4. [`docs/handoff.md`](docs/handoff.md) — what the last session did, key decisions, what's next

---

## Two Packages, One Language

| Package | PyPI name | Purpose |
|---|---|---|
| `packages/core` | `mission_ctrl_core` | Pure Python lib. No network, no LLM, no subprocess. Pydantic models, stores, event builder, planner, recap. |
| `packages/pi-package` | `mission_ctrl_pi` | Pi agent extension. Hooks + skills. Imports core directly (no bridge). |

Everything is Python. No Node.js, no TypeScript, no bridge — by design.

---

## Way of Working

### Before You Write Anything

1. **Read `AGENTS.md`** (this file) — you're doing that now. ✓
2. **Read `docs/handoff.md`** — find out where the last session ended and what
   decisions were made. Don't repeat solved problems.
3. **Check `docs/kanban.md`** — find the current milestone and its OpenSpec
   change. The change's `proposal.md`, `design.md`, and `tasks.md` are your
   source of truth for what to build.
4. **Ask one clarifying question** if anything is ambiguous before starting.
   Don't assume. Don't gold-plate. Don't start a tangent.

### While You Work

- **One task at a time.** Pick the first unchecked item in the current change's
  `tasks.md`. Do it. Verify it. Move on.
- **Atomic commits.** Each commit is one logical thing. Commit message format:
  `<change-id>: <what you did>` (e.g. `core-foundation-01: add MissionStore read/write + tests`).
  No mega-commits that mix unrelated changes.
- **No scope creep.** If you notice something that should be improved but it's
  not in the current task, write it in `docs/handoff.md` under "Noticed / Deferred"
  and keep moving. Don't fix it now.
- **Tests before done.** A task is not done until there's a test for it (or an
  explicit reason documented why there can't be one).
- **Plain English.** Comments, docs, commit messages — write them as if
  explaining to a smart person who hasn't read the codebase. No jargon for
  jargon's sake.
- **Keep it simple.** If you're choosing between two implementations, choose
  the simpler one. Complexity is a cost, not a feature.

### Never Do These Things

- ❌ Don't hand-edit `.intent/` files — always go through stores or skills.
- ❌ Don't add network calls, subprocess calls, or LLM calls to `mission_ctrl_core`.
- ❌ Don't implement features from outside the current OpenSpec change unless
  explicitly asked.
- ❌ Don't refactor "while you're in there" unless the current task requires it.
- ❌ Don't introduce Node.js, TypeScript, or non-Python dependencies anywhere
  in the v1 path.

### When You Finish a Session

**Always append to `docs/handoff.md` before you stop.** See the handoff format
below. This is not optional — the next session starts cold and will use this
to get up to speed in 60 seconds.

---

## Working with the Developer (ADHD-Friendly Defaults)

The developer works best with:
- **Short feedback loops.** Show progress early and often. Don't disappear for
  20 minutes and return with a wall of code. Check in after each meaningful step.
- **One thing at a time.** Don't ask three questions in one message. Don't
  present five options at once. One question, one decision, then proceed.
- **Explicit "done" signals.** When a task is complete, say so clearly:
  *"Done. X is implemented and tested. Next up: Y. Want me to proceed?"*
- **Recaps before transitions.** When switching topics or starting a new task,
  give a one-sentence recap of where things stand before jumping in.
- **No walls of text.** Use bullet points and short paragraphs. If something
  needs a long explanation, summarize first, expand only if asked.
- **Surfaced decisions.** When you make a non-obvious choice (e.g. using
  `graphlib` instead of a custom cycle-detection algorithm), say so in one
  sentence. Don't let decisions go invisible.
- **Scope guardrail.** If you notice the conversation drifting off-task, say:
  *"That's interesting — should I note it in handoff and stay on the current
  task, or do you want to switch?"*

---

## Handoff Document Format

**File:** `docs/handoff.md`  
**Rule:** Append a new entry at the top (newest first) after every session.
Never delete old entries.

```markdown
## [YYYY-MM-DD HH:MM] Session Summary

**OpenSpec change in progress:** <change-id>
**Tasks completed this session:**
- <task description> ✓

**Key decisions made:**
- <decision>: <brief reasoning>

**Assumptions:**
- <assumption>

**Noticed / Deferred (not in scope but worth tracking):**
- <observation>

**Next session should start with:**
- <first task to pick up>
```

---

## OpenSpec Change Workflow (Quick Reference)

```
find current change in docs/kanban.md
  → read openspec/changes/<change-id>/proposal.md   (what and why)
  → read openspec/changes/<change-id>/design.md      (contracts and decisions)
  → work through openspec/changes/<change-id>/tasks.md (one checkbox at a time)
  → when done-when criterion is met: archive the change
  → append session summary to docs/handoff.md
```

---

## Current Status

See [`docs/kanban.md`](docs/kanban.md) — OpenSpec Change Index at the top.  
See [`docs/handoff.md`](docs/handoff.md) — most recent session summary.
