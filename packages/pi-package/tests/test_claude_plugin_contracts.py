"""Contract tests for the Claude Code plugin (claude-plugin-08).

Every SKILL.md ````json input block MUST validate against its Pydantic
schema 1:1 — doc/schema drift fails the build. Structural checks pin the
plugin layout to the upstream plugin reference (manifest, hooks.json shape).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from mission_ctrl_pi import schemas

PLUGIN_DIR = Path(__file__).resolve().parents[2] / "claude-plugin"

# skill dir -> Input model; None = skill takes no input (block must be {});
# "PENDING" = skill not implemented yet (no json block, must carry marker).
CONTRACTS: dict[str, object] = {
    "intent-init": schemas.InitInput,
    "intent-add-idea": schemas.AddIdeaInput,
    "intent-triage": schemas.TriageInput,
    "intent-spec-create": schemas.SpecCreateInput,
    "intent-spec-status": schemas.SpecStatusInput,
    "intent-design-propose": schemas.DesignProposeInput,
    "intent-design-approve": schemas.DesignApproveInput,
    "intent-recap": schemas.RecapInput,
    "intent-next": None,
    "intent-status": None,
    "intent-log-feedback": "PENDING",
}

FENCE = re.compile(r"```json\s*\n(.*?)```", re.DOTALL)


def _read_skill(name: str) -> str:
    path = PLUGIN_DIR / "skills" / name / "SKILL.md"
    assert path.is_file(), f"missing {path}"
    return path.read_text(encoding="utf-8")


def test_all_expected_skills_present():
    for name in CONTRACTS:
        assert (PLUGIN_DIR / "skills" / name / "SKILL.md").is_file(), name


def test_skill_input_blocks_match_schemas():
    failures = []
    for name, model in CONTRACTS.items():
        if model == "PENDING" or model is None:
            continue
        blocks = FENCE.findall(_read_skill(name))
        assert len(blocks) == 1, f"{name}: expected 1 json block, got {len(blocks)}"
        try:
            model.model_validate(json.loads(blocks[0]))
        except Exception as exc:
            failures.append(f"{name}: {exc}")
    assert not failures, "\n".join(failures)


def test_no_input_skills_document_empty_object():
    for name in ("intent-next", "intent-status"):
        blocks = FENCE.findall(_read_skill(name))
        assert len(blocks) == 1, f"{name}: expected 1 json block"
        assert json.loads(blocks[0]) == {}, f"{name}: input block must be {{}}"


def test_pending_skills_carry_marker_and_no_contract():
    text = _read_skill("intent-log-feedback")
    assert FENCE.findall(text) == []
    assert "Pending" in text and "log-feedback-06" in text


def test_skill_frontmatter_has_description():
    for name in CONTRACTS:
        text = _read_skill(name)
        assert text.startswith("---"), f"{name}: missing frontmatter"
        head = text.split("---", 2)[1]
        assert "description:" in head, f"{name}: frontmatter needs description"


def test_plugin_manifest():
    manifest = json.loads((PLUGIN_DIR / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "mission-ctrl"
    assert manifest["description"]
    assert "skills/" not in json.dumps(manifest)


def test_hooks_json_shape():
    hooks = json.loads((PLUGIN_DIR / "hooks" / "hooks.json").read_text())
    assert set(hooks) == {"SessionStart", "UserPromptSubmit"}
    for event, groups in hooks.items():
        assert groups, event
        for group in groups:
            for handler in group["hooks"]:
                assert handler["type"] == "command", event
                assert handler["command"].startswith(
                    "${CLAUDE_PLUGIN_ROOT}/bin/mission-ctrl hook "
                ), event
    commands = [h["command"] for gs in hooks.values() for g in gs for h in g["hooks"]]
    assert any("hook session-start" in c for c in commands)
    assert any("hook before-send" in c for c in commands)
