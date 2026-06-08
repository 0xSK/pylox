from collections.abc import Callable

from pylox.exceptions import LoxParserError, TokenErrorCallback
from pylox.expression import (
    AssignExpr,
    BinaryExpr,
    BinaryLogicalExpr,
    CallExpr,
    Expr,
    GroupingExpr,
    LiteralExpr,
    UnaryExpr,
    VarExpr,
)
from pylox.statement import (
    BlockStmt,
    ClassStmt,
    ExpressionStmt,
    FunctionStmt,
    IfStmt,
    PrintStmt,
    ReturnStmt,
    Stmt,
    VarStmt,
    WhileStmt,
)
from pylox.token import Token, TokenType


class Parser:
    def __init__(self, tokens: list[Token], error_callback: TokenErrorCallback) -> None:
        self.tokens: list[Token] = tokens
        self.current: int = 0
        self.error_callback = error_callback

    def parse(self) -> list[Stmt]:
        stmts: list[Stmt] = []
        while not self.is_at_end():
            stmt = self.parse_declaration()
            if stmt is not None:
                stmts.append(stmt)
        return stmts

    def parse_declaration(self) -> Stmt | None:
        try:
            if self.match(TokenType.CLASS):
                return self.parse_class_declaration()
            elif self.match(TokenType.FUN):
                return self.parse_function_declaration("function")
            elif self.match(TokenType.VAR):
                return self.parse_var_declaration()
            else:
                return self.parse_statement()
        except LoxParserError:
            self.synchronize()
            return None

    def parse_class_declaration(self) -> ClassStmt:
        name = self.consume(TokenType.IDENTIFIER, "Expect class name.")
        self.consume(TokenType.LEFT_BRACE, "Expect '{' before class body.")

        methods: list[FunctionStmt] = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            methods.append(self.parse_function_declaration("method"))

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after class body.")

        return ClassStmt(name, methods)

    def parse_function_declaration(self, kind: str) -> FunctionStmt:
        name = self.consume(TokenType.IDENTIFIER, f"Expect {kind} name.")

        params: list[Token] = []
        self.consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                if len(params) >= 255:
                    self.error(self.peek(), "Can't have more than 255 parameters.")
                params.append(self.consume(TokenType.IDENTIFIER, "Expect parameter name."))

                if not self.match(TokenType.COMMA):
                    break
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")

        self.consume(TokenType.LEFT_BRACE, f"Expect '{{' before {kind} body.")
        body = self.parse_block_statement()

        return FunctionStmt(name, params, body)

    def parse_statement(self) -> Stmt:
        if self.match(TokenType.IF):
            stmt = self.parse_if_statement()
        elif self.match(TokenType.PRINT):
            stmt = self.parse_print_statement()
        elif self.match(TokenType.RETURN):
            stmt = self.parse_return_statement()
        elif self.match(TokenType.WHILE):
            stmt = self.parse_while_statement()
        elif self.match(TokenType.FOR):
            stmt = self.parse_for_statement()
        elif self.match(TokenType.LEFT_BRACE):
            stmt = self.parse_block_statement()
        else:
            stmt = self.parse_expression_statement()
        return stmt

    def parse_if_statement(self) -> Stmt:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition: Expr = self.parse_expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")
        thenBranch: Stmt = self.parse_statement()

        elseBranch: Stmt | None = None
        if self.match(TokenType.ELSE):
            elseBranch = self.parse_statement()

        return IfStmt(condition, thenBranch, elseBranch)

    def parse_var_declaration(self) -> Stmt:
        name: Token = self.consume(TokenType.IDENTIFIER, "Expect variable name.")

        initializer: Expr | None = None
        if self.match(TokenType.EQUAL):
            initializer = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")

        return VarStmt(name, initializer)

    def parse_block_statement(self) -> BlockStmt:
        stmts: list[Stmt] = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            stmt = self.parse_declaration()
            if stmt is not None:
                stmts.append(stmt)

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return BlockStmt(stmts)

    def parse_print_statement(self) -> Stmt:
        expr: Expr = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return PrintStmt(expr)

    def parse_while_statement(self) -> Stmt:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition: Expr = self.parse_expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after condition.")
        body: Stmt = self.parse_statement()
        return WhileStmt(condition, body)

    def parse_return_statement(self) -> Stmt:
        keyword = self.previous()
        value = None

        if not self.check(TokenType.SEMICOLON):
            value = self.parse_expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after return value.")

        return ReturnStmt(keyword, value)

    def parse_for_statement(self) -> Stmt:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        initializer: Stmt | None
        if self.match(TokenType.SEMICOLON):
            initializer = None
        elif self.match(TokenType.VAR):
            initializer = self.parse_var_declaration()
        else:
            initializer = self.parse_expression_statement()

        condition: Expr | None = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        increment: Expr | None = None
        if not self.check(TokenType.RIGHT_PAREN):
            increment = self.parse_expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")

        body: Stmt = self.parse_statement()

        if increment is not None:
            body = BlockStmt([body, ExpressionStmt(increment)])
        if condition is None:
            condition = LiteralExpr(True)

        stmt = WhileStmt(condition, body)

        if initializer is not None:
            stmt = BlockStmt([initializer, stmt])

        return stmt

    def parse_expression_statement(self) -> Stmt:
        expr: Expr = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return ExpressionStmt(expr)

    def parse_expression(self) -> Expr:
        return self.parse_assignment()

    def parse_assignment(self) -> Expr:
        expr = self.parse_or()

        if self.match(TokenType.EQUAL):
            equals: Token = self.previous()
            value: Expr = self.parse_assignment()

            if isinstance(expr, VarExpr):
                return AssignExpr(expr.name, value)

            else:
                self.error(equals, "Invalid assignment target.")

        return expr

    def parse_or(self) -> Expr:
        return self.parse_binary(
            self.parse_and,
            TokenType.OR,
            expressionType=BinaryLogicalExpr,
        )

    def parse_and(self) -> Expr:
        return self.parse_binary(
            self.parse_equality,
            TokenType.AND,
            expressionType=BinaryLogicalExpr,
        )

    def parse_equality(self) -> Expr:
        return self.parse_binary(self.parse_comparison, TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL)

    def parse_comparison(self) -> Expr:
        return self.parse_binary(
            self.parse_term,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        )

    def parse_term(self) -> Expr:
        return self.parse_binary(self.parse_factor, TokenType.PLUS, TokenType.MINUS)

    def parse_factor(self) -> Expr:
        return self.parse_binary(self.parse_unary, TokenType.SLASH, TokenType.STAR)

    def parse_binary(
        self,
        next_rule: Callable[[], Expr],
        *operators: TokenType,
        expressionType: type[BinaryExpr] = BinaryExpr,
    ) -> Expr:
        expr: Expr = next_rule()
        while self.match(*operators):
            operator: Token = self.previous()
            right_expr: Expr = next_rule()
            expr = expressionType(expr, operator, right_expr)
        return expr

    def parse_unary(self) -> Expr:
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator: Token = self.previous()
            right_expr: Expr = self.parse_unary()
            expr = UnaryExpr(operator, right_expr)
        else:
            expr = self.parse_call()

        return expr

    def parse_call(self) -> Expr:
        expr = self.parse_primary()

        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self.finish_parsing_call(expr)
            else:
                break

        return expr

    def finish_parsing_call(self, callee: Expr) -> Expr:
        arguments: list[Expr] = []
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                if len(arguments) >= 255:
                    self.error(self.peek(), "Can't have more than 255 arguments.")
                arguments.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break

        closingParen: Token = self.consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")

        return CallExpr(callee, closingParen, arguments)

    def parse_primary(self) -> Expr:
        if self.match(TokenType.FALSE):
            expr = LiteralExpr(False)
        elif self.match(TokenType.TRUE):
            expr = LiteralExpr(True)
        elif self.match(TokenType.NIL):
            expr = LiteralExpr(None)
        elif self.match(TokenType.IDENTIFIER):
            expr = VarExpr(self.previous())
        elif self.match(TokenType.NUMBER, TokenType.STRING):
            expr = LiteralExpr(value=self.previous().literal)
        elif self.match(TokenType.LEFT_PAREN):
            innerExpr: Expr = self.parse_expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            expr = GroupingExpr(innerExpr)
        else:
            raise self.error(self.peek(), "Expect expression.")

        return expr

    def consume(self, tokenType: TokenType, message: str) -> Token:
        if self.check(tokenType):
            return self.advance()

        raise self.error(self.peek(), message)

    def error(self, token: Token, message: str) -> LoxParserError:
        self.error_callback(token, message)
        return LoxParserError()

    def synchronize(self) -> None:
        self.advance()

        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return
            elif self.peek().type in {
                TokenType.CLASS,
                TokenType.FUN,
                TokenType.VAR,
                TokenType.FOR,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.PRINT,
                TokenType.RETURN,
            }:
                return

            self.advance()

    def match(self, *tokenTypes: TokenType) -> bool:
        for tokenType in tokenTypes:
            if self.check(tokenType):
                self.advance()
                return True

        return False

    def check(self, tokenType: TokenType) -> bool:
        if self.is_at_end():
            return False
        return self.peek().type == tokenType

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]
