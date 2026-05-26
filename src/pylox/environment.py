from __future__ import annotations

from dataclasses import dataclass, field

from pylox.exceptions import LoxRuntimeError, PyloxImpossibleCaseError
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

    def get_at(self, distance: int, name: str) -> object:
        resolved_environment = self.ancestor(distance)
        if name not in resolved_environment.values:
            raise PyloxImpossibleCaseError("Resolved environment depth is incorrect")
        return resolved_environment.values[name]

    def ancestor(self, distance: int) -> Environment:
        if distance == 0:
            return self

        if self.enclosing is None:
            raise PyloxImpossibleCaseError(
                "Resolved environment depth is deeper than environment nesting"
            )

        return self.enclosing.ancestor(distance - 1)

    def assign(self, name: Token, value: object) -> None:
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return

        raise LoxRuntimeError(f"Undefined variable '{name.lexeme}'", name)

    def assign_at(self, distance: int, name: Token, value: object) -> None:
        resolved_environment = self.ancestor(distance)
        resolved_environment.values[name.lexeme] = value
