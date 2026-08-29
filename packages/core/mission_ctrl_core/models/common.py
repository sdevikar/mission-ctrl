from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, PlainSerializer


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamp must include a UTC offset")
    return value.astimezone(timezone.utc)


def _to_zulu(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


UtcDatetime = Annotated[
    datetime,
    AfterValidator(_require_utc),
    PlainSerializer(_to_zulu, return_type=str, when_used="json"),
]


def id_validator(prefix: str, width: int):
    pattern = re.compile(rf"^{prefix}_\d{{{width},}}$")

    def check(value: str) -> str:
        if not pattern.match(value):
            raise ValueError(f"must be '{prefix}_' followed by at least {width} digits")
        return value

    return AfterValidator(check)


def next_id(prefix: str, width: int, existing: list[str]) -> str:
    highest = 0
    for candidate in existing:
        digits = candidate.rsplit("_", 1)[-1]
        if digits.isdigit():
            highest = max(highest, int(digits))
    return f"{prefix}_{highest + 1:0{width}d}"


MisId = Annotated[str, id_validator("mis", 3)]
MvpId = Annotated[str, id_validator("mvp", 3)]
ConId = Annotated[str, id_validator("con", 3)]
IdeaId = Annotated[str, id_validator("idea", 3)]
SpecId = Annotated[str, id_validator("spec", 3)]
EvtId = Annotated[str, id_validator("evt", 6)]
