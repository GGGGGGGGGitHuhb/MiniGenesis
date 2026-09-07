from __future__ import annotations

import builtins
import json
from pathlib import Path
import socket
import subprocess
import sys

import pytest

from minigenesis import cli


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = REPO_ROOT / "examples" / "v0.1" / "s1-baseline.yaml"


def run_cli(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, "-m", "minigenesis", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )


def test_help_documents_real_interface() -> None:
    result = run_cli("--help")
    assert result.returncode == 0
    assert b"--config PATH" in result.stdout
    assert b"--output-format {text,json}" in result.stdout
    assert result.stderr == b""


def test_example_json_success_is_one_parseable_object() -> None:
    result = run_cli("--config", str(EXAMPLE), "--output-format", "json")
    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout.endswith(b"\n") and not result.stdout.endswith(b"\n\n")
    parsed = json.loads(result.stdout)
    assert parsed["completed_ticks"] == 10
    assert parsed["requested_ticks"] == 10
    assert parsed["status"] == "completed"


def test_default_text_output_has_same_meaning() -> None:
    result = run_cli("--config", str(EXAMPLE))
    assert result.returncode == 0
    text = result.stdout.decode("utf-8")
    assert "s1-baseline" in text
    assert "10/10 ticks" in text
    assert "seed 1" in text
    assert "python.random.Random/MT19937" in text
    assert "sha256:" in text
    assert result.stderr == b""


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("experiment:\n  name: ok\n  seed: 1\n", "missing required"),
        (
            "experiment:\n  name: ok\n  seed: 1\n  max_ticks: 1\n  unknown: 2\n",
            "unknown field",
        ),
        (
            "experiment:\n  name: ok\n  seed: true\n  max_ticks: 1\n",
            "experiment.seed",
        ),
        (
            "experiment:\n  name: ok\n  seed: 1\n  max_ticks: 100001\n",
            "experiment.max_ticks",
        ),
        (
            "experiment:\n  name: first\n  name: last\n  seed: 1\n  max_ticks: 1\n",
            "duplicate mapping key",
        ),
        ("experiment: [\n", "invalid YAML"),
    ],
)
def test_invalid_config_exits_nonzero_without_success_output(
    tmp_path: Path, body: str, message: str
) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(body, encoding="utf-8")
    result = run_cli("--config", str(path), "--output-format", "json")
    assert result.returncode != 0
    assert result.stdout == b""
    assert message.encode() in result.stderr
    assert b"Traceback" not in result.stderr


@pytest.mark.parametrize("path_kind", ["missing", "directory"])
def test_invalid_config_path_fails_cleanly(tmp_path: Path, path_kind: str) -> None:
    path = tmp_path / "config.yaml" if path_kind == "missing" else tmp_path
    result = run_cli("--config", str(path), "--output-format", "json")
    assert result.returncode != 0
    assert result.stdout == b""
    assert b"regular file" in result.stderr
    assert b"Traceback" not in result.stderr


def test_missing_required_argument_uses_nonzero_exit() -> None:
    result = run_cli("--output-format", "json")
    assert result.returncode != 0
    assert result.stdout == b""
    assert b"--config" in result.stderr
    assert b"Traceback" not in result.stderr


def test_invalid_config_is_rejected_before_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text("experiment: {}\n", encoding="utf-8")

    def forbidden_execute(config: object) -> object:
        raise AssertionError("simulation execution must not begin")

    monkeypatch.setattr(cli, "execute", forbidden_execute)
    assert cli.main(["--config", str(path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "missing required" in captured.err


def test_runtime_does_not_use_network_subprocess_or_file_writes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("forbidden host capability was invoked")

    original_open = builtins.open

    def guarded_open(file: object, mode: str = "r", *args: object, **kwargs: object):
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError("runtime attempted a file write")
        return original_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)

    assert cli.main(["--config", str(EXAMPLE)]) == 0
    captured = capsys.readouterr()
    assert "completed 10/10 ticks" in captured.out
    assert captured.err == ""
