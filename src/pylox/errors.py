from __future__ import annotations

from typing import Protocol


class LineErrorCallback(Protocol):
    def __call__(self, line: int, message: str) -> None: ...
