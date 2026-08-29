from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from ..errors import render_validation_error

ModelT = TypeVar("ModelT", bound=BaseModel)


def utcnow() -> datetime:
    return datetime.now(UTC)


def atomic_write_json(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(path)


class Store(Generic[ModelT]):
    """Single-document JSON store: one pydantic model per file."""

    FILENAME: ClassVar[str]
    MODEL: ClassVar[type[BaseModel]]

    def __init__(self, intent_dir: Path | str) -> None:
        self.dir = Path(intent_dir)
        self.path = self.dir / self.FILENAME

    def read(self) -> ModelT:
        raw = self.path.read_text(encoding="utf-8")
        try:
            return self.MODEL.model_validate_json(raw)  # type: ignore[arg-type]
        except ValidationError as exc:
            raise render_validation_error(self.FILENAME, exc) from exc

    def write(self, model: ModelT) -> None:
        atomic_write_json(self.path, model.model_dump_json(indent=2))
