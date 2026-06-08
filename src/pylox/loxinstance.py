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
        if name.lexeme not in self.fields:
            raise LoxRuntimeError(f"Undefined proprety {name.lexeme}.", name)
        return self.fields[name.lexeme]

    def set(self, name: Token, value: object):
        self.fields[name.lexeme] = value

    def __str__(self) -> str:
        return f"{self.klass.name} instance"

    def __repr__(self) -> str:
        return f"LoxInstance<{self.klass.name}>"
