# Mission Ctrl — Architecture
## v1 scope: Pi extension, pure Python core. No Claude plugin, no MCP, no bridge.
Status: current source of truth. Supersedes the architecture sections of
`mission-ctrl-technical-roadmap.md`, `mission-ctrl-common.md`,
`mission-ctrl-claude-plugin.md`, `mission-ctrl-pi-package.md` (all deleted — see roadmap.md
for what's deferred and why).

---

## 1. System Context

```mermaid
flowchart LR
    Dev["Developer"]
    Agent["Pi (coding agent)"]
    Ext["Pi Extension\n(Python: hooks + skills)"]
    Core["mission_ctrl_core\n(pure Python lib, no network)"]
    State[".intent/ files\n(repo, git-tracked)"]
    Git["git log / commits"]
    MD["AGENTS.md\n(auto-generated)"]

    Dev -->|types in chat| Agent
    Agent -->|calls skill| Ext
    Ext -->|direct import, in-process| Core
    Core -->|validate + persist| State
    Core -->|read only| Git
    Ext -->|regenerate| MD
    MD -->|loaded natively by Pi| Agent
```

No subprocess boundary, no external network call anywhere. Pi is the only LLM in the system — it reasons in its own context; core only validates and persists what Pi tells it.

---

## 2. Component Diagram

```mermaid
flowchart TB
    subgraph PiPackage["pi-package (Python)"]
        Hooks["Hooks: on_session_start, on_before_send"]
        Skills["9 skills — see design.md §2"]
        Sync["AGENTS.md sync"]
    end

    subgraph Core["mission_ctrl_core (Python)"]
        Store["Store layer\nMission/Mvp/Backlog/Spec/Constraints/Meta"]
        Logic["Logic layer\nplanner.py, recap.py (no LLM calls)"]
        Schema["pydantic models (validation + typing)"]
        EventB["EventBuilder"]
    end

    Skills --> Store
    Skills --> Logic
    Store --> Schema
    Store --> EventB
    Hooks --> Skills
    Skills --> Sync
```

Two packages, one language, one process. `mission_ctrl_core` stays a separate pip package so it's reusable later — see §6 for the cost of reusing it from a non-Python surface.

---

## 3. Data Flow — Core Loop

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Pi as Pi (reasoning)
    participant Skill as Pi Skill
    participant Core as mission_ctrl_core
    participant Meta as meta.jsonl

    Dev->>Pi: "exports should be async"
    Pi->>Skill: add_idea(title, description)
    Skill->>Core: BacklogStore.add()
    Core->>Meta: BACKLOG_ADDED

    Pi->>Pi: reason about alignment (in-context)
    Pi->>Skill: triage(idea_id, bucket, alignment)
    Skill->>Core: BacklogStore.update()
    Core->>Meta: BACKLOG_TRIAGE

    Pi->>Skill: spec_create(idea_id)
    Skill->>Core: SpecStore.add()
    Core->>Meta: SPEC_CREATED

    Pi->>Pi: draft digest (in-context)
    Pi->>Skill: design_propose(spec_id, digest)
    Skill->>Core: SpecStore.update() (validate + store only)
    Core->>Meta: DESIGN_PROPOSED

    Dev->>Pi: approve
    Pi->>Skill: design_approve(spec_id, "approved")
    Core->>Meta: DESIGN_APPROVED

    Dev->>Pi: "implement it" (raw request, no backlog ref)
    Pi->>Pi: on_before_send hook intercepts
    Pi-->>Dev: "spec_001 needs design approval first" (or proceeds if already approved)

    Dev->>Pi: writes code directly
    Pi->>Skill: spec_status(spec_id, in_progress -> done)
    Core->>Meta: SPEC_STATUS_UPDATED

    Dev->>Pi: (next day) opens project
    Pi->>Skill: recap()
    Skill->>Core: generate_recap()
    Core-->>Pi: RecapResult
```

---

## 4. Data Model Relationships

```mermaid
flowchart TB
    Mission["mission.json"] --> Backlog["backlog.json"]
    MVP["mvp.json"] --> Backlog
    Constraints["constraints.json"] --> Backlog
    Backlog --> Specs["specs.json"]
    Specs --> Git["git commits (manual git_refs)"]
    Mission --> Meta["meta.jsonl"]
    Backlog --> Meta
    Specs --> Meta
    Meta --> MD["AGENTS.md (derived, regenerated)"]
```

File format (JSON/JSONL) is language-agnostic by design — see `docs/examples/domain/` for live samples. This is unchanged regardless of core implementation language.

---

## 5. Repository Layout

```
mission-ctrl/
├── packages/
│   ├── core/                     # mission_ctrl_core (Python, pip)
│   │   ├── mission_ctrl_core/
│   │   │   ├── models/           # pydantic models (replaces old *.schema.json + AJV)
│   │   │   ├── store/            # IntentStore + sub-stores
│   │   │   ├── logic/            # planner.py, recap.py
│   │   │   └── events/           # EventBuilder
│   │   ├── tests/
│   │   │   └── fixtures/         # empty-project, mid-flight, complex-graph
│   │   └── pyproject.toml
│   │
│   └── pi-package/               # mission_ctrl_pi (Python, depends on core)
│       ├── mission_ctrl_pi/
│       │   ├── extension.py
│       │   ├── hooks/
│       │   │   ├── on_session_start.py
│       │   │   └── on_before_send.py
│       │   ├── skills/
│       │   └── sync/agents_md_sync.py
│       ├── templates/AGENTS.md
│       └── pyproject.toml
│
├── docs/
│   ├── concept.md
│   ├── architecture.md           # this file
│   ├── design.md
│   ├── roadmap.md
│   ├── scratchpad.md
│   └── examples/
│
└── README.md
```

Runtime layout inside a user's project is unchanged: `.intent/*.json`, `.intent/meta.jsonl`, `AGENTS.md` at repo root, committed to git.

---

## 6. Deferred Cost (accepted, not resolved)

Building a Claude Code plugin later means either:
- (a) a Node → Python subprocess bridge (mirror image of the bridge we removed), or
- (b) porting `mission_ctrl_core` to TypeScript, duplicating it.

Not a v1 decision. Revisit only when the Claude plugin is actually scheduled — see `roadmap.md` Backlog.
