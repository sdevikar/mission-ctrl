---
description: Log a structured dogfood issue (false positive, planner miss, verbosity, hook behavior, bug, UX). Use when anything in the intent loop behaves unexpectedly during real use.
---

# intent:log-feedback

> Pending: this skill lands in `log-feedback-06` and is not implemented yet.
> Until then the wrapper answers `NOT_IMPLEMENTED`; record dogfood issues as
> plain notes. This file pins the planned contract so the plugin is ready the
> moment the skill ships.

Capture structured dogfood observations — false positives, planner misses,
recap verbosity complaints, hook misfires — tagged by category and severity
so M5 fixes are evidence-based rather than anecdotal.

## Planned input

The `log-feedback-06` proposal pins this contract:

- `category`: one of `false_positive`, `planner_miss`, `recap_verbosity`,
  `hook_behavior`, `bug`, `ux`, `other`
- `description`: free-form text (what happened, what was expected)
- `severity`: one of `blocker`, `polish`, `backlog`
- `related_spec_id`: optional spec the issue is associated with

Example (illustrative — validate against `LogFeedbackInput` once it exists):

```text
category=bug, severity=polish, description="...", related_spec_id=spec_001
```

## Planned invocation

```bash
mission-ctrl skill log-feedback --cwd "<project-dir>" <<'EOF'
<LogFeedbackInput JSON>
EOF
```

## Errors

- `NOT_IMPLEMENTED` — expected until `log-feedback-06` ships.
