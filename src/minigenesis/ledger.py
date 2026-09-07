"""An auditable integer resource ledger; verification never repairs state."""

from dataclasses import dataclass


class ConsistencyError(RuntimeError):
    """A world invariant failed and the run must be discarded."""


@dataclass(slots=True)
class Ledger:
    initial_resource: int
    initial_agent_energy: int
    cumulative_external_inflow: int = 0
    cumulative_dissipated_energy: int = 0

    def verify(self, tick: int, world_resource: int, living_agent_energy: int) -> None:
        accounts = {
            "initial_resource": self.initial_resource,
            "initial_agent_energy": self.initial_agent_energy,
            "cumulative_external_inflow": self.cumulative_external_inflow,
            "world_resource": world_resource,
            "living_agent_energy": living_agent_energy,
            "cumulative_dissipated_energy": self.cumulative_dissipated_energy,
        }
        left = self.initial_resource + self.initial_agent_energy + self.cumulative_external_inflow
        right = world_resource + living_agent_energy + self.cumulative_dissipated_energy
        if any(type(value) is not int or value < 0 for value in accounts.values()) or left != right:
            raise ConsistencyError(f"ledger mismatch at tick {tick}: {accounts}; left={left}, right={right}")
