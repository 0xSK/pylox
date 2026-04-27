import argparse

from pylox.errors import LoxRuntimeError
from pylox.interpreter import Interpreter
from pylox.knobs import KnobConfigurationError, initialize_knobs, iter_knobs
from pylox.parser import Parser
from pylox.scanner import Scanner
from pylox.token import Token, TokenType


class PyLox:
    def __init__(self):
        self.hadError: bool = False
        self.hadRuntimeError: bool = False

    def main(self) -> int:
        args = self.parse_args()
        if args.list_knobs:
            self.print_knobs()
            return 0
        if args.input:
            return self.run_file(args.input)
        else:
            return self.run_prompt()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("input", nargs="?", default=None, help="Input source file")
        parser.add_argument(
            "--knobs-file",
            default=None,
            help="Path to an additional TOML knobs file. Overrides default knobs.",
        )
        parser.add_argument(
            "--list-knobs",
            action="store_true",
            help="Print knob names, types, and active values, then exit.",
        )
        args, unknown_args = parser.parse_known_args()
        try:
            initialize_knobs(knobs_file=args.knobs_file, cli_overrides=unknown_args)
        except KnobConfigurationError as e:
            parser.error(str(e))
        return args

    def run_file(self, path: str) -> int:
        sourceFile = open(path)
        source = sourceFile.read()
        sourceFile.close()

        self.run(source)
        if self.hadError:
            return 65
        if self.hadRuntimeError:
            return 70
        return 0

    def run_prompt(self) -> int:
        """Run the interactive REPL"""
        print("Type 'exit' or 'quit' to exit")
        print()

        while True:
            try:
                line = input("pylox> ")
                if line.lower() in ("exit", "quit"):
                    print("Goodbye!")
                    break
                # TODO: Implement interpreter
                self.run(line)
                self.hadError = False
                self.hadRuntimeError = False
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break
        return 0

    def run(self, source: str) -> None:
        scanner = Scanner(source, self.lineError)
        tokens: list[Token] = scanner.scan_tokens()

        parser = Parser(tokens, self.tokenError)
        expr = parser.parse()
        if expr is None or self.hadError:
            return

        interpreter = Interpreter(self.runtimeError)
        value = interpreter.interpret(expr)
        if self.hadRuntimeError:
            return
        print(interpreter.stringify(value))

    def print_knobs(self) -> None:
        for name, value_type, value in iter_knobs():
            print(f"{name} ({value_type}) = {value}")

    def lineError(self, line: int, message: str) -> None:
        self.report(line, "", message)

    def tokenError(self, token: Token, message: str) -> None:
        if token.type == TokenType.EOF:
            self.report(token.line, "at end", message)
        else:
            self.report(token.line, f"at `{token.lexeme}`", message)

    def runtimeError(self, error: LoxRuntimeError):
        print(f"{error}\n[line {error.token.line} at '{error.token.lexeme}']")
        self.hadRuntimeError = True

    def report(self, line: int, where: str, message: str) -> None:
        print(f"[line {line}] Error {where}: {message}")
        self.hadError = True
