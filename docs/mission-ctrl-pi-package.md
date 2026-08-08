# Mission Ctrl — Pi Package Specification
## Python Extension for Pi Coding Agent
### v1.0 | 2026-08-04

> This document covers only the **Pi package** surface (`@mission-ctrl/pi-package`), implemented as a Python-based extension for the Pi coding agent.
> For shared data model, schemas, and core library, see [`mission-ctrl-common.md`](./mission-ctrl-common.md).
> For the Claude Code plugin, see [`mission-ctrl-claude-plugin.md`](./mission-ctrl-claude-plugin.md).

---

## Table of Contents

1. [Extension Overview](#1-extension-overview)
2. [Repository Layout](#2-repository-layout)
3. [Pi-Specific Architecture](#3-pi-specific-architecture)
4. [Extension Manifest](#4-extension-manifest)
5. [Hooks](#5-hooks)
6. [Skills (Pi)](#6-skills-pi)
7. [AGENTS.md Auto-Generation](#7-agentsmd-auto-generation)
8. [Installation & Distribution](#8-installation--distribution)
9. [Testing Strategy](#9-testing-strategy)
10. [Phase-by-Phase Rollout](#10-phase-by-phase-rollout)

---

## 1. Extension Overview

The Pi package is a **Python-based thin wrapper** around the core TypeScript library (`@mission-ctrl/core`), called via a Node.js subprocess bridge. It:

- Registers Pi extension lifecycle hooks that fire automatically on session start
- Exposes all 7 `intent:*` skills as Pi skill definitions
- Intercepts implementation-first requests to enforce backlog-first workflow
- Syncs `AGENTS.md` after every `.intent/` write so mission/MVP/constraints are always in context
- Has **zero** business logic of its own — all logic delegates to `@mission-ctrl/core`

### Core Bridge Strategy

Since `@mission-ctrl/core` is TypeScript, the Python Pi package calls it via a lightweight CLI bridge:

```
Pi Extension (Python)
      |
      | subprocess call
      v
mission-ctrl-cli (Node.js thin CLI wrapping @mission-ctrl/core)
      |
      v
.intent/ files
```

The CLI bridge accepts JSON-encoded arguments over stdin and returns JSON results over stdout. This keeps the TypeScript core as the single source of truth while allowing Python to drive the extension lifecycle.

---

## 2. Repository Layout

```
packages/pi-package/
├── src/
│   ├── extension.py         # Extension manifest — entry point
│   ├── bridge.py            # Node.js subprocess bridge to @mission-ctrl/core
│   ├── hooks/
│   │   ├── on_session_start.py
│   │   └── on_before_send.py
│   ├── skills/
│   │   ├── recap.py
│   │   ├── add_idea.py
│   │   ├── triage.py
│   │   ├── next.py
│   │   ├── design_propose.py
│   │   ├── design_approve.py
│   │   └── status.py
│   ├── sync/
│   │   └── agents_md_sync.py  # AGENTS.md regeneration
│   └── types.py               # Pi extension type bindings
├── templates/
│   └── AGENTS.md              # Template for AGENTS.md generation
├── tests/
│   ├── test_skills/
│   ├── test_hooks/
│   └── fixtures/              # Shared with core (symlinked or copied)
├── pyproject.toml
└── README.md
```

---

## 3. Pi-Specific Architecture

### 3.1 Reuse Strategy

The Pi package reuses `@mission-ctrl/core` entirely via the CLI bridge. The wrapper is thin:

| Claude Component | Pi Equivalent |
|---|---|
| Plugin manifest (`index.ts`) | Extension manifest (`extension.py`) |
| `session:start` hook | `onSessionStart` lifecycle hook |
| `file:write` hook | Post-skill callback for `AGENTS.md` sync |
| Slash command skills | Pi skill definitions |
| `CLAUDE.md` sync | `AGENTS.md` generation |

### 3.2 Pi-Specific Additions

These features are unique to the Pi package and have no Claude equivalent:

1. **AGENTS.md auto-generation** — Pi loads `AGENTS.md` natively from project dir; this is the primary context injection mechanism.
2. **Message interception (`onBeforeSend`)** — Pi extensions can filter/modify agent messages before sending. Used to enforce backlog-first: intercepts `"implement X"` → redirects to `"add idea X to backlog first?"`.
3. **Tree navigation** — Pi's tree-structured history can correlate with `meta.jsonl` for decision archaeology (v2 feature).
4. **Context engineering** — Pi's minimal system prompt makes intent injection more effective; `AGENTS.md` is kept lean and focused.

### 3.3 CLI Bridge Protocol

**`bridge.py`** wraps calls to the `mission-ctrl` CLI:

```python
import subprocess
import json

class CoreBridge:
    def __init__(self, intent_dir: str):
        self.intent_dir = intent_dir

    def call(self, command: str, args: dict) -> dict:
        payload = json.dumps({"command": command, "intentDir": self.intent_dir, **args})
        result = subprocess.run(
            ["npx", "@mission-ctrl/core-cli"],
            input=payload,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        return json.loads(result.stdout)
```

Available bridge commands mirror the core library operations:
- `generate_recap`
- `suggest_next`
- `check_alignment`
- `generate_design_digest`
- `backlog_add`
- `backlog_update`
- `spec_update`
- `event_append`
- `validate_all`
- `intent_store_init`

---

## 4. Extension Manifest

**File:** `packages/pi-package/src/extension.py`

```python
from mission_ctrl.hooks.on_session_start import on_session_start
from mission_ctrl.hooks.on_before_send import on_before_send
from mission_ctrl.skills import (
    recap, add_idea, triage, next_spec,
    design_propose, design_approve, status,
)

extension = {
    "name": "mission-ctrl",
    "version": "1.0.0",
    "description": "Intent-driven development assistant for Pi",
    "hooks": {
        "onSessionStart": on_session_start,
        "onBeforeSend": on_before_send,
    },
    "skills": [
        recap, add_idea, triage, next_spec,
        design_propose, design_approve, status,
    ],
}
```

---

## 5. Hooks

### 5.1 Session Start Hook

**File:** `packages/pi-package/src/hooks/on_session_start.py`

**Fires:** Every time Pi opens a workspace

**Behavior:**
1. Check if `.intent/` exists in workspace root. If not, inject message suggesting `intent:init`.
2. Detect last session time by reading the most recent `meta.jsonl` event timestamp.
3. Compute gap in hours.
4. Determine verbosity:
   - < 1 hour → `"ultra-brief"`
   - 1–24 hours → `"brief"`
   - > 24 hours or first session → `"full"`
5. Call `bridge.call("generate_recap", ...)` to get recap content.
6. Inject formatted recap as a system message before the user's first turn.
7. Append `SESSION_STARTED` event to `meta.jsonl` via bridge.

**Adaptive Recap Rules:**

| Gap | Verbosity | Content |
|---|---|---|
| < 1 hour | Ultra-brief | `"Welcome back. spec_001 still in progress."` |
| 1–24 hours | Brief | Mission one-liner + last focus + next step |
| > 24 hours | Full | Mission + MVP progress + last focus + changes since + recommended next + constraints reminder |
| First ever | Full + bootstrap | Full recap + "This project uses Mission Ctrl. Here's how it works..." |

### 5.2 Before Send Hook (Backlog Enforcement)

**File:** `packages/pi-package/src/hooks/on_before_send.py`

**Fires:** Before every message is sent to the model (Pi-specific capability)

**Behavior:**
1. Scan outgoing message for implementation-intent patterns:
   - `"implement X"`, `"write X"`, `"build X"`, `"create X"`, `"add X feature"`, etc.
2. If pattern detected AND the feature is not already in backlog:
   - Intercept the message
   - Prepend: `"Before implementing, let's capture this idea: /intent:add-idea "{feature_name}""`
3. If pattern detected AND feature is in backlog but not triaged:
   - Prepend: `"This idea is untriaged. Consider /intent:triage {idea_id} first."`
4. If spec exists and design is not approved:
   - Prepend: `"spec_{id} needs design approval before implementation. Run /intent:design-propose spec_{id}."`

> **Note:** This hook has no Claude equivalent. It is unique to Pi's message interception capability.

### 5.3 Post-Skill Hook (AGENTS.md Sync)

**Fires:** After any skill that writes to `.intent/`

**Behavior:**
1. Read current `.intent/` state via bridge.
2. Regenerate `./AGENTS.md` from template.
3. Write to disk.
4. Do NOT commit — let the user handle git.

---

## 6. Skills (Pi)

All skills are registered as Pi skill definitions. They share identical logic with the Claude plugin (via the core bridge) but use Pi's skill API format instead of Claude Code's slash command format.

### `intent:recap`

- **Trigger:** Manual or `onSessionStart` hook
- **Input:** `verbosity?: "brief" | "full"`
- **Output:** Formatted status message
- **Side Effects:** None
- **Implementation:** `bridge.call("generate_recap", {"verbosity": verbosity})`

---

### `intent:add-idea`

- **Trigger:** Manual
- **Input:** `title: str, description: str`
- **Output:** Confirmation + assigned idea ID
- **Side Effects:** Writes to `backlog.json`, appends `BACKLOG_ADDED` meta event
- **Implementation:**
  ```python
  result = bridge.call("backlog_add", {"title": title, "description": description})
  # Returns: {"idea_id": "idea_003", "message": "..."}
  ```

---

### `intent:triage`

- **Trigger:** Manual
- **Input:** `idea_id: str, bucket: Literal["mvp_critical", "parked", "archived"], override_alignment: bool = False`
- **Output:** Classification result with alignment summary
- **Side Effects:** Updates `backlog.json`, appends `BACKLOG_TRIAGE` meta event
- **Implementation:**
  ```python
  result = bridge.call("backlog_update", {
      "idea_id": idea_id,
      "bucket": bucket,
      "override_alignment": override_alignment,
  })
  ```

---

### `intent:next`

- **Trigger:** Manual
- **Input:** `count: int = 3`
- **Output:** Ranked list of suggested next specs
- **Side Effects:** None (read-only)
- **Implementation:** `bridge.call("suggest_next", {"count": count})`

---

### `intent:design-propose`

- **Trigger:** Manual (or auto-triggered by `onBeforeSend` enforcement)
- **Input:** `spec_id: str`
- **Output:** Design digest with key choices, risks, open questions, impacted modules
- **Side Effects:** Updates spec status to `"design_proposed"`, appends `DESIGN_PROPOSED` meta event
- **Implementation:** `bridge.call("generate_design_digest", {"spec_id": spec_id})`

---

### `intent:design-approve`

- **Trigger:** Manual
- **Input:** `spec_id: str, decision: Literal["approved", "rejected", "revised"], notes: Optional[str] = None`
- **Output:** Approval confirmation with next step guidance
- **Side Effects:** Updates spec status, appends `DESIGN_APPROVED` meta event
- **Implementation:** `bridge.call("spec_update", {"spec_id": spec_id, "decision": decision, "notes": notes})`

---

### `intent:status`

- **Trigger:** Manual
- **Input:** None
- **Output:** Full project dashboard
- **Side Effects:** None (read-only)
- **Implementation:** `bridge.call("generate_status", {})`

---

## 7. AGENTS.md Auto-Generation

### 7.1 Purpose

`AGENTS.md` is Pi's native context-injection file. It is loaded automatically by Pi from the project directory. Mission Ctrl regenerates it after every `.intent/` write so that Pi always operates with current mission, MVP, and constraints in context.

### 7.2 Template Structure

**File:** `packages/pi-package/templates/AGENTS.md`

```markdown
<!-- Auto-generated by Mission Ctrl. Do not edit manually. -->
<!-- Last updated: {timestamp} -->

# Project Intent

## Mission
{mission.statement}

## MVP ({mvp.version}) — {done}/{total} Complete
- [x] {mvp item 1}
- [ ] {mvp item 2}
- [ ] {mvp item 3}

## Constraints
- [{severity}] {constraint rule}
- [{severity}] {constraint rule}

## Current Focus
{spec_id} — {spec title} ({status})

## Next Up
- {spec_id} — {spec title} (blocked by {deps} or unblocked)

## Backlog Summary
- MVP-critical: {count}
- Parked: {count}
- Untriaged: {count}

---

## Agent Instructions

When working on this project:
1. All new ideas must be captured to backlog first (intent:add-idea).
2. Before implementing any spec, ensure design is approved (intent:design-propose -> intent:design-approve).
3. Prefer completing MVP items over parked ideas unless explicitly overridden.
4. Respect constraints. If a constraint must be broken, explain why and use intent:next.
```

### 7.3 Sync Strategy

- **Trigger:** After every skill write to `.intent/`
- **Performance:** File is < 2KB. Regeneration is < 10ms.
- **Git impact:** `AGENTS.md` changes appear in git diff alongside intent changes. This is intentional.

> **Difference from Claude:** `CLAUDE.md` uses Claude-specific slash command syntax (`/intent:*`). `AGENTS.md` uses plain text references (`intent:*`) compatible with Pi's skill naming conventions.

---

## 8. Installation & Distribution

### 8.1 Pi Extension Installation

Via npm (Pi loads Node packages via `pi install`):
```
pi install npm:@mission-ctrl/pi-package
```

Local development:
```
pi install ./packages/pi-package
```

### 8.2 Package Structure

The Pi package is distributed as an npm package (`@mission-ctrl/pi-package`) that bundles:
- Python source files under `src/`
- The `AGENTS.md` template under `templates/`
- A `pyproject.toml` for Python dependency management
- A bundled `@mission-ctrl/core-cli` for the bridge subprocess

### 8.3 Python Dependencies

```toml
[project]
name = "mission-ctrl-pi"
requires-python = ">=3.11"
dependencies = []  # No external Python deps; core logic in Node bridge

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio"]
```

---

## 9. Testing Strategy

### 9.1 Pi Extension Tests

| Test Category | Approach |
|---|---|
| Skill parameter parsing | Unit tests with mock bridge |
| Hook behavior | Integration tests with temp directories |
| AGENTS.md sync | Snapshot tests |
| Bridge calls | Mock subprocess tests |
| Message interception | Unit tests for `onBeforeSend` pattern matching |
| End-to-end workflow | Script that runs full lifecycle on temp repo |

### 9.2 Bridge Tests

The bridge layer requires both Python and Node.js in the test environment:

```bash
# Run Pi extension tests
cd packages/pi-package
python -m pytest tests/

# Run bridge integration tests (requires Node.js)
python -m pytest tests/test_bridge/ --integration
```

### 9.3 End-to-End Acceptance

Full lifecycle test:
```
init -> add idea -> triage -> design propose -> design approve -> next -> status
```

All state changes reflected in `.intent/` files; all decisions recorded in `meta.jsonl`; `AGENTS.md` updated after each write.

---

## 10. Phase-by-Phase Rollout

### Phase 6: Pi Package (Weeks 7–8)

**Goal:** Same functionality available in Pi.

**Deliverables:**
- `packages/pi-package/` scaffolded with Python project structure
- `bridge.py` implementing CLI subprocess bridge to `@mission-ctrl/core`
- Pi extension manifest (`extension.py`) with all hooks and skills registered
- All 7 skills implemented via bridge calls
- `onBeforeSend` hook for backlog-first enforcement (Pi-specific)
- `AGENTS.md` template and sync logic
- `pi install npm:@mission-ctrl/pi-package` works
- Documentation for Pi-specific features

**Files to create:**
```
packages/pi-package/src/extension.py
packages/pi-package/src/bridge.py
packages/pi-package/src/hooks/on_session_start.py
packages/pi-package/src/hooks/on_before_send.py
packages/pi-package/src/skills/*.py
packages/pi-package/src/sync/agents_md_sync.py
packages/pi-package/templates/AGENTS.md
packages/pi-package/pyproject.toml
packages/pi-package/tests/
```

**Acceptance criteria:**
- Pi auto-loads `AGENTS.md` from project directory
- All 7 skills work in Pi interactive mode
- Session start hook fires recap automatically
- `onBeforeSend` correctly intercepts implementation-first messages
- `AGENTS.md` updates within 1 second of any `.intent/` write

---

### Phase 7: Advanced Features (Weeks 9–12)

**Goal:** v2 features that deepen the system (shared with Claude plugin).

**Pi-specific deliverables:**
- Tree navigation integration: correlate Pi's conversation tree with `meta.jsonl` events
- Enhanced `onBeforeSend`: smarter NLU for detecting implementation intent
- Drift detection: suggest intent update after repeated overrides
- Analytics: velocity tracking, constraint violation frequency

---

*End of Pi Package Specification*
