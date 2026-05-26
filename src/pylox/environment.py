from __future__ import annotations

from dataclasses import dataclass, field

from pylox.exceptions import LoxRuntimeError
from pylox.token import Token


@dataclass
class Environment:
    enclosing: Environment | None = None
    values: dict[str, object] = field(init=False, default_factory=dict)

    def define(self, name: str, value: object) -> None:
        self.values[name] = value

    def get(self, name: Token) -> object:
        if name.lexeme in self.values:
            return self.values[name.lexeme]

        if self.enclosing is not None:
            return self.enclosing.get(name)

        raise LoxRuntimeError(f"Undefined variable '{name.lexeme}'", name)

    def assign(self, name: Token, value: object) -> object:
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return

        raise LoxRuntimeError(f"Undefined variable '{name.lexeme}'", name)
