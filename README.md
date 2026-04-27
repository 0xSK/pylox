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

## Knobs

Knobs are declared in TOML and loaded through Dynaconf:

- `config/knobs.toml` is always loaded.
- You can pass an additional file with `--knobs-file path/to/knobs.toml`.
- The TOML files define what knobs are available.
- CLI overrides have highest precedence:
  - `--plus_allow_string_mixed_types`
  - `--divide_by_zero_error`
  - `--no-divide_by_zero_error`

To inspect active knob values:

```bash
uv run pylox --list-knobs
```

## Development

```bash
uv run ruff check .
uv run ruff format .
uv run pre-commit install
```

Source code lives under `src/pylox`.
