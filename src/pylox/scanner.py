from typing import Any

from pylox.token import Token, TokenType


class Scanner:
    def __init__(self, source: str) -> None:
        self.source = source
        self.tokens: list[Token] = []
        self.start: int = 0
        self.current: int = 0
        self.line: int = 1

    def scan_tokens(self) -> list[Token]:
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def advance(self) -> str:
        """
        returns the character at the `current` index,
        and increments the `current` index
        """
        curr_char = self.source[self.current]
        self.current += 1
        return curr_char

    def add_token_simple(self, tokenType: TokenType) -> None:
        self.add_token_literal(tokenType=tokenType, literal=None)

    def add_token_literal(self, tokenType: TokenType, literal: Any) -> None:
        lexeme = self.source[self.start : self.current]
        self.tokens.append(Token(type=tokenType, lexeme=lexeme, literal=literal, line=self.line))
