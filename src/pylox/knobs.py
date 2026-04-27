from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Literal, overload

from dynaconf import Dynaconf

type KnobValue = bool | int | float | str
type KnobType = type[bool] | type[int] | type[float] | type[str]

_DEFAULT_KNOBS_PATH = Path(__file__).resolve().parents[2] / "config" / "knobs.toml"
_BOOL_TRUE = frozenset({"true", "1", "yes", "on"})
_BOOL_FALSE = frozenset({"false", "0", "no", "off"})

_active_values: dict[str, KnobValue] | None = None
_known_types: dict[str, KnobType] | None = None


class KnobConfigurationError(ValueError):
    pass


def initialize_knobs(knobs_file: str | None, cli_overrides: list[str]) -> dict[str, KnobValue]:
    default_values = _read_knob_file(_DEFAULT_KNOBS_PATH, context="default knobs file")
    types = {key: _type_for_value(value) for key, value in default_values.items()}

    settings_files: list[str] = [str(_DEFAULT_KNOBS_PATH)]
    if knobs_file is not None:
        user_path = Path(knobs_file).expanduser().resolve()
        if user_path.suffix.lower() != ".toml":
            raise KnobConfigurationError(f"Knobs file must be TOML: `{user_path}`")
        user_values = _read_knob_file(user_path, context="user knobs file")
        _validate_known_keys(user_values, known_keys=set(default_values), source=user_path)
        settings_files.append(str(user_path))

    settings = Dynaconf(
        settings_files=settings_files,
        environments=False,
        load_dotenv=False,
    )
    values: dict[str, KnobValue] = {}
    for key, value_type in types.items():
        raw = settings.get(key, default_values[key])
        values[key] = _coerce(raw, value_type, key)

    cli_values = _parse_cli_overrides(cli_overrides, types)
    values.update(cli_values)

    global _active_values
    global _known_types
    _active_values = values
    _known_types = types
    return values


@overload
def get_knob(name: str, *, missing_ok: Literal[False] = False) -> KnobValue: ...


@overload
def get_knob(name: str, *, missing_ok: Literal[True]) -> KnobValue | None: ...


def get_knob(name: str, *, missing_ok: bool = False) -> KnobValue | None:
    values = _get_active_values()
    if name not in values:
        if missing_ok:
            return None
        available = ", ".join(sorted(values))
        raise KnobConfigurationError(f"Unknown knob `{name}`. Available knobs: {available}")
    return values[name]


def iter_knobs() -> list[tuple[str, str, KnobValue]]:
    values = _get_active_values()
    types = _get_known_types()
    return [(name, types[name].__name__, values[name]) for name in sorted(values)]


def _get_active_values() -> dict[str, KnobValue]:
    global _active_values
    if _active_values is None:
        _active_values = initialize_knobs(knobs_file=None, cli_overrides=[])
    return _active_values


def _get_known_types() -> dict[str, KnobType]:
    global _known_types
    if _known_types is None:
        initialize_knobs(knobs_file=None, cli_overrides=[])
    if _known_types is None:
        raise KnobConfigurationError("Failed to initialize knobs")
    return _known_types


def _parse_cli_overrides(args: list[str], types: dict[str, KnobType]) -> dict[str, KnobValue]:
    overrides: dict[str, KnobValue] = {}
    for arg in args:
        if not arg.startswith("--"):
            raise KnobConfigurationError(f"Unsupported argument `{arg}`")

        token = arg[2:]
        if not token:
            raise KnobConfigurationError(f"Invalid knob override `{arg}`")

        if "=" in token:
            key, raw_value = token.split("=", 1)
            value_type = _type_for_key(key, types)
            overrides[key] = _parse_typed_value(raw_value, value_type, key)
            continue

        if token.startswith("no-"):
            key = token[3:]
            value_type = _type_for_key(key, types)
            if value_type is not bool:
                raise KnobConfigurationError(f"`--no-{key}` is only valid for boolean knobs")
            overrides[key] = False
            continue

        key = token
        value_type = _type_for_key(key, types)
        if value_type is not bool:
            raise KnobConfigurationError(f"`--{key}` needs a value, use `--{key}=...`")
        overrides[key] = True

    return overrides


def _type_for_key(key: str, types: dict[str, KnobType]) -> KnobType:
    value_type = types.get(key)
    if value_type is None:
        available = ", ".join(sorted(types))
        raise KnobConfigurationError(f"Unknown knob `{key}`. Available knobs: {available}")
    return value_type


def _parse_typed_value(raw: str, value_type: KnobType, key: str) -> KnobValue:
    if value_type is str:
        return raw
    if value_type is bool:
        lower = raw.strip().lower()
        if lower in _BOOL_TRUE:
            return True
        if lower in _BOOL_FALSE:
            return False
        raise KnobConfigurationError(f"Invalid boolean value for `{key}`: `{raw}`")
    if value_type is int:
        try:
            return int(raw)
        except ValueError as e:
            raise KnobConfigurationError(f"Invalid integer value for `{key}`: `{raw}`") from e
    if value_type is float:
        try:
            return float(raw)
        except ValueError as e:
            raise KnobConfigurationError(f"Invalid float value for `{key}`: `{raw}`") from e
    raise KnobConfigurationError(f"Unsupported knob type for `{key}`")


def _coerce(raw: Any, value_type: KnobType, key: str) -> KnobValue:
    if value_type is bool:
        if isinstance(raw, bool):
            return raw
        raise KnobConfigurationError(f"Knob `{key}` must be a boolean")
    if value_type is int:
        if isinstance(raw, int) and not isinstance(raw, bool):
            return raw
        raise KnobConfigurationError(f"Knob `{key}` must be an integer")
    if value_type is float:
        if isinstance(raw, int | float) and not isinstance(raw, bool):
            return float(raw)
        raise KnobConfigurationError(f"Knob `{key}` must be a float")
    if value_type is str:
        if isinstance(raw, str):
            return raw
        raise KnobConfigurationError(f"Knob `{key}` must be a string")
    raise KnobConfigurationError(f"Unsupported type for `{key}`")


def _type_for_value(value: Any) -> KnobType:
    if isinstance(value, bool):
        return bool
    if isinstance(value, int):
        return int
    if isinstance(value, float):
        return float
    if isinstance(value, str):
        return str
    raise KnobConfigurationError(
        f"Knob defaults must be bool/int/float/str, found `{type(value).__name__}`"
    )


def _validate_known_keys(raw: dict[str, Any], known_keys: set[str], source: Path) -> None:
    unknown = sorted(set(raw) - known_keys)
    if unknown:
        known = ", ".join(sorted(known_keys))
        values = ", ".join(unknown)
        raise KnobConfigurationError(
            f"Unknown knob(s) in `{source}`: {values}. Allowed knobs: {known}"
        )


def _read_knob_file(path: Path, context: str) -> dict[str, Any]:
    if not path.exists():
        raise KnobConfigurationError(f"Missing {context}: `{path}`")
    if not path.is_file():
        raise KnobConfigurationError(f"Expected {context} to be a file: `{path}`")
    with path.open("rb") as f:
        data = tomllib.load(f)
    if not isinstance(data, dict):
        raise KnobConfigurationError(f"Expected top-level TOML table in `{path}`")
    return data
