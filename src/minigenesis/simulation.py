"""Finite simulation with explicit, failure-latched tick phases."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Any

from .config import ExperimentConfig
from .ledger import ConsistencyError
from .rng import RNGContext
from .scheduler import schedule
from .world import World


class SimulationStateError(RuntimeError):
    """The requested tick transition is invalid for the current state."""


@dataclass(slots=True)
class Simulation:
    config: ExperimentConfig
    rng: RNGContext = field(init=False)
    tick: int = field(default=0, init=False)
    failed: bool = field(default=False, init=False)
    world: World | None = field(default=None, init=False)
    _snapshot: Mapping[str, Any] | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.rng = RNGContext(self.config.seed)
        if self.config.world is not None:
            self.world = World(self.config.world, self.config.agent)
            from .summary import project_state
            self._snapshot = project_state(self.world, 0)

    def snapshot(self) -> Mapping[str, Any]:
        """Read the last completely verified state, including after failure."""
        if self._snapshot is None:
            raise SimulationStateError("S1 empty worlds have no resource state snapshot")
        return self._snapshot

    def step(self) -> None:
        if self.failed:
            raise SimulationStateError("simulation has failed; cannot continue")
        if self.tick >= self.config.max_ticks:
            raise SimulationStateError("simulation has already reached max_ticks")
        target = self.tick + 1
        try:
            if self.world is not None:
                world = self.world
                # 1. External inflow precedes the shared resource observation.
                world.inject()
                # 2-3. Canonical live snapshot, then run-local shuffle.
                ordered = schedule(world.agents.values(), self.rng)
                # 4. Generate ALL intents before any resource settlement.
                intents = [agent.intent(world.resource) for agent in ordered]
                # 5. Validate ownership and settle in the scheduled order.
                for agent, intent in zip(ordered, intents, strict=True):
                    if type(intent.agent_id) is not int or intent.agent_id != agent.id:
                        raise ConsistencyError(f"action ownership mismatch at tick {target}")
                    result = world.apply(intent)
                    if result.status != "applied" and result.reason != "insufficient_energy":
                        raise ConsistencyError(f"illegal pipeline request at tick {target}: {result.reason}")
                # 6. Every start-of-tick live agent ages, even at zero energy.
                for agent in ordered:
                    world.metabolize_and_age(agent)
                # 7. Death is deferred until all actions and metabolism finish.
                for agent in ordered:
                    world.settle_death(agent)
                # 8. Verify and construct before publishing tick or snapshot.
                world.verify(target)
                from .summary import project_state
                next_snapshot = project_state(world, target)
                self._snapshot = next_snapshot
            self.tick = target
        except Exception:
            self.failed = True
            raise

    def run(self) -> None:
        if self.failed:
            raise SimulationStateError("simulation has failed; cannot continue")
        while self.tick < self.config.max_ticks:
            self.step()
