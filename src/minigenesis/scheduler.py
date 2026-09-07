"""Run-scoped ordering without state mutation or action execution."""

from collections.abc import Iterable

from .agent import Agent
from .rng import RNGContext


def schedule(agents: Iterable[Agent], rng: RNGContext) -> list[Agent]:
    ordered = sorted((agent for agent in agents if agent.alive), key=lambda agent: agent.id)
    if len(ordered) > 1:
        rng.shuffle(ordered)
    return ordered
