from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pylox.interpreter import Interpreter


@runtime_checkable
class LoxCallable(Protocol):
    @property
    def arity(self) -> int: ...
    def call(self, interpreter: Interpreter, arguments: list[object]) -> object: ...
