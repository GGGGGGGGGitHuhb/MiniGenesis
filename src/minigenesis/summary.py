"""Canonical deterministic summaries for completed runs."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .rng import RNG_IMPLEMENTATION
from .simulation import Simulation


SCHEMA_VERSION = "minigenesis.summary.v1"
SUMMARY_FIELDS = (
    "schema_version",
    "experiment_name",
    "seed",
    "rng_implementation",
    "requested_ticks",
    "completed_ticks",
    "status",
    "digest",
)


def canonical_json_bytes(value: dict[str, Any]) -> bytes:
    """Serialize insertion-ordered JSON using the approved byte contract."""

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def build_summary(simulation: Simulation) -> dict[str, Any]:
    """Build a canonical summary without changing simulation state."""

    if simulation.tick != simulation.config.max_ticks:
        raise ValueError("cannot summarize an incomplete simulation")

    digest_input: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "experiment_name": simulation.config.name,
        "seed": simulation.config.seed,
        "rng_implementation": RNG_IMPLEMENTATION,
        "requested_ticks": simulation.config.max_ticks,
        "completed_ticks": simulation.tick,
        "status": "completed",
    }
    digest = hashlib.sha256(canonical_json_bytes(digest_input)).hexdigest()
    return {**digest_input, "digest": f"sha256:{digest}"}


def canonical_output_bytes(summary: dict[str, Any]) -> bytes:
    """Return one canonical JSON object followed by exactly one newline."""

    if tuple(summary) != SUMMARY_FIELDS:
        raise ValueError("summary fields or field order do not match the S1 contract")
    return canonical_json_bytes(summary) + b"\n"

