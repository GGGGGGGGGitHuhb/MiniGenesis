"""Resource ownership, action settlement and lifecycle accounting."""

from .actions import Action, ActionIntent, ActionResult
from .agent import Agent
from .config import AgentConfig, WorldConfig
from .ledger import ConsistencyError, Ledger


class World:
    __slots__ = ("config", "agent_config", "resource", "agents", "ledger")

    def __init__(self, config: WorldConfig, agent_config: AgentConfig) -> None:
        self.config = config
        self.agent_config = agent_config
        self.resource = config.initial_resource
        self.agents = {i: Agent(i, agent_config.initial_energy) for i in range(agent_config.initial_count)}
        self.ledger = Ledger(config.initial_resource, agent_config.initial_count * agent_config.initial_energy)
        self.verify(0)

    def inject(self) -> None:
        self.resource += self.config.resource_inflow_per_tick
        self.ledger.cumulative_external_inflow += self.config.resource_inflow_per_tick

    def apply(self, intent: ActionIntent) -> ActionResult:
        def rejected(reason: str) -> ActionResult:
            return ActionResult(intent.agent_id, intent.action, "rejected", reason)

        if type(intent.agent_id) is not int or intent.agent_id not in self.agents:
            return rejected("unknown_agent")
        agent = self.agents[intent.agent_id]
        if not agent.alive:
            return rejected("dead_agent")
        if not isinstance(intent.action, Action):
            return rejected("invalid_action")
        if intent.action == Action.WAIT:
            return ActionResult(agent.id, intent.action, "applied", None)
        if agent.energy < self.config.action_cost:
            return rejected("insufficient_energy")
        cost = self.config.action_cost
        agent.energy -= cost
        self.ledger.cumulative_dissipated_energy += cost
        harvested = min(self.config.harvest_amount, self.resource)
        self.resource -= harvested
        agent.energy += harvested
        return ActionResult(agent.id, intent.action, "applied", None, harvested, cost)

    def metabolize_and_age(self, agent: Agent) -> None:
        cost = min(self.config.metabolism_cost, agent.energy)
        agent.energy -= cost
        self.ledger.cumulative_dissipated_energy += cost
        agent.age += 1

    def settle_death(self, agent: Agent) -> None:
        if agent.alive and (agent.energy <= 0 or agent.age >= self.agent_config.max_age):
            self.resource += agent.energy
            agent.energy = 0
            agent.alive = False

    def verify(self, tick: int) -> None:
        for key, agent in self.agents.items():
            if (type(agent.id) is not int or agent.id != key or type(agent.energy) is not int
                    or agent.energy < 0 or type(agent.age) is not int or agent.age < 0
                    or type(agent.alive) is not bool or (not agent.alive and agent.energy != 0)):
                raise ConsistencyError(f"invalid agent state at tick {tick}: {agent}")
        self.ledger.verify(tick, self.resource, sum(a.energy for a in self.agents.values() if a.alive))
