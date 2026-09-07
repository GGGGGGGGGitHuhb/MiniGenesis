"""Strict loading and normalization of S1 experiment configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


MAX_TICKS = 100_000


class ConfigError(ValueError):
    """A user-facing configuration error."""


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: _UniqueKeySafeLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise ConfigError(
                f"invalid unhashable mapping key at line {key_node.start_mark.line + 1}"
            ) from exc
        if duplicate:
            raise ConfigError(
                f"duplicate mapping key {key!r} at line {key_node.start_mark.line + 1}"
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    """Normalized immutable input for one isolated experiment run."""

    name: str
    seed: int
    max_ticks: int


def _require_exact_keys(
    value: dict[Any, Any], expected: set[str], path: str
) -> None:
    keys = set(value)
    missing = sorted(expected - keys)
    unknown = sorted(keys - expected, key=repr)
    if missing:
        raise ConfigError(f"{path}: missing required field(s): {', '.join(missing)}")
    if unknown:
        rendered = ", ".join(repr(item) for item in unknown)
        raise ConfigError(f"{path}: unknown field(s): {rendered}")


def _normalize(document: Any) -> ExperimentConfig:
    if not isinstance(document, dict):
        raise ConfigError("configuration root: expected a mapping")
    _require_exact_keys(document, {"experiment"}, "configuration root")

    experiment = document["experiment"]
    if not isinstance(experiment, dict):
        raise ConfigError("experiment: expected a mapping")
    _require_exact_keys(experiment, {"name", "seed", "max_ticks"}, "experiment")

    name = experiment["name"]
    if not isinstance(name, str):
        raise ConfigError("experiment.name: expected a string")
    name = name.strip()
    if not name:
        raise ConfigError("experiment.name: must not be empty")

    seed = experiment["seed"]
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ConfigError("experiment.seed: expected a non-negative integer")
    if seed < 0:
        raise ConfigError("experiment.seed: must be non-negative")

    max_ticks = experiment["max_ticks"]
    if isinstance(max_ticks, bool) or not isinstance(max_ticks, int):
        raise ConfigError(
            f"experiment.max_ticks: expected an integer in 1..{MAX_TICKS}"
        )
    if not 1 <= max_ticks <= MAX_TICKS:
        raise ConfigError(f"experiment.max_ticks: must be in 1..{MAX_TICKS}")

    return ExperimentConfig(name=name, seed=seed, max_ticks=max_ticks)


def load_config(path: str | Path) -> ExperimentConfig:
    """Load a UTF-8 YAML file as a strict, normalized configuration."""

    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigError(f"config file is not a readable regular file: {config_path}")
    try:
        text = config_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ConfigError(f"cannot read config file {config_path}: {exc}") from exc

    try:
        document = yaml.load(text, Loader=_UniqueKeySafeLoader)
    except ConfigError:
        raise
    except yaml.YAMLError as exc:
        location = ""
        mark = getattr(exc, "problem_mark", None)
        if mark is not None:
            location = f" at line {mark.line + 1}, column {mark.column + 1}"
        raise ConfigError(f"invalid YAML{location}: {exc}") from exc

    return _normalize(document)

