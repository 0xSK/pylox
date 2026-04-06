# pylox

An interpreter for the Lox programming language, written in Python.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

## Quick start

```bash
uv sync
uv run pylox
```

## Development

```bash
uv run ruff check .
uv run ruff format .
uv run pre-commit install
```

Source code lives under `src/pylox`.
