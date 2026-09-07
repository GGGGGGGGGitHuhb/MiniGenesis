from __future__ import annotations

import random

import pytest

from minigenesis.cli import execute
from minigenesis.config import ExperimentConfig
from minigenesis.rng import RNG_IMPLEMENTATION, RNGContext
from minigenesis.summary import canonical_output_bytes


def make_config(name: str, seed: int, ticks: int) -> ExperimentConfig:
    return ExperimentConfig(name=name, seed=seed, max_ticks=ticks)


def test_rng_has_stable_implementation_identifier() -> None:
    assert RNGContext(1).implementation == RNG_IMPLEMENTATION
    assert RNG_IMPLEMENTATION == "python.random.Random/MT19937"


def test_rng_known_seed_sequence() -> None:
    rng = RNGContext(1)
    assert [rng.random() for _ in range(3)] == pytest.approx(
        [0.13436424411240122, 0.8474337369372327, 0.763774618976614]
    )


def test_rng_instances_are_independent_and_different_seeds_differ() -> None:
    first = RNGContext(23)
    second = RNGContext(23)
    other = RNGContext(24)
    first_value = first.random()
    first.random()
    assert second.random() == first_value
    assert other.random() != first_value


@pytest.mark.parametrize("seed", [True, -1, 1.5, "1"])
def test_rng_rejects_invalid_seed(seed: object) -> None:
    with pytest.raises(ValueError, match="non-negative integer"):
        RNGContext(seed)  # type: ignore[arg-type]


def test_same_input_produces_identical_complete_json() -> None:
    config = make_config("same", 42, 25)
    assert canonical_output_bytes(execute(config)) == canonical_output_bytes(execute(config))


def test_a_b_a_runs_are_isolated_in_one_process() -> None:
    a = make_config("A", 101, 7)
    b = make_config("B", 202, 13)
    a1 = canonical_output_bytes(execute(a))
    b_result = canonical_output_bytes(execute(b))
    a2 = canonical_output_bytes(execute(a))
    assert a1 == a2
    assert b_result != a1


def test_experiment_does_not_touch_module_level_random_state() -> None:
    random.seed(9876)
    before = random.getstate()
    execute(make_config("isolated", 1, 100))
    assert random.getstate() == before

