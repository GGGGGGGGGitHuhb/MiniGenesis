"""Finite, deterministic empty-world tick progression."""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import ExperimentConfig
from .rng import RNGContext


class SimulationStateError(RuntimeError):
    """The requested tick transition is invalid for the current state."""


@dataclass(slots=True)
class Simulation:
    """One isolated empty-world run."""

    config: ExperimentConfig
    rng: RNGContext = field(init=False)
    tick: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.rng = RNGContext(self.config.seed)

    def step(self) -> None:
        """Complete exactly one empty-world step without consuming RNG."""

        if self.tick >= self.config.max_ticks:
            raise SimulationStateError("simulation has already reached max_ticks")
        self.tick += 1

    def run(self) -> None:
        """Advance until the configured finite boundary."""

        while self.tick < self.config.max_ticks:
            self.step()

