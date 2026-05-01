from collections.abc import Callable

from pylox.errors import LoxParserError, TokenErrorCallback
from pylox.expression import BinaryExpr, Expr, GroupingExpr, LiteralExpr, UnaryExpr
from pylox.statement import ExpressionStmt, PrintStmt, Stmt
from pylox.token import Token, TokenType


class Parser:
    def __init__(self, tokens: list[Token], error_callback: TokenErrorCallback) -> None:
        self.tokens: list[Token] = tokens
        self.current: int = 0
        self.error_callback = error_callback

    def parse(self) -> list[Stmt]:
        stmts: list[Stmt] = []
        while not self.is_at_end():
            stmt = self.parse_statement()
            stmts.append(stmt)
        return stmts

    def parse_statement(self) -> Stmt:
        if self.match(TokenType.PRINT):
            stmt = self.parse_print_statement()
        else:
            stmt = self.parse_expression_statement()
        return stmt

    def parse_print_statement(self) -> Stmt:
        expr: Expr = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return PrintStmt(expr)

    def parse_expression_statement(self) -> Stmt:
        expr: Expr = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return ExpressionStmt(expr)

    def parse_expression(self) -> Expr:
        return self.parse_equality()

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

    def parse_binary(self, next_rule: Callable[[], Expr], *operators: TokenType) -> Expr:
        expr: Expr = next_rule()
        while self.match(*operators):
            operator: Token = self.previous()
            right_expr: Expr = next_rule()
            expr = BinaryExpr(expr, operator, right_expr)
        return expr

    def parse_unary(self) -> Expr:
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator: Token = self.previous()
            right_expr: Expr = self.parse_unary()
            expr = UnaryExpr(operator, right_expr)
        else:
            expr = self.parse_primary()

        return expr

    def parse_primary(self) -> Expr:
        if self.match(TokenType.FALSE):
            expr = LiteralExpr(False)
        elif self.match(TokenType.TRUE):
            expr = LiteralExpr(True)
        elif self.match(TokenType.NIL):
            expr = LiteralExpr(None)
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
