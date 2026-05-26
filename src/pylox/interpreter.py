import math
import time
from functools import singledispatchmethod
from typing import Any, TypeGuard

from pylox.environment import Environment
from pylox.exceptions import (
    LoxReturn,
    LoxRuntimeError,
    PyloxImpossibleCaseError,
    RuntimeErrorCallback,
)
from pylox.expression import (
    AssignExpr,
    BinaryExpr,
    BinaryLogicalExpr,
    CallExpr,
    Expr,
    ExprVisitor,
    GroupingExpr,
    LiteralExpr,
    UnaryExpr,
    VarExpr,
)
from pylox.function import LoxCallable, LoxFunction
from pylox.knobs import get_knob
from pylox.statement import (
    BlockStmt,
    ExpressionStmt,
    FunctionStmt,
    IfStmt,
    PrintStmt,
    ReturnStmt,
    Stmt,
    StmtVisitor,
    VarStmt,
    WhileStmt,
)
from pylox.token import Token, TokenType


class Interpreter(ExprVisitor[object], StmtVisitor[None]):
    def __init__(self, error_callback: RuntimeErrorCallback) -> None:
        self.error_callback = error_callback
        self.globals = Environment()
        self.environment = self.globals
        self.locals: dict[Expr, int] = {}

        self._add_builtin_globals()

    def _add_builtin_globals(self) -> None:
        class Clock(LoxCallable):
            @property
            def arity(self) -> int:
                return 0

            def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
                return time.time()

            def __str__(self) -> str:
                return "<native fn>"

        self.globals.define("clock", Clock())

    def interpret(self, stmts: list[Stmt]) -> None:
        try:
            for stmt in stmts:
                self.execute(stmt)
        except LoxRuntimeError as e:
            self.error_callback(e)
        except Exception as e:
            raise PyloxImpossibleCaseError() from e

    def execute(self, stmt: Stmt) -> object:
        return stmt.accept(self)

    def evaluate(self, expr: Expr) -> object:
        return expr.accept(self)

    def resolve(self, expr: Expr, depth: int) -> None:
        self.locals[expr] = depth

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

    def executeBlock(self, block: BlockStmt, environment: Environment) -> None:
        previousEnvironment = self.environment
        try:
            self.environment = environment
            for stmt in block.stmts:
                self.execute(stmt)
        finally:
            self.environment = previousEnvironment

    def lookup_variable(self, name: Token, expr: Expr) -> object:
        distance = self.locals.get(expr, None)
        if distance is None:
            return self.globals.get(name)
        else:
            return self.environment.get_at(distance, name.lexeme)

    @singledispatchmethod
    def visit(self, invalidArg: Any) -> object:  # pyright: ignore[reportIncompatibleMethodOverride]
        raise NotImplementedError(
            f"The `visit` dispatcher for {type(invalidArg)} objects is not defined"
        )

    @visit.register
    def _(self, stmt: ExpressionStmt) -> object:
        self.evaluate(stmt.expr)
        return None

    @visit.register
    def _(self, stmt: PrintStmt) -> object:
        value = self.evaluate(stmt.expr)
        print(self.stringify(value))
        return None

    @visit.register
    def _(self, stmt: VarStmt) -> None:
        value: object = None
        if stmt.initializer is not None:
            value = self.evaluate(stmt.initializer)
        self.environment.define(stmt.name.lexeme, value)

    @visit.register
    def _(self, stmt: WhileStmt) -> None:
        while self.is_truthy(self.evaluate(stmt.condition)):
            self.execute(stmt.body)

    @visit.register
    def _(self, stmt: ReturnStmt) -> None:
        returnValue: object = None
        if isinstance(stmt.value, Expr):
            returnValue = self.evaluate(stmt.value)

        raise LoxReturn(returnValue)

    @visit.register
    def _(self, stmt: BlockStmt) -> None:
        self.executeBlock(stmt, Environment(self.environment))

    @visit.register
    def _(self, stmt: IfStmt) -> None:
        if self.is_truthy(self.evaluate(stmt.condition)):
            self.execute(stmt.thenBranch)
        elif stmt.elseBranch is not None:
            self.execute(stmt.elseBranch)

    @visit.register
    def _(self, stmt: FunctionStmt) -> None:
        function = LoxFunction(stmt, self.environment)
        self.environment.define(stmt.name.lexeme, function)

    @visit.register
    def _(self, expr: GroupingExpr) -> object:
        return self.evaluate(expr.expression)

    @visit.register
    def _(self, expr: LiteralExpr) -> object:
        return expr.value

    @visit.register
    def _(self, expr: VarExpr) -> object:
        return self.lookup_variable(expr.name, expr)

    @visit.register
    def _(self, expr: AssignExpr) -> object:
        value: object = self.evaluate(expr.value)
        distance = self.locals.get(expr, None)
        if distance is None:
            return self.globals.assign(expr.name, value)
        else:
            return self.environment.assign_at(distance, expr.name, value)
        return value

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
    def _(self, expr: BinaryLogicalExpr) -> object:
        left_value: object = self.evaluate(expr.left)

        if expr.operator.type is TokenType.OR and self.is_truthy(left_value):
            return left_value
        elif expr.operator.type is TokenType.AND and not self.is_truthy(left_value):
            return left_value

        right_value: object = self.evaluate(expr.right)

        return right_value

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
                            if get_knob("divide_by_zero_error"):
                                raise LoxRuntimeError(  # noqa: B904
                                    "Division by zero is not allowed", expr.operator
                                )
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
                elif get_knob("plus_allow_string_mixed_types") and isinstance(left_value, str):
                    right_value = self.stringify(right_value)
                    return f"{left_value}{right_value}"
                elif get_knob("plus_allow_string_mixed_types") and isinstance(right_value, str):
                    left_value = self.stringify(left_value)
                    return f"{left_value}{right_value}"

                if get_knob("plus_allow_string_mixed_types"):
                    raise LoxRuntimeError(
                        "Operands must be two numbers, or at least one string", expr.operator
                    )
                else:
                    raise LoxRuntimeError(
                        "Operands must be two numbers or two strings", expr.operator
                    )

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

    @visit.register
    def _(self, expr: CallExpr) -> object:
        callee: object = self.evaluate(expr.callee)

        arguments: list[object] = [self.evaluate(argument) for argument in expr.arguments]

        if not isinstance(callee, LoxCallable):
            raise LoxRuntimeError("Can only call functions and classes.", expr.closingParen)

        if len(arguments) != callee.arity:
            raise LoxRuntimeError(
                f"Expected {callee.arity} arguments but got {len(arguments)}.", expr.closingParen
            )

        return callee.call(self, arguments)

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
