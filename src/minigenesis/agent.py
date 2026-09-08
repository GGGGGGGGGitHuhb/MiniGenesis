"""Individual state and the explicitly non-genetic baseline policy."""

from dataclasses import dataclass

from .actions import Action, ActionIntent


@dataclass(slots=True)
class Agent:
    id: int
    energy: int
    age: int = 0
    alive: bool = True

    def intent(self, available_resource: int) -> ActionIntent:
        return ActionIntent(self.id, Action.HARVEST if available_resource > 0 else Action.WAIT)
