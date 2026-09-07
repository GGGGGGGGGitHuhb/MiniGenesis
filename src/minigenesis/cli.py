"""Command-line integration for one MiniGenesis S1 experiment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Sequence

from .config import ConfigError, ExperimentConfig, load_config
from .simulation import Simulation
from .summary import build_summary, canonical_output_bytes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m minigenesis",
        description="Run a finite deterministic MiniGenesis empty-world experiment.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        metavar="PATH",
        help="UTF-8 YAML experiment configuration file",
    )
    parser.add_argument(
        "--output-format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    return parser


def execute(config: ExperimentConfig) -> dict[str, Any]:
    """Execute one isolated run and return its completed summary."""

    simulation = Simulation(config)
    simulation.run()
    return build_summary(simulation)


def _text_output(summary: dict[str, Any]) -> str:
    return (
        f"Experiment {summary['experiment_name']!r} completed "
        f"{summary['completed_ticks']}/{summary['requested_ticks']} ticks "
        f"with seed {summary['seed']} "
        f"({summary['rng_implementation']}); {summary['digest']}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        summary = execute(config)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # Defensive CLI boundary: no traceback for end users.
        print(f"error: unexpected failure: {exc}", file=sys.stderr)
        return 1

    if args.output_format == "json":
        sys.stdout.buffer.write(canonical_output_bytes(summary))
        sys.stdout.buffer.flush()
    else:
        print(_text_output(summary))
    return 0

