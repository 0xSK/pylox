from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from functools import singledispatchmethod
from typing import Any, Protocol, runtime_checkable

from numpy import format_float_positional

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
    def visit(self, expr: Expr) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
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
        elif expr is True:
            return "true"
        elif expr is False:
            return "false"
        elif isinstance(expr.value, str):
            return f'"{expr.value}"'
        elif isinstance(expr.value, float):
            return format_float_positional(
                expr.value,
                precision=17,  # up to 17 significant digits
                unique=True,  # shortest string that round-trips to the same float
                fractional=True,  # always keep a decimal point with at least one digit
                trim="0",  # trim trailing zeros, but keep at least one fractional digit
            )
        else:
            raise TypeError(f"Unexpected Literal {LiteralExpr}")

    @visit.register
    def _(self, expr: UnaryExpr) -> str:
        return self.parenthesize(str(expr.operator.lexeme), expr.right)

    @visit.register
    def _(self, expr: BinaryExpr) -> str:
        return self.parenthesize(str(expr.operator.lexeme), expr.left, expr.right)


class RpnPrinter(Visitor[str]):
    def pformat(self, expr: Expr) -> str:
        return expr.accept(self)

    def merge(self, *parts: str | Expr) -> str:
        values: list[str] = []
        for part in parts:
            if isinstance(part, str):
                values.append(part)
            elif isinstance(part, Expr):
                values.append(part.accept(self))
            else:
                raise TypeError()
        return " ".join(value.strip() for value in values if value.strip())

    @singledispatchmethod
    def visit(self, expr: Expr) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
        raise NotImplementedError(f"The `visit` dispatcher for {type(expr)} objects is not defined")

    @visit.register
    def _(self, expr: AssignExpr) -> str:
        return self.merge(f"{expr.name}=", expr.value)

    @visit.register
    def _(self, expr: GroupingExpr) -> str:
        return self.visit(expr.expression)

    @visit.register
    def _(self, expr: LiteralExpr) -> str:
        if expr.value is None:
            return "nil"
        return str(expr.value)

    @visit.register
    def _(self, expr: UnaryExpr) -> str:
        return self.merge(expr.right, str(expr.operator.lexeme))

    @visit.register
    def _(self, expr: BinaryExpr) -> str:
        return self.merge(expr.left, expr.right, str(expr.operator.lexeme))


if __name__ == "__main__":
    from pylox.token import TokenType

    expression: Expr = BinaryExpr(
        UnaryExpr(Token(TokenType.MINUS, "-", None, 1), LiteralExpr(123)),
        Token(TokenType.STAR, "*", None, 1),
        GroupingExpr(LiteralExpr(45.67)),
    )

    astPrinter = RpnPrinter()
    print(astPrinter.pformat(expression))

    expression: Expr = BinaryExpr(
        GroupingExpr(
            BinaryExpr(
                LiteralExpr(1),
                Token(TokenType.PLUS, "+", None, 1),
                LiteralExpr(2),
            )
        ),
        Token(TokenType.STAR, "*", None, 1),
        GroupingExpr(
            BinaryExpr(
                LiteralExpr(4),
                Token(TokenType.MINUS, "-", None, 1),
                LiteralExpr(3),
            )
        ),
    )

    rpnPrinter = RpnPrinter()
    print(rpnPrinter.pformat(expression))
