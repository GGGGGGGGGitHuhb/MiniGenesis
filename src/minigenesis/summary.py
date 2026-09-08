"""Canonical deterministic summaries for completed runs."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .rng import RNG_IMPLEMENTATION
from typing import TYPE_CHECKING
from types import MappingProxyType
from collections.abc import Mapping
from dataclasses import asdict

if TYPE_CHECKING:
    from .simulation import Simulation
    from .world import World


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

    if simulation.failed or simulation.tick != simulation.config.max_ticks:
        raise ValueError("cannot summarize an incomplete simulation")

    digest_input: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION if simulation.world is None else "minigenesis.summary.v2",
        "experiment_name": simulation.config.name,
        "seed": simulation.config.seed,
        "rng_implementation": RNG_IMPLEMENTATION,
        "requested_ticks": simulation.config.max_ticks,
        "completed_ticks": simulation.tick,
        "status": "completed",
    }
    if simulation.world is not None:
        digest_input["config"] = {"world": asdict(simulation.config.world), "agent": asdict(simulation.config.agent)}
        digest_input["state"] = _plain(simulation.snapshot())
    digest = hashlib.sha256(canonical_json_bytes(digest_input)).hexdigest()
    return {**digest_input, "digest": f"sha256:{digest}"}


def canonical_output_bytes(summary: dict[str, Any]) -> bytes:
    """Return one canonical JSON object followed by exactly one newline."""

    expected = SUMMARY_FIELDS if summary.get("schema_version") == SCHEMA_VERSION else SUMMARY_FIELDS[:-1] + ("config", "state", "digest")
    if summary.get("schema_version") not in (SCHEMA_VERSION, "minigenesis.summary.v2") or tuple(summary) != expected:
        raise ValueError("summary fields or field order do not match the S1 contract")
    return canonical_json_bytes(summary) + b"\n"



def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def project_state(world: World, tick: int) -> Mapping[str, Any]:
    """Canonical immutable projection; never a source of mutable world state."""
    world.verify(tick)
    agents = sorted(world.agents.values(), key=lambda agent: agent.id)
    living = [agent for agent in agents if agent.alive]
    ledger = world.ledger
    return MappingProxyType({
        "tick": tick,
        "world_resource": world.resource,
        "living_count": len(living),
        "dead_count": len(agents) - len(living),
        "living_agent_energy": sum(agent.energy for agent in living),
        "ledger": MappingProxyType({
            "initial_resource": ledger.initial_resource,
            "initial_agent_energy": ledger.initial_agent_energy,
            "cumulative_external_inflow": ledger.cumulative_external_inflow,
            "cumulative_dissipated_energy": ledger.cumulative_dissipated_energy,
            "valid": True,
        }),
        "agents": tuple(MappingProxyType({"id": a.id, "energy": a.energy, "age": a.age, "alive": a.alive}) for a in agents),
    })
