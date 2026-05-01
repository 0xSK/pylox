from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from pylox.expression import Expr


class Stmt(ABC):  # noqa: B024
    def accept[T](self, visitor: StmtVisitor[T]) -> T:
        return visitor.visit(self)


@runtime_checkable
class StmtVisitor[T](Protocol):
    def visit(self, stmt: Stmt) -> T: ...


@dataclass
class ExpressionStmt(Stmt):
    expr: Expr


@dataclass
class PrintStmt(Stmt):
    expr: Expr
