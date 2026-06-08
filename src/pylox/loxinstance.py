from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pylox.loxclass import LoxClass


@dataclass
class LoxInstance:
    klass: LoxClass

    def __str__(self) -> str:
        return f"{self.klass.name} instance"

    def __repr__(self) -> str:
        return f"LoxInstance<{self.klass.name}>"
