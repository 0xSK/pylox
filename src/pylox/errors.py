from __future__ import annotations

from abc import ABC
from typing import Protocol

from pylox.token import Token


class LineErrorCallback(Protocol):
    def __call__(self, line: int, message: str) -> None: ...


class TokenErrorCallback(Protocol):
    def __call__(self, token: Token, message: str) -> None: ...

class RuntimeErrorCallback(Protocol):
    def __call__(self, error: LoxRuntimeError) -> None: ...

class LoxErrorBase(Exception, ABC):
    pass


class LoxParserError(LoxErrorBase):
    pass


class LoxRuntimeError(LoxErrorBase):
    def __init__(self, message: str, token: Token):
        super().__init__(message)
        self.token = token


class PyloxImpossibleCaseError(Exception):
    "Exception for all Pylox coding errors. This should be used for impossible cases."

    pass
