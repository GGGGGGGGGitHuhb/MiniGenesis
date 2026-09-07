from __future__ import annotations

import pytest

from minigenesis.config import ExperimentConfig, MAX_TICKS
from minigenesis.simulation import Simulation, SimulationStateError


def config(max_ticks: int = 3, seed: int = 1) -> ExperimentConfig:
    return ExperimentConfig(name="test", seed=seed, max_ticks=max_ticks)


def test_tick_starts_at_zero_and_single_step_increments_once() -> None:
    simulation = Simulation(config())
    assert simulation.tick == 0
    simulation.step()
    assert simulation.tick == 1


@pytest.mark.parametrize("max_ticks", [1, 2, 10, MAX_TICKS])
def test_run_stops_exactly_at_finite_boundary(max_ticks: int) -> None:
    simulation = Simulation(config(max_ticks=max_ticks))
    simulation.run()
    assert simulation.tick == max_ticks
    with pytest.raises(SimulationStateError, match="already reached"):
        simulation.step()


def test_empty_world_ticks_do_not_consume_rng() -> None:
    simulation = Simulation(config(max_ticks=10_000, seed=7))
    before = simulation.rng.getstate()
    simulation.run()
    assert simulation.rng.getstate() == before


def test_each_simulation_starts_with_fresh_tick_and_rng() -> None:
    first = Simulation(config(max_ticks=2, seed=11))
    first.run()
    first.rng.random()

    second = Simulation(config(max_ticks=2, seed=11))
    assert second.tick == 0
    assert second.rng.random() == pytest.approx(0.4523795535098186)

