> **Status note (added):** This document is the original vision/rationale doc. Sections 0–4
> (problem statement, feature list, non-goals, data-model rationale) are still accurate and
> authoritative. Sections 5–9 describe an early "VS Code first, agent-agnostic" implementation
> plan that has since been superseded by concrete decisions: **Pi extension first, pure Python
> core, no MCP in v1.** For current technical architecture, component design, and roadmap, see
> `docs/architecture.md`, `docs/design.md`, and `docs/roadmap.md`. One correction worth flagging:
> §9.1 below correctly lists `spec.create_from_idea` and `spec.update_status` as required v1
> skills — a later draft mistakenly deferred them to v2; `docs/design.md` restores them.

# Intent-Driven, Spec-Aware Development Assistant (VS Code First)
Version: 0.2 (Implementation Draft)
Owner: (you)
Last updated: 2026-03-20

---

## 0) Purpose of This Document
This document consolidates all decisions and details into a single implementation-oriented spec. It is intended to be the working reference for building:
- VS Code integration
- MCP servers / skills
- Data model and persistence
- Agent interaction patterns

---

## 1) Abstract (Intent of the Tool)

### 1.1 Problem Statement
AI-assisted coding increases output velocity but also increases:
- **scope creep** (adding low-value features because they're easy to generate)
- **loss of mission alignment** (work drifts away from the original end-to-end goal)
- **planning overhead** (humans manually decide “what’s next” repeatedly)
- **review friction** (hard to review design changes at the right time)
- **re-entry cost** (after a break, it’s hard to regain context and resume optimally)

Existing “spec-driven development” (SDD) tooling improves local alignment between spec ↔ code, but does not provide a first-class system for:
- mission/MVP alignment over time
- backlog-first arbitration
- dependency-aware prioritization
- lightweight onboarding and drift control inside the IDE

### 1.2 Solution Overview
Build an **Intent Layer** that integrates into users’ existing agent workflow via **skills** rather than replacing their IDE or coding agent.

Core behavior:
- Treat **Mission → MVP → Constraints** as authoritative project intent.
- Force **Backlog-first** for all new ideas/features.
- Operate as a **Minimalist Enforcer**: default posture is “protect focus, reduce complexity, defer distractions,” while allowing explicit user overrides.
- Provide **quick recap onboarding** when returning after time away.
- Maintain **spec dependency graph** so prioritization and “what next” can be dependency-aware.
- Add **human-in-the-loop design gates** to reduce review friction.

### 1.3 Design Philosophy
- Integrate, don’t replace: works with existing agents.
- Strict structure for reliability; natural language CRUD for usability.
- Minimal UX; speak only at decision boundaries.
- Store state in small, diffable artifacts; store history as structured events.

---

## 2) Features of the Tool (What It Does)

### 2.1 Intent Management (First-Class)
Artifacts:
- Mission statement (what success means end-to-end)
- MVP definition (what must exist for “product stands up”)
- Constraints (engineering guardrails; e.g., keep architecture simple, avoid elaborate tests initially)

Behavior:
- Any feature/idea is evaluated against these artifacts.
- Intent changes are explicit and tracked, not accidental.

### 2.2 Backlog-First Idea Capture + Arbitration
Behavior:
- Any new idea is captured to backlog by default.
- Tool categorizes ideas into buckets (examples):
  - MVP-critical (should be scheduled soon)
  - Parked / Nice-to-have (defer until MVP is stable)
  - Archived / Not aligned (out of mission or violates constraints)
- Tool can:
  - merge/club similar items
  - retire items that are no longer relevant
  - surface items later when “timing is right” (e.g., after dependencies or milestones)

### 2.3 Minimalist Enforcer + Override Model
Default:
- Prevents non-MVP or high-complexity work from becoming the “current focus” unintentionally.

Override model (hybrid):
- Small exception → allow as one-time without changing intent.
- Big exception → prompt collaborative renegotiation (update mission/MVP/constraints).
- Repeated pattern → propose intent update because user behavior indicates changed priorities.

### 2.4 Prioritization + “What Next” Guidance
Behavior:
- Suggest next spec/feature based on:
  - MVP alignment
  - dependency unblocking
  - complexity/risk
  - current focus continuity (minimize context switching)
- Human stays in control:
  - agent proposes ranked options + rationale
  - user picks or overrides

### 2.5 Spec Dependency Graph (First-Class)
Behavior:
- Specs/features exist as nodes with explicit dependencies.
- Tool prevents implementing blocked nodes without an explicit override.
- Re-planning is supported: user can reorder, rewire dependencies, split/merge nodes.

### 2.6 Design Gate + Digestible Review
Before implementation:
- Generate a short design digest (one pager):
  - proposed architecture changes
  - impacted modules
  - main risks
  - open questions
- User can approve, modify, or reject.
- This becomes an explicit “gate” before writing code.

### 2.7 Quick Recap Onboarding (Return After Time Away)
When user opens project after time away or starts a new session:
- Mission reminder (1–2 lines)
- MVP status snapshot
- Top constraints
- Last active focus (what was being implemented)
- What changed since last session (from meta event log and git history)
- Top recommended next steps (2 items) + rationale

### 2.8 Lightweight Dashboard (Later UX, deferred)
Requirements:
- Extremely light.
- Presents:
  - intent summary (mission/MVP/constraints)
  - Now (current focus)
  - Next (top suggestions)
  - Backlog buckets
  - drift indicators (optional)

Non-requirement for v1:
- no heavy PM UI
- no complex drag-and-drop editor required initially

---

## 3) Specifications (Derived from Discussion)

### 3.1 Primary Use Cases (Original)
1. Adjust future specs even when sequential implementation intent exists.
2. “Next feature” should be intuitive; reduce manual selection burden.
3. Design review/interjection should be easy and digestible.
4. Visual block view of design/spec graph (lightweight) for preview and tweaks.

### 3.2 Intent Alignment Use Cases (Added Later)
- Prevent low-value additions from consuming time.
- Reduce anxiety that optimization/vision is being lost.
- Provide arbitration/prioritization like a common-sense PM + Scrum Master.
- Backlog-first with timing-aware resurfacing.
- Merge/retire ideas as relevance changes.

### 3.3 Non-Goals (Explicit)
- Do not replace the IDE.
- Do not require users to adopt a new agent runtime.
- Do not become a full Jira/Linear replacement.
- Do not enforce heavy ceremonies or formal frameworks.
- Do not be verbose or overly conversational.

### 3.4 Agent Personality Constraints (Tone/Behavior)
- Professional, direct, minimal.
- Speaks only at decision boundaries:
  - new idea capture
  - feature triage and planning
  - misalignment detection
  - before implementation
  - session onboarding
- Always provides clear options:
  - implement now / park / archive / adjust intent

---

## 4) Data Model / Schema (Implementation‑Oriented)

### 4.1 Purpose of the Data Model

The data model is the **single source of truth** that makes intent‑driven development possible. It exists to provide durable, inspectable, machine‑readable project state so that:

- The **agent cannot rely on chat history** or implicit assumptions.
- The **human can correct** the agent and the workflow at any time.
- The system can enforce **Mission → MVP → Constraints** consistently across sessions.
- The workflow can support **backlog-first arbitration**, **dependency-aware planning**, and **low-friction re-entry**.

Without this data model, the system collapses into “prompt-and-pray” behavior.

### 4.2 What the Data Model Must Enable (Responsibilities)

- **(R1) Represent Current Truth** — mission, MVP, constraints, backlog, spec graph. "What is true right now?"
- **(R2) Preserve Decision Context** — why was this idea parked, spec prioritized, MVP changed? "Why is it true?"
- **(R3) Enable Agent Enforcement** — deterministic validation of alignment, backlog-first, blocked specs, next steps.
- **(R4) Enable Human Correction and Override** — inspect, understand, override, edit directly.
- **(R5) Enable Re-entry / Onboarding** — what changed, current focus, recommended next, tied to mission/MVP.

### 4.3 What the Data Model Explicitly Does NOT Do

- No full event-sourcing replay requirement.
- No business logic embedded in data files (logic lives in skills/core).
- Does not replace git history.
- Not a full PM system (no sprints/epics/reporting).
- Does not store large design docs (references only).

### 4.4 Core Design: Separate State vs History

| Concern | Stored Where | Why |
|---|---|---|
| Current truth (small, bounded) | Domain JSON files | Fast inspection, diffable, stable |
| Decision rationale + linkage | `meta.jsonl` | Onboarding, explainability, traceability |
| Enforcement logic | Skills / core library | Replaceable, testable, tool-agnostic |
| UX surfaces | Thin, optional | Minimal UI |

### 4.5 Storage Layout

- `.intent/mission.json`, `mvp.json`, `constraints.json`, `backlog.json`, `specs.json`, `meta.jsonl`

Full field-level schema reference: `docs/design.md` §3.

### 4.6 Global Canonical IDs (Locked Decision)

All entities use global canonical IDs (`mis_001`, `mvp_012`, `con_007`, `idea_104`, `spec_058`, `evt_000391`) — stable cross-file linking, no file-scoped ID coupling.

### 4.7–4.10

Superseded by `docs/design.md` §3–4 (data model reference + event catalog). Kept here only as historical rationale for *why* the split exists — see §4.1–4.6 above.

---

## 5–9) Implementation, Architecture, Decision Log, Lifecycle, Skill Surface

Superseded by:
- `docs/architecture.md` — system diagrams, component design, repo layout
- `docs/design.md` — skill contracts, hooks, data model, event catalog
- `docs/roadmap.md` — phases, milestones, testing, distribution

The original decision log (§7) is still binding for product-level calls: Mission → MVP → Constraints hierarchy, backlog-first, minimalist-enforcer posture, hybrid override model, quick-recap onboarding, skills-first (not MCP-dependent) correctness. Only the *implementation* specifics (VS Code, agent-agnostic multi-surface framing) have changed.

---

## Appendix A: Example Quick Recap Output (Target)

- **Mission** — Build X that does Y end-to-end for Z users.
- **MVP Status** — 3 of 5 required capabilities implemented. Remaining: Export flow, Error handling.
- **Constraints** — Keep architecture simple. Avoid elaborate testing until core flows stabilize.
- **Last Focus** — `spec_012` – Async export pipeline (design approved, implementation in progress).
- **What Changed Since Last Session** — Parked 2 backlog items. Approved design for `spec_012`. 4 commits touching export and queue modules.
- **Recommended Next Step** — Finish `spec_012` to unblock remaining MVP flows.

## Appendix B: Backlog Classification Semantics

- **MVP-Critical** — directly required, often unblocks other work, prioritize unless explicitly deferred.
- **Parked** — potentially valuable, not required for MVP, intentionally deferred.
- **Archived** — misaligned or redundant. Not deletion — an explicit, audit-trailed decision.

## Appendix C: Git and Meta Event Correlation Model

- Meta events capture *why*; git commits capture *what*. Neither replaces the other.
- Association is additive (manual `git_refs` field in v1), not duplicative.
- Git history is never rewritten; commits are never auto-generated; meta events don't try to mirror git.
