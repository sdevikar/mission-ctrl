# Mission Ctrl — Claude Code Plugin Specification
## TypeScript Plugin for Claude Code
### v1.0 | 2026-08-04

> This document covers only the **Claude Code plugin** surface (`@mission-ctrl/claude-plugin`).
> For shared data model, schemas, and core library, see [`mission-ctrl-common.md`](./mission-ctrl-common.md).
> For the Pi package, see [`mission-ctrl-pi-package.md`](./mission-ctrl-pi-package.md).

---

## Table of Contents

1. [Plugin Overview](#1-plugin-overview)
2. [Repository Layout](#2-repository-layout)
3. [Plugin Manifest](#3-plugin-manifest)
4. [Hooks](#4-hooks)
5. [Skills (Claude Code)](#5-skills-claude-code)
6. [CLAUDE.md Auto-Generation](#6-claudemd-auto-generation)
7. [Installation & Distribution](#7-installation--distribution)
8. [Testing Strategy](#8-testing-strategy)
9. [Phase-by-Phase Rollout](#9-phase-by-phase-rollout)

---

## 1. Plugin Overview

The Claude Code plugin is a **thin wrapper** around `@mission-ctrl/core`. It:

- Registers hooks that fire automatically when Claude Code opens a workspace
- Exposes all 7 `intent:*` skills as Claude Code slash commands
- Syncs `CLAUDE.md` after every `.intent/` write so mission/MVP/constraints are always in context
- Has **zero** business logic of its own — all logic lives in `@mission-ctrl/core`

### High-Level Flow

```
Developer opens project in Claude Code
        |
        v
  session:start hook (guaranteed by Claude plugin)
        |
        v
  Recap displayed before user types
        |
        v
  Developer works via slash commands:
    /intent:add-idea "progress bar"
    /intent:triage idea_001
    /intent:design-propose spec_001
    /intent:design-approve spec_001
    /intent:next
    /intent:status
        |
        v
  Skills read/write .intent/ via @mission-ctrl/core
        |
        v
  State changes trigger CLAUDE.md auto-regeneration
```

---

## 2. Repository Layout

```
packages/claude-plugin/
├── src/
│   ├── index.ts             # Plugin manifest — entry point
│   ├── hooks/
│   │   └── sessionStart.ts  # session:start hook
│   ├── skills/
│   │   ├── recap.ts
│   │   ├── addIdea.ts
│   │   ├── triage.ts
│   │   ├── next.ts
│   │   ├── designPropose.ts
│   │   ├── designApprove.ts
│   │   └── status.ts
│   ├── sync/
│   │   └── claudeMdSync.ts  # CLAUDE.md regeneration
│   └── types.ts             # Claude plugin type bindings
├── tests/
│   ├── skills/
│   ├── hooks/
│   └── __snapshots__/       # CLAUDE.md snapshot tests
├── package.json
└── tsconfig.json
```

---

## 3. Plugin Manifest

**File:** `packages/claude-plugin/src/index.ts`

```typescript
export default {
  name: "mission-ctrl",
  version: "1.0.0",
  description: "Intent-driven development assistant for Claude Code",
  hooks: {
    "session:start": sessionStartHook,
    "file:write": claudeMdSyncHook,
  },
  skills: [recap, addIdea, triage, next, designPropose, designApprove, status],
  mcpServers: [], // optional standalone MCP server reference
};
```

---

## 4. Hooks

### 4.1 Session Start Hook

**File:** `packages/claude-plugin/src/hooks/sessionStart.ts`

**Fires:** Every time Claude Code opens a workspace containing `.intent/`

**Behavior:**
1. Check if `.intent/` exists in workspace root. If not, inject message suggesting `/intent:init`.
2. Detect last session time by reading the most recent `meta.jsonl` event timestamp.
3. Compute gap in hours.
4. Determine verbosity:
   - < 1 hour → `"ultra-brief"`
   - 1–24 hours → `"brief"`
   - > 24 hours or first session → `"full"`
5. Call `generateRecap()` from `@mission-ctrl/core` with detected parameters.
6. Inject formatted recap message into chat before user types.
7. Append `SESSION_STARTED` event to `meta.jsonl`.

**Adaptive Recap Rules:**

| Gap | Verbosity | Content |
|---|---|---|
| < 1 hour | Ultra-brief | `"Welcome back. spec_001 still in progress."` |
| 1–24 hours | Brief | Mission one-liner + last focus + next step |
| > 24 hours | Full | Mission + MVP progress + last focus + changes since + recommended next + constraints reminder |
| First ever | Full + bootstrap | Full recap + "This project uses Mission Ctrl. Here's how it works..." |

### 4.2 File Write Hook (CLAUDE.md Sync)

**Fires:** After any skill writes to `.intent/`

**Behavior:**
1. Read current `.intent/` state.
2. Regenerate `./CLAUDE.md` from template.
3. Write to disk.
4. Do NOT commit — let the user handle git.

---

## 5. Skills (Claude Code)

All skills are registered as Claude Code slash commands under the `/intent:*` namespace.

### `/intent:recap`

- **Trigger:** Manual or hook
- **Input:** `verbosity?: "brief" | "full"`
- **Output:** Formatted status message
- **Side Effects:** None
- **Implementation:** Calls `generateRecap()` from core

---

### `/intent:add-idea`

- **Trigger:** Manual
- **Input:** `title: string, description: string`
- **Output:** Confirmation + assigned idea ID
- **Side Effects:** Writes to `backlog.json`, appends `BACKLOG_ADDED` meta event
- **Implementation:**
  1. Generate next idea ID
  2. Create `BacklogItem` with `bucket="untriaged"`
  3. Call `store.backlog.add()`
  4. Call `EventBuilder.backlogAdded()`
  5. Return confirmation message

---

### `/intent:triage`

- **Trigger:** Manual
- **Input:** `ideaId: string, bucket: "mvp_critical"|"parked"|"archived", overrideAlignment?: boolean`
- **Output:** Classification result with alignment summary
- **Side Effects:** Updates `backlog.json`, appends `BACKLOG_TRIAGE` meta event
- **Implementation:**
  1. Look up idea by ID
  2. If not `overrideAlignment`: call `checkAlignment()` using idea title/description
  3. Update `idea.bucket` and `idea.alignment`
  4. Call `store.backlog.update()` + `EventBuilder.backlogTriage()`
  5. If bucket is `mvp_critical` but `alignment.mvp` is not `required`: append warning
  6. Return result message

---

### `/intent:next`

- **Trigger:** Manual
- **Input:** `count?: number` (default 3)
- **Output:** Ranked list of suggested next specs
- **Side Effects:** None (read-only)
- **Implementation:**
  1. Call `suggestNext()` from core with `respectDependencies=true`
  2. Take top N results
  3. Format as numbered list with title, ID, MVP alignment, blocked status, rationale
  4. Return formatted message

---

### `/intent:design-propose`

- **Trigger:** Manual (or auto-triggered before code generation)
- **Input:** `specId: string`
- **Output:** Design digest with key choices, risks, open questions, impacted modules
- **Side Effects:** Updates spec status to `"design_proposed"`, appends `DESIGN_PROPOSED` meta event
- **Implementation:**
  1. Look up spec by ID
  2. Validate spec is in `"draft"` or `"design_proposed"` status
  3. Call `generateDesignDigest()` from core
  4. Update `spec.status` to `"design_proposed"`
  5. Call `store.specs.update()` + `EventBuilder.designProposed()`
  6. Return formatted digest

---

### `/intent:design-approve`

- **Trigger:** Manual
- **Input:** `specId: string, decision: "approved"|"rejected"|"revised", notes?: string`
- **Output:** Approval confirmation with next step guidance
- **Side Effects:** Updates spec status, appends `DESIGN_APPROVED` meta event
- **Implementation:**
  1. Look up spec by ID
  2. Validate spec is in `"design_proposed"` status
  3. If `approved`: set status to `"design_approved"`
  4. If `rejected`: set status to `"draft"`
  5. If `revised`: keep status as `"design_proposed"`
  6. Call `store.specs.update()` + `EventBuilder.designApproved()`
  7. Return confirmation with appropriate next step message

---

### `/intent:status`

- **Trigger:** Manual
- **Input:** None
- **Output:** Full project dashboard
- **Side Effects:** None (read-only)
- **Implementation:**
  1. Read all domain state
  2. Count MVP completion (items where all `linked_specs` are `"done"`)
  3. List active specs (`in_progress` or `design_approved`)
  4. List unblocked specs (`design_approved` with all dependencies `done`)
  5. Count backlog buckets
  6. Return formatted dashboard

---

## 6. CLAUDE.md Auto-Generation

### 6.1 Purpose

`CLAUDE.md` serves as a cache of intent state in the agent's system prompt. Even when the agent doesn't explicitly call skills, it has mission/MVP/constraints in context. This reduces drift during free-form conversation.

### 6.2 Template Structure

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
1. All new ideas must be captured to backlog first (/intent:add-idea).
2. Before implementing any spec, ensure design is approved (/intent:design-propose -> /intent:design-approve).
3. Prefer completing MVP items over parked ideas unless explicitly overridden.
4. Respect constraints. If a constraint must be broken, use /intent:next and explain why.
```

### 6.3 Sync Strategy

- **Trigger:** After every skill write to `.intent/`
- **Performance:** File is < 2KB. Regeneration is < 10ms.
- **Git impact:** `CLAUDE.md` changes appear in git diff alongside intent changes. This is intentional.

---

## 7. Installation & Distribution

### 7.1 Claude Plugin Installation

Via marketplace:
```
/plugin install mission-ctrl@claude-plugins-official
```

Via npm (bleeding edge):
```
/plugin install npm:@mission-ctrl/claude-plugin
```

Local development:
```
/plugin install ./packages/claude-plugin
```

### 7.2 Build & Publish

GitHub Actions workflow (`release.yml`) additional steps:
- Build `@mission-ctrl/claude-plugin`
- Publish to npm
- Submit to `claude-plugins-official` marketplace

---

## 8. Testing Strategy

### 8.1 Plugin Tests

| Test Category | Approach |
|---|---|
| Skill parameter parsing | Unit tests with mock context |
| Hook behavior | Integration tests with temp directories |
| CLAUDE.md sync | Snapshot tests |
| End-to-end workflow | Script that runs full lifecycle on temp repo |

### 8.2 End-to-End Acceptance

Full lifecycle test:
```
init -> add idea -> triage -> design propose -> design approve -> next -> status
```

All state changes reflected in `.intent/` files; all decisions recorded in `meta.jsonl`.

---

## 9. Phase-by-Phase Rollout

### Phase 2: Claude Plugin Shell (Week 3)

**Goal:** Plugin installs in Claude Code and exposes skills.

**Deliverables:**
- `packages/claude-plugin/` scaffolded
- Plugin manifest with all 7 skills registered
- Stub skill implementations (read-only, no core integration yet)
- Local installation and manual testing in Claude Code
- README with installation instructions

**Files to create:**
```
packages/claude-plugin/src/index.ts
packages/claude-plugin/src/skills/*.ts (stubs)
packages/claude-plugin/package.json
packages/claude-plugin/tsconfig.json
```

**Acceptance criteria:**
- `/plugin install ./packages/claude-plugin` succeeds
- All 7 `/intent:*` commands appear in Claude Code skill palette
- Stub skills return placeholder text

---

### Phase 3: Skill Integration (Week 4)

**Goal:** All skills wired to core library, full CRUD working.

**Deliverables:**
- `recap` skill calls `generateRecap()`
- `add-idea` skill writes to `backlog.json` + meta
- `triage` skill updates `backlog.json` + meta
- `next` skill calls `suggestNext()`
- `design-propose` skill generates digest + updates spec status
- `design-approve` skill updates spec status
- `status` skill aggregates full project state
- Error handling: validation failures, missing files, invalid IDs
- Integration tests for full workflows

**Files modified:**
```
packages/claude-plugin/src/skills/*.ts
```

**Acceptance criteria:**
- Full lifecycle works end-to-end
- All state changes reflected in `.intent/` files
- All decisions recorded in `meta.jsonl`
- Invalid inputs return clear errors, not silent failures

---

### Phase 4: Hooks & Auto-Onboarding (Week 5)

**Goal:** Session start hook fires automatically. CLAUDE.md sync works.

**Deliverables:**
- `sessionStartHook` implementation
- Last session detection (`meta.jsonl` timestamp parsing)
- Adaptive recap formatting
- `file:write` hook for CLAUDE.md regeneration
- CLAUDE.md template and sync logic
- Hook integration tests

**Files to create:**
```
packages/claude-plugin/src/hooks/sessionStart.ts
packages/claude-plugin/src/sync/claudeMdSync.ts
packages/claude-plugin/src/hooks/__tests__/sessionStart.test.ts
```

**Acceptance criteria:**
- Opening a project with `.intent/` auto-injects recap message
- Recap is brief for recent sessions, full for long gaps
- After any skill write, CLAUDE.md updates within 1 second
- CLAUDE.md accurately reflects current mission, MVP, constraints, active specs

---

### Phase 5: Polish & Release (Week 6)

**Goal:** Plugin is installable from marketplace, documented, tested.

**Deliverables:**
- README with screenshots/gifs of workflow
- Marketplace submission to `claude-plugins-official`
- CI/CD pipeline (test -> build -> publish)
- Example project with pre-populated `.intent/`
- Troubleshooting guide
- Video walkthrough (optional)

**Files:**
```
README.md
CHANGELOG.md
examples/todo-app/.intent/*
```

**Acceptance criteria:**
- `/plugin install mission-ctrl@claude-plugins-official` works for beta testers
- 3+ external users can complete full workflow without assistance
- No critical bugs in 48 hours of real-world usage

---

*End of Claude Code Plugin Specification*
