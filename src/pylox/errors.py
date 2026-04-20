from __future__ import annotations

from abc import ABC
from typing import Protocol

from pylox.token import Token


class LineErrorCallback(Protocol):
    def __call__(self, line: int, message: str) -> None: ...


class TokenErrorCallback(Protocol):
    def __call__(self, token: Token, message: str) -> None: ...


class LoxErrorBase(Exception, ABC):
    pass


class ParserError(LoxErrorBase):
    pass
