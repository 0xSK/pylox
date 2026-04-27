import math
from functools import singledispatchmethod
from typing import TypeGuard

from pylox.errors import LoxRuntimeError, PyloxImpossibleCaseError, RuntimeErrorCallback
from pylox.expression import (
    BinaryExpr,
    Expr,
    GroupingExpr,
    LiteralExpr,
    UnaryExpr,
    Visitor,
)
from pylox.token import Token, TokenType
from pylox.knobs import get_knob

class Interpreter(Visitor[object]):
    def __init__(self, error_callback: RuntimeErrorCallback) -> None:
        self.error_callback = error_callback

    def interpret(self, expr: Expr) -> object:
        try:
            value = self.evaluate(expr)
            return value
        except LoxRuntimeError as e:
            self.error_callback(e)
        except Exception as e:
            raise PyloxImpossibleCaseError() from e

    def evaluate(self, expr: Expr) -> object:
        return expr.accept(self)

    def stringify(self, value: object) -> str:
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, float):
            from numpy import format_float_positional

            return format_float_positional(
                value,
                precision=17,  # up to 17 significant digits
                unique=True,  # shortest string that round-trips to the same float
                fractional=True,  # always keep a decimal point with at least one digit
                trim="0",  # trim trailing zeros, but keep at least one fractional digit
            )
        if isinstance(value, str):
            return f'"{value}"'
        raise PyloxImpossibleCaseError()

    @singledispatchmethod
    def visit(self, expr: Expr) -> object:  # pyright: ignore[reportIncompatibleMethodOverride]
        raise NotImplementedError(f"The `visit` dispatcher for {type(expr)} objects is not defined")

    @visit.register
    def _(self, expr: GroupingExpr) -> object:
        return self.evaluate(expr.expression)

    @visit.register
    def _(self, expr: LiteralExpr) -> object:
        return expr.value

    @visit.register
    def _(self, expr: UnaryExpr) -> object:
        right_value: object = self.evaluate(expr.right)

        match expr.operator.type:
            case TokenType.BANG:
                return not self.is_truthy(right_value)
            case TokenType.MINUS:
                if self.check_number_operand(right_value, expr.operator):
                    return -right_value
            case t:
                PyloxImpossibleCaseError(f"Unexpected token type: {t}")

        PyloxImpossibleCaseError()

    @visit.register
    def _(self, expr: BinaryExpr) -> object:
        left_value: object = self.evaluate(expr.left)
        right_value: object = self.evaluate(expr.right)

        match expr.operator.type:
            case TokenType.MINUS:
                if self.check_number_operand(left_value, expr.operator):
                    if self.check_number_operand(right_value, expr.operator):
                        return left_value - right_value

            case TokenType.STAR:
                if self.check_number_operand(left_value, expr.operator):
                    if self.check_number_operand(right_value, expr.operator):
                        return left_value * right_value

            case TokenType.SLASH:
                if self.check_number_operand(left_value, expr.operator):
                    if self.check_number_operand(right_value, expr.operator):
                        try:
                            return left_value / right_value
                        except ZeroDivisionError as e:
                            if get_knob('divide_by_zero_error'):
                                raise LoxRuntimeError(f"Division by zero is not allowed", expr.operator)
                            if left_value == 0.0:
                                return math.nan
                            elif left_value > 0.0:
                                return math.inf
                            elif left_value < 0.0:
                                return -math.inf
                            raise PyloxImpossibleCaseError() from e

            case TokenType.PLUS:
                if isinstance(left_value, float) and isinstance(right_value, float):
                    return left_value + right_value
                elif isinstance(left_value, str) and isinstance(right_value, str):
                    return f"{left_value}{right_value}"
                raise LoxRuntimeError("Operands must be two numbers or two strings", expr.operator)

            case TokenType.GREATER:
                if self.check_number_operand(left_value, expr.operator):
                    if self.check_number_operand(right_value, expr.operator):
                        return left_value > right_value

            case TokenType.GREATER_EQUAL:
                if self.check_number_operand(left_value, expr.operator):
                    if self.check_number_operand(right_value, expr.operator):
                        return left_value >= right_value

            case TokenType.LESS:
                if self.check_number_operand(left_value, expr.operator):
                    if self.check_number_operand(right_value, expr.operator):
                        return left_value < right_value

            case TokenType.LESS_EQUAL:
                if self.check_number_operand(left_value, expr.operator):
                    if self.check_number_operand(right_value, expr.operator):
                        return left_value <= right_value

            case TokenType.EQUAL_EQUAL:
                return self.is_equal(left_value, right_value)

            case TokenType.BANG_EQUAL:
                return not self.is_equal(left_value, right_value)

            case t:
                PyloxImpossibleCaseError(f"Unexpected token type: {t}")

        PyloxImpossibleCaseError()

    def is_truthy(self, value: object) -> bool:
        if value is False or value is None:
            return False
        return True

    def is_equal(self, a: object, b: object) -> bool:
        return type(a) is type(b) and a == b

    def check_number_operand(self, operand: object, operator: Token) -> TypeGuard[float]:
        if not isinstance(operand, float):
            raise LoxRuntimeError("Operand must be a number", operator)
        return True
