from pylox.pylox import PyLox


def main() -> int:
    """Run the Pylox CLI."""
    PyLox().main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
