from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from minigenesis.config import ConfigError, ExperimentConfig, MAX_TICKS, load_config


def write_config(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "experiment.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def test_loads_and_normalizes_minimal_config(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        "experiment:\n  name: '  baseline 中文  '\n  seed: 0\n  max_ticks: 1\n",
    )
    config = load_config(path)
    assert config == ExperimentConfig(name="baseline 中文", seed=0, max_ticks=1)
    with pytest.raises(FrozenInstanceError):
        config.name = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("{}\n", "missing required"),
        ("[]\n", "root: expected a mapping"),
        ("experiment: null\n", "experiment: expected a mapping"),
        (
            "experiment:\n  name: ok\n  seed: 1\n",
            "missing required field",
        ),
        (
            "experiment:\n  name: ok\n  seed: 1\n  max_ticks: 2\n  extra: 3\n",
            "unknown field",
        ),
        (
            "experiment:\n  name: ok\n  seed: 1\n  max_ticks: 2\nother: 3\n",
            "unknown field",
        ),
        (
            "experiment:\n  name: 7\n  seed: 1\n  max_ticks: 2\n",
            "experiment.name",
        ),
        (
            "experiment:\n  name: '   '\n  seed: 1\n  max_ticks: 2\n",
            "experiment.name",
        ),
        (
            "experiment:\n  name: ok\n  seed: true\n  max_ticks: 2\n",
            "experiment.seed",
        ),
        (
            "experiment:\n  name: ok\n  seed: -1\n  max_ticks: 2\n",
            "experiment.seed",
        ),
        (
            "experiment:\n  name: ok\n  seed: 1.5\n  max_ticks: 2\n",
            "experiment.seed",
        ),
        (
            "experiment:\n  name: ok\n  seed: 1\n  max_ticks: false\n",
            "experiment.max_ticks",
        ),
        (
            "experiment:\n  name: ok\n  seed: 1\n  max_ticks: 0\n",
            "experiment.max_ticks",
        ),
        (
            "experiment:\n  name: ok\n  seed: 1\n  max_ticks: -1\n",
            "experiment.max_ticks",
        ),
        (
            f"experiment:\n  name: ok\n  seed: 1\n  max_ticks: {MAX_TICKS + 1}\n",
            "experiment.max_ticks",
        ),
        ("experiment: [\n", "invalid YAML"),
    ],
)
def test_rejects_invalid_documents(tmp_path: Path, body: str, message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        load_config(write_config(tmp_path, body))


@pytest.mark.parametrize(
    "body",
    [
        "experiment:\n  name: first\n  name: second\n  seed: 1\n  max_ticks: 2\n",
        "experiment:\n  name: first\n  seed: 1\n  max_ticks: 2\nexperiment:\n  name: second\n  seed: 2\n  max_ticks: 3\n",
    ],
)
def test_rejects_duplicate_mapping_keys(tmp_path: Path, body: str) -> None:
    with pytest.raises(ConfigError, match="duplicate mapping key"):
        load_config(write_config(tmp_path, body))


def test_safe_loader_rejects_python_object_constructor(tmp_path: Path) -> None:
    marker = tmp_path / "must-not-exist.txt"
    body = (
        "experiment:\n"
        "  name: !!python/object/apply:pathlib.Path.write_text\n"
        f"    - {marker.as_posix()}\n"
        "    - unsafe\n"
        "  seed: 1\n"
        "  max_ticks: 1\n"
    )
    with pytest.raises(ConfigError, match="invalid YAML"):
        load_config(write_config(tmp_path, body))
    assert not marker.exists()


def test_accepts_fixed_max_tick_boundary(tmp_path: Path) -> None:
    body = f"experiment:\n  name: max\n  seed: 1\n  max_ticks: {MAX_TICKS}\n"
    assert load_config(write_config(tmp_path, body)).max_ticks == MAX_TICKS


def test_rejects_missing_file_and_directory(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="regular file"):
        load_config(tmp_path / "missing.yaml")
    with pytest.raises(ConfigError, match="regular file"):
        load_config(tmp_path)


def test_reports_unreadable_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = write_config(tmp_path, "experiment: {}\n")

    def fail_read(self: Path, *args: object, **kwargs: object) -> str:
        raise PermissionError("denied for test")

    monkeypatch.setattr(Path, "read_text", fail_read)
    with pytest.raises(ConfigError, match="cannot read config file.*denied for test"):
        load_config(path)
