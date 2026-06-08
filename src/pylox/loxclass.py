from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pylox.function import LoxCallable
from pylox.loxinstance import LoxInstance

if TYPE_CHECKING:
    from pylox.interpreter import Interpreter


@dataclass
class LoxClass(LoxCallable):
    name: str

    # for LoxCallable
    @property
    def arity(self) -> int:
        return 0

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        instance = LoxInstance(self)
        return instance

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        return f"LoxClass<{self.name}>"
