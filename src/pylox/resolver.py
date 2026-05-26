from collections import deque
from enum import Enum, auto
from functools import singledispatchmethod
from typing import Any

from pylox.exceptions import (
    TokenErrorCallback,
)
from pylox.expression import (
    AssignExpr,
    BinaryExpr,
    CallExpr,
    Expr,
    ExprVisitor,
    GroupingExpr,
    LiteralExpr,
    UnaryExpr,
    VarExpr,
)
from pylox.interpreter import Interpreter
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
from pylox.token import Token


class FunctionType(Enum):
    NONE = auto()
    FUNCTION = auto()


class Scope(dict[str, bool]):
    pass


class Resolver(ExprVisitor[None], StmtVisitor[None]):
    def __init__(self, interpreter: Interpreter, error_callback: TokenErrorCallback) -> None:
        self.interpreter = interpreter
        self.error_callback = error_callback
        self.scopes: deque[Scope] = deque()
        self.currentFunctionType = FunctionType.NONE

    def resolve(self, stmts: list[Stmt]) -> None:
        for stmt in stmts:
            self.resolve_stmt(stmt)

    def resolve_stmt(self, stmt: Stmt) -> None:
        stmt.accept(self)

    def resolve_expr(self, expr: Expr) -> None:
        expr.accept(self)

    def begin_scope(self) -> None:
        self.scopes.append(Scope())

    def end_scope(self) -> None:
        self.scopes.pop()

    @property
    def peek_scope(self) -> Scope:
        return self.scopes[-1]

    def declare(self, name: Token) -> None:
        if not self.scopes:
            return
        if name.lexeme in self.peek_scope:
            self.error_callback(name, f"Scope already has var '{name.lexeme}' declared")

        self.peek_scope[name.lexeme] = False

    def define(self, name: Token) -> None:
        if not self.scopes:
            return
        self.peek_scope[name.lexeme] = True

    def resolve_local(self, expr: Expr, name: Token) -> None:
        for revIdx, scope in enumerate(reversed(self.scopes)):
            if name.lexeme in scope:
                self.interpreter.resolve(expr, revIdx)
                return

    def resolve_function(self, stmt: FunctionStmt, functionType: FunctionType) -> None:
        enclosingFunctionType = self.currentFunctionType
        self.currentFunctionType = functionType

        self.begin_scope()
        for param in stmt.params:
            self.declare(param)
            self.define(param)
        self.resolve_stmt(stmt.body)
        self.end_scope()

        self.currentFunctionType = enclosingFunctionType

    @singledispatchmethod
    def visit(self, invalidArg: Any) -> object:  # pyright: ignore[reportIncompatibleMethodOverride]
        raise NotImplementedError(
            f"The `visit` dispatcher for {type(invalidArg)} objects is not defined"
        )

    @visit.register
    def _(self, stmt: BlockStmt) -> None:
        self.begin_scope()
        self.resolve(stmt.stmts)
        self.end_scope()

    @visit.register
    def _(self, stmt: VarStmt) -> None:
        self.declare(stmt.name)
        if stmt.initializer is not None:
            self.resolve_expr(stmt.initializer)
        self.define(stmt.name)

    @visit.register
    def _(self, stmt: FunctionStmt) -> None:
        self.declare(stmt.name)
        self.define(stmt.name)
        self.resolve_function(stmt, FunctionType.FUNCTION)

    @visit.register
    def _(self, stmt: ExpressionStmt) -> None:
        self.resolve_expr(stmt.expr)

    @visit.register
    def _(self, stmt: PrintStmt) -> None:
        self.resolve_expr(stmt.expr)

    @visit.register
    def _(self, stmt: ReturnStmt) -> None:
        if self.currentFunctionType is FunctionType.NONE:
            self.error_callback(stmt.keyword, "Can't return from top-level code.")
        if stmt.value is not None:
            self.resolve_expr(stmt.value)

    @visit.register
    def _(self, stmt: IfStmt) -> None:
        self.resolve_expr(stmt.condition)
        self.resolve_stmt(stmt.thenBranch)
        if stmt.elseBranch is not None:
            self.resolve_stmt(stmt.elseBranch)

    @visit.register
    def _(self, stmt: WhileStmt) -> None:
        self.resolve_expr(stmt.condition)
        self.resolve_stmt(stmt.body)

    @visit.register
    def _(self, expr: VarExpr) -> None:
        if self.scopes and self.peek_scope.get(expr.name.lexeme) is False:
            self.error_callback(expr.name, "Can't read local variable in its own initializer.")

        self.resolve_local(expr, expr.name)

    @visit.register
    def _(self, expr: AssignExpr) -> None:
        self.resolve_expr(expr.value)
        self.resolve_local(expr, expr.name)

    @visit.register
    def _(self, expr: UnaryExpr) -> None:
        self.resolve_expr(expr.right)

    @visit.register
    def _(self, expr: GroupingExpr) -> None:
        self.resolve_expr(expr.expression)

    @visit.register
    def _(self, expr: BinaryExpr) -> None:
        self.resolve_expr(expr.left)
        self.resolve_expr(expr.right)

    @visit.register
    def _(self, expr: CallExpr) -> None:
        self.resolve_expr(expr.callee)
        for argument in expr.arguments:
            self.resolve_expr(argument)

    @visit.register
    def _(self, expr: LiteralExpr) -> None:
        return None
