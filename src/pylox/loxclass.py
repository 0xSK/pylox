from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pylox.function import LoxCallable, LoxFunction
from pylox.loxinstance import LoxInstance

if TYPE_CHECKING:
    from pylox.interpreter import Interpreter


@dataclass
class LoxClass(LoxCallable):
    name: str
    methods: dict[str, LoxFunction]

    # for LoxCallable
    @property
    def arity(self) -> int:
        return 0

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        instance = LoxInstance(self)
        return instance

    def find_method(self, name: str) -> LoxFunction | None:
        if name in self.methods:
            return self.methods[name]
        return None

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        return f"LoxClass<{self.name}>"
