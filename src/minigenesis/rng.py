"""Run-scoped random number generation."""

from __future__ import annotations

import random
from typing import Any


RNG_IMPLEMENTATION = "python.random.Random/MT19937"


class RNGContext:
    """An independent and explicitly seeded random source for one run."""

    __slots__ = ("_random", "seed")

    def __init__(self, seed: int) -> None:
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ValueError("seed must be a non-negative integer")
        self.seed = seed
        self._random = random.Random(seed)

    @property
    def implementation(self) -> str:
        return RNG_IMPLEMENTATION

    def random(self) -> float:
        """Return the next value from this run's random stream."""

        return self._random.random()

    def getstate(self) -> tuple[Any, ...]:
        """Return state for deterministic checks without consuming the stream."""

        return self._random.getstate()

