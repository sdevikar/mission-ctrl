from __future__ import annotations

from pydantic import ValidationError


class MissionCtrlError(Exception):
    """Base error for all core failures."""


def _format_loc(loc: tuple[object, ...]) -> str:
    out = ""
    for i, part in enumerate(loc):
        if isinstance(part, int):
            out += f"[{part}]"
        elif i == 0:
            out += str(part)
        else:
            out += f".{part}"
    return out or "<root>"


def render_validation_error(filename: str, exc: ValidationError) -> MissionCtrlError:
    """Render a pydantic error as ``<file>: <path.to.field>: <message>``."""
    parts = []
    for err in exc.errors():
        path = _format_loc(err.get("loc", ()))
        msg = err.get("msg", "invalid value")
        parts.append(f"{filename}: {path}: {msg}")
    return MissionCtrlError("; ".join(parts))
