from __future__ import annotations

import hashlib
import json

import pytest

from minigenesis.cli import execute
from minigenesis.config import ExperimentConfig
from minigenesis.simulation import Simulation
from minigenesis.summary import (
    SCHEMA_VERSION,
    SUMMARY_FIELDS,
    build_summary,
    canonical_output_bytes,
)


def completed_summary(name: str = "baseline 中文") -> dict[str, object]:
    return execute(ExperimentConfig(name=name, seed=1, max_ticks=10))


def test_summary_has_exact_fields_order_and_fixed_values() -> None:
    summary = completed_summary()
    assert tuple(summary) == SUMMARY_FIELDS
    assert summary == {
        "schema_version": SCHEMA_VERSION,
        "experiment_name": "baseline 中文",
        "seed": 1,
        "rng_implementation": "python.random.Random/MT19937",
        "requested_ticks": 10,
        "completed_ticks": 10,
        "status": "completed",
        "digest": summary["digest"],
    }
    assert isinstance(summary["digest"], str)
    assert str(summary["digest"]).startswith("sha256:")
    assert len(str(summary["digest"])) == 71


def test_digest_can_be_independently_recomputed() -> None:
    summary = completed_summary()
    first_seven = {key: summary[key] for key in SUMMARY_FIELDS[:-1]}
    independent_bytes = json.dumps(
        first_seven, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    expected = "sha256:" + hashlib.sha256(independent_bytes).hexdigest()
    assert summary["digest"] == expected


def test_canonical_json_is_utf8_unescaped_and_has_one_trailing_newline() -> None:
    output = canonical_output_bytes(completed_summary())
    assert "中文".encode("utf-8") in output
    assert b"\\u4e2d" not in output
    assert output.endswith(b"\n")
    assert not output.endswith(b"\n\n")
    assert b'": ' not in output
    assert b', "' not in output
    assert json.loads(output) == completed_summary()


def test_summary_contains_no_host_specific_metadata(tmp_path: object) -> None:
    output = canonical_output_bytes(completed_summary()).decode("utf-8")
    for forbidden in ("absolute_path", "timestamp", "wall_time", "process_id", "pid"):
        assert forbidden not in output.lower()


def test_canonical_output_rejects_wrong_order_or_fields() -> None:
    reversed_summary = dict(reversed(list(completed_summary().items())))
    with pytest.raises(ValueError, match="field order"):
        canonical_output_bytes(reversed_summary)


def test_incomplete_simulation_cannot_claim_completed_summary() -> None:
    simulation = Simulation(ExperimentConfig(name="incomplete", seed=1, max_ticks=2))
    simulation.step()
    state_before = simulation.tick
    with pytest.raises(ValueError, match="incomplete"):
        build_summary(simulation)
    assert simulation.tick == state_before
