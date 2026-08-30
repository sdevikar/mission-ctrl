# Design: Logic Layer (M1)

Builds on M0 stores (`IntentStore` + per-file stores) and the three shared
fixtures. No new models except the recap output contract.

## Key decisions

- **No LLM / alignment in core.** Alignment verdicts and design digests are
  judgment calls that Pi (the agent) makes. The logic layer therefore takes
  *structured results* as inputs or simply reports stored state — it never
  calls a model. This keeps `mission_ctrl_core` importable offline and testable
  deterministically. Pi supplies the structured inputs to skills (change 03).

- **Planner ranking order** (`planner.suggest_next`), applied as lexicographic
  sort keys:
  1. **MVP-linked first** — `SpecNode.links.mvp_items` non-empty.
  2. **Fewer unresolved dependencies first** — a spec is a candidate only if
     every `depends_on` entry is `done`; ties broken by the count of remaining
     (unresolved) deps (always 0 at this point, but the key is kept so a
     relaxed gate in future sorts sensibly).
  3. **Current-focus continuity first** — the candidate's feature area
     (its deps + idea/mvp links) intersects the in-progress spec's feature area.
  4. **Stable by `spec_id`** — deterministic tie-break.

  Candidates are restricted to `draft`, `design_proposed`, `design_approved`.
  `in_progress` and `done` are already "working/finished"; blocked specs are
  excluded by rule 2.

- **Recap is a `RecapResult` pydantic model**, imported (not redefined) by the
  Pi package. Fields: mission statement, `mvp_completed/total/percent`,
  `last_focus` (first `in_progress` spec), `changes` (git commit summary),
  `recommendations` (from `suggest_next`), `events_since`, `verbosity`, and a
  rendered markdown `rendered` string.
  - **MVP %** = MVP items whose `linked_specs` are all in `done` states, divided
    by total items (0% when empty).
  - **Changes-since** is bounded by an explicit `since_iso` (UTC) when given:
    meta events strictly after it, plus `git log --since <iso>` (read-only).

- **Verbosity tiers** (`brief` / `standard` / `full`): `brief` = mission + % +
  focus + top suggestion; `standard` = + changes section + up to 5
  recommendations; `full` = like standard but the "Next up" list is the full
  ranked set. Tier *selection* by session gap is the hook's job (change 04);
  here the tier is an explicit parameter.

- **Git is read-only.** `gitutil.git_commits_since` runs
  `git log --no-pager --since <iso> --pretty=format:%h<TAB>%s` and parses it.
  No `git add/status --write`, no index mutation; returns `[]` for a non-repo
  or any error, so recap never fails over git.

## Constraints

- No network, no LLM. Only stdlib `subprocess` used, read-only, with a timeout.
- Must run against all three fixtures (empty-project, mid-flight,
  complex-graph) and produce `validate_all()`-clean, deterministic output.
