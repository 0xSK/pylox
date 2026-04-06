from __future__ import annotations

from typing import Any

from pylox.errors import LineErrorCallback
from pylox.token import Token, TokenType


class Scanner:
    def __init__(self, source: str, error_callback: LineErrorCallback) -> None:
        self.source = source
        self.error_callback = error_callback
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

    def scan_token(self) -> None:
        c = self.advance()
        match c:
            case "(":
                self.add_token(TokenType.LEFT_PAREN)
            case ")":
                self.add_token(TokenType.RIGHT_PAREN)
            case "{":
                self.add_token(TokenType.LEFT_BRACE)
            case "}":
                self.add_token(TokenType.RIGHT_BRACE)
            case ",":
                self.add_token(TokenType.COMMA)
            case ".":
                self.add_token(TokenType.DOT)
            case "-":
                self.add_token(TokenType.MINUS)
            case "+":
                self.add_token(TokenType.PLUS)
            case ";":
                self.add_token(TokenType.SEMICOLON)
            case "*":
                self.add_token(TokenType.STAR)
            case "!":
                self.add_token(TokenType.BANG_EQUAL if self.match("=") else TokenType.BANG)
            case "=":
                self.add_token(TokenType.EQUAL_EQUAL if self.match("=") else TokenType.EQUAL)
            case "<":
                self.add_token(TokenType.LESS_EQUAL if self.match("=") else TokenType.LESS)
            case ">":
                self.add_token(TokenType.GREATER_EQUAL if self.match("=") else TokenType.GREATER)
            case "/":
                if self.match("/"):
                    # this is a comment
                    # consume everything until the EOL or EOF
                    while self.peek() != "\n" and not self.is_at_end():
                        self.advance()
                else:
                    self.add_token(TokenType.SLASH)
            case " " | "\r" | "\t":
                pass  # ignore whitespace
            case "\n":
                self.line += 1
            case '"':
                self.parse_string()
            case _:
                if self.character_is_digit(c):
                    self.parse_number()
                elif self.character_is_alpha(c):
                    self.parse_identifier()
                else:
                    self.error_callback(self.line, f"Unexpected character: {c}")

    def parse_identifier(self) -> None:
        while self.character_is_alphanumeric(self.peek()):
            self.advance()

        identifierName: str = self.source[self.start : self.current]

        if identifierName in _RESERVED_KEYWORDS:
            tokenType = TokenType[identifierName.upper()]
        else:
            tokenType = TokenType.IDENTIFIER

        self.add_token(tokenType)

    def parse_number(self) -> None:
        while self.character_is_digit(self.peek()):
            self.advance()

        # look for the decimal part
        if self.peek() == "." and self.character_is_digit(self.peek_next()):
            # consume the '.'
            self.advance()

            while self.character_is_digit(self.peek()):
                self.advance()

        number_string = self.source[self.start : self.current]
        number_literal = float(number_string)
        self.add_token(TokenType.NUMBER, number_literal)

    def parse_string(self) -> None:
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == "\n":
                self.line += 1
            self.advance()

        if self.is_at_end():
            self.error_callback(self.line, "Unterminated string.")
            return

        # if we made it so far, then the string must have been gracefully terminated

        # consume the closing "
        self.advance()

        literal_value = self.source[self.start + 1 : self.current]
        self.add_token(TokenType.STRING, literal_value)

    def character_is_digit(self, character: str) -> bool:
        return "0" <= character <= "9"

    def character_is_alpha(self, char: str) -> bool:
        return ("a" <= char <= "z") or ("A" <= char <= "Z") or char == "_"

    def character_is_alphanumeric(self, char: str) -> bool:
        return self.character_is_alpha(char) or self.character_is_digit(char)

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def match(self, character: str) -> bool:
        if self.peek() == character:
            self.advance()
            return True
        else:
            return False

    def advance(self) -> str:
        """
        returns the character at the `current` index,
        and increments the `current` index
        """
        curr_char = self.source[self.current]
        self.current += 1
        return curr_char

    def peek(self) -> str:
        if self.is_at_end():
            return "\0"
        return self.source[self.current]

    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def add_token(self, tokenType: TokenType, literal: Any = None) -> None:
        lexeme = self.source[self.start : self.current]
        self.tokens.append(Token(type=tokenType, lexeme=lexeme, literal=literal, line=self.line))

    def report_error(self, line: int, message: str) -> None:
        self.error_callback(line, message)


_RESERVED_KEYWORDS: set[str] = {
    "and",
    "class",
    "else",
    "false",
    "for",
    "fun",
    "if",
    "nil",
    "or",
    "print",
    "return",
    "super",
    "this",
    "true",
    "var",
    "while",
}
