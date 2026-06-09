from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pylox.environment import Environment
from pylox.exceptions import LoxReturn
from pylox.statement import FunctionStmt

if TYPE_CHECKING:
    from pylox.interpreter import Interpreter
    from pylox.loxinstance import LoxInstance


@runtime_checkable
class LoxCallable(Protocol):
    @property
    def arity(self) -> int: ...
    def call(self, interpreter: Interpreter, arguments: list[object]) -> object: ...


@dataclass
class LoxFunction(LoxCallable):
    declaration: FunctionStmt
    closure: Environment
    isInitializer: bool

    @property
    def arity(self) -> int:
        return len(self.declaration.params)

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        environment = Environment(self.closure)
        for param, argument in zip(self.declaration.params, arguments, strict=True):
            environment.define(param.lexeme, argument)

        try:
            interpreter.executeBlock(self.declaration.body, Environment(environment))
        except LoxReturn as ret:
            if self.isInitializer:
                return self.closure.get_at(0, "this")
            return ret.value

        if self.isInitializer:
            return self.closure.get_at(0, "this")

        return None

    def bind(self, instance: LoxInstance) -> LoxFunction:
        environment = Environment(self.closure)
        environment.define("this", instance)
        return LoxFunction(self.declaration, environment, self.isInitializer)

    def __str__(self) -> str:
        return f"<fn {self.declaration.name.lexeme}>"
