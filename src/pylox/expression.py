from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from functools import singledispatchmethod
from typing import Any, Protocol, runtime_checkable

from pylox.token import Token


class Expr(ABC):  # noqa: B024
    def accept[T](self, visitor: Visitor[T]) -> T:
        return visitor.visit(self)


@dataclass
class AssignExpr(Expr):
    name: Token
    value: Expr


@dataclass
class GroupingExpr(Expr):
    expression: Expr


@dataclass
class LiteralExpr(Expr):
    value: Any


@dataclass
class UnaryExpr(Expr):
    operator: Token
    right: Expr


@dataclass
class BinaryExpr(Expr):
    left: Expr
    operator: Token
    right: Expr


@runtime_checkable
class Visitor[R](Protocol):
    def visit(self, expr: Expr) -> R: ...


class AstPrinter(Visitor[str]):
    def pformat(self, expr: Expr) -> str:
        return expr.accept(self)

    def parenthesize(self, name: str, *expressions: Expr):
        s = f"({name}"
        for expression in expressions:
            s += f" {expression.accept(self)}"
        s += ")"
        return s

    @singledispatchmethod
    def visit(self, expr: Expr) -> str:
        raise NotImplementedError(f"The `visit` dispatcher for {type(expr)} objects is not defined")

    @visit.register
    def _(self, expr: AssignExpr) -> str:
        return self.parenthesize(f"{expr.name}=", expr.value)

    @visit.register
    def _(self, expr: GroupingExpr) -> str:
        return self.parenthesize("group", expr.expression)

    @visit.register
    def _(self, expr: LiteralExpr) -> str:
        if expr.value is None:
            return "nil"
        return str(expr.value)

    @visit.register
    def _(self, expr: UnaryExpr) -> str:
        return self.parenthesize(str(expr.operator.lexeme), expr.right)

    @visit.register
    def _(self, expr: BinaryExpr) -> str:
        return self.parenthesize(str(expr.operator.lexeme), expr.left, expr.right)


if __name__ == "__main__":
    from pylox.token import TokenType

    expression: Expr = BinaryExpr(
        UnaryExpr(Token(TokenType.MINUS, "-", None, 1), LiteralExpr(123)),
        Token(TokenType.STAR, "*", None, 1),
        GroupingExpr(LiteralExpr(45.67)),
    )

    astPrinter = AstPrinter()
    print(astPrinter.pformat(expression))
