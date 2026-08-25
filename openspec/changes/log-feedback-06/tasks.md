# Tasks: Feedback Logging Skill — log-feedback-06

## Core Extension (mission_ctrl_core)
- [ ] New event type `FEEDBACK_LOGGED` added to `EventBuilder`
- [ ] `FeedbackEvent` Pydantic model: category, description, severity,
      related_spec_id (optional), timestamp, event_id
- [ ] `MetaStore.read_feedback(severity: str | None = None)` — returns all
      `FEEDBACK_LOGGED` events, filtered by severity if provided
- [ ] Unit tests: FeedbackEvent model validation; read_feedback filtering;
      EventBuilder emits correct event type

## Skill (mission_ctrl_pi)
- [ ] Add `LogFeedbackInput` and `LogFeedbackResult` to `schemas.py`
- [ ] `intent:log-feedback` skill:
      - Input: category, description, severity, related_spec_id (optional)
      - Validates category and severity are within allowed literals
      - Calls EventBuilder + MetaStore.append()
      - Returns LogFeedbackResult(feedback_id, status="logged")
- [ ] Register `intent:log-feedback` in `extension.py` manifest

## Tests
- [ ] Skill test: valid feedback written to meta.jsonl with correct structure
- [ ] Skill test: invalid category/severity raises SkillError(INVALID_INPUT)
- [ ] Integration: read_feedback() returns only events matching the requested
      severity filter
- [ ] Test: `intent:log-feedback` leaves all `.intent/` files untouched except
      meta.jsonl
