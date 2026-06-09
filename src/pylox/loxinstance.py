from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pylox.exceptions import LoxRuntimeError

if TYPE_CHECKING:
    from pylox.loxclass import LoxClass
    from pylox.token import Token


@dataclass
class LoxInstance:
    klass: LoxClass
    fields: dict[str, object] = field(default_factory=dict)

    def get(self, name: Token):
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]

        method = self.klass.find_method(name.lexeme)
        if method is not None:
            return method.bind(self)

        raise LoxRuntimeError(f"Undefined proprety {name.lexeme}.", name)

    def set(self, name: Token, value: object):
        self.fields[name.lexeme] = value

    def __str__(self) -> str:
        return f"{self.klass.name} instance"

    def __repr__(self) -> str:
        return f"LoxInstance<{self.klass.name}>"
