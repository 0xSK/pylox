import argparse

from pylox.scanner import Scanner
from pylox.token import Token


class PyLox:
    def __init__(self):
        self.hadError: bool = False

    def main(self) -> int:
        args = self.parse_args()
        if args.input:
            return self.run_file(args.input)
        else:
            return self.run_prompt()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("input", nargs="?", default=None, help="Input source file")
        args = parser.parse_args()
        return args

    def run_file(self, path: str) -> int:
        sourceFile = open(path)
        source = sourceFile.read()
        sourceFile.close()

        self.run(source)
        if self.hadError:
            return 65
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
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break
        return 0

    def run(self, source: str) -> None:
        scanner = Scanner(source, self.error)
        tokens: list[Token] = scanner.scan_tokens()

        for token in tokens:
            print(f"{token.line:>6d} {token.type.name:<20} : {token.lexeme}")

    def error(self, line: int, message: str) -> None:
        self.report(line, "", message)

    def report(self, line: int, where: str, message: str) -> None:
        print(f"[line {line}] Error {where}: {message}")
        self.hadError = True
