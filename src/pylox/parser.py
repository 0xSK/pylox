from pylox.errors import ParserError
from pylox.expression import BinaryExpr, Expr, GroupingExpr, LiteralExpr, UnaryExpr
from pylox.token import Token, TokenType


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens: list[Token] = tokens
        self.current: int = 0

    def parse_expression(self) -> Expr:
        expr: Expr = self.parse_equality()
        return expr

    def parse_equality(self) -> Expr:
        expr: Expr = self.parse_comparison()

        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator: Token = self.previous()
            rightExpr: Expr = self.parse_comparison()
            expr: Expr = BinaryExpr(expr, operator, rightExpr)

        return expr

    def parse_comparison(self) -> Expr:
        expr: Expr = self.parse_term()

        while self.match(
            TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL
        ):
            operator: Token = self.previous()
            rightExpr: Expr = self.parse_term()
            expr: Expr = BinaryExpr(expr, operator, rightExpr)

        return expr

    def parse_term(self) -> Expr:
        expr: Expr = self.parse_factor()

        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator: Token = self.previous()
            rightExpr: Expr = self.parse_factor()
            expr: Expr = BinaryExpr(expr, operator, rightExpr)

        return expr

    def parse_factor(self) -> Expr:
        expr: Expr = self.parse_unary()

        while self.match(TokenType.SLASH, TokenType.STAR):
            operator: Token = self.previous()
            rightExpr: Expr = self.parse_unary()
            expr: Expr = BinaryExpr(expr, operator, rightExpr)

        return expr

    def parse_unary(self) -> Expr:
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator: Token = self.previous()
            rightExpr: Expr = self.parse_unary()
            expr = UnaryExpr(operator, rightExpr)
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
            raise ParserError()
            # TODO

        return expr
        # TODO

    def consume(self, tokenType: TokenType, message: str) -> Token:
        if self.check(tokenType):
            return self.advance()
        # TODO

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
