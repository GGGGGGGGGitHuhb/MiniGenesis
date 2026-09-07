"""Immutable requests and outcomes for the two baseline actions."""

from dataclasses import dataclass
from enum import StrEnum


class Action(StrEnum):
    HARVEST = "HARVEST"
    WAIT = "WAIT"


@dataclass(frozen=True, slots=True)
class ActionIntent:
    agent_id: int
    action: Action


@dataclass(frozen=True, slots=True)
class ActionResult:
    agent_id: int
    action: Action
    status: str
    reason: str | None
    harvested: int = 0
    cost_paid: int = 0
