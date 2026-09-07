from dataclasses import replace

import pytest

from minigenesis.actions import Action, ActionIntent
from minigenesis.agent import Agent
from minigenesis.config import AgentConfig, ExperimentConfig, WorldConfig
from minigenesis.ledger import ConsistencyError
from minigenesis.simulation import Simulation, SimulationStateError
from minigenesis.summary import build_summary
from minigenesis.world import World


def config(*, ticks=3, seed=1, resource=10, inflow=0, harvest=4, action=1, metabolism=1, count=1, energy=10, age=20):
    return ExperimentConfig('test', seed, ticks, WorldConfig(resource, inflow, harvest, action, metabolism), AgentConfig(count, energy, age))


def independent_balance(state):
    ledger = state['ledger']
    assert ledger['initial_resource'] + ledger['initial_agent_energy'] + ledger['cumulative_external_inflow'] == state['world_resource'] + sum(a['energy'] for a in state['agents'] if a['alive']) + ledger['cumulative_dissipated_energy']
    assert state['living_count'] == sum(a['alive'] for a in state['agents'])
    assert state['dead_count'] + state['living_count'] == len(state['agents'])
    assert all(type(a['energy']) is int and a['energy'] >= 0 for a in state['agents'])


@pytest.mark.parametrize('resource,harvest,expected', [(0,4,0), (2,4,2), (4,4,4), (8,4,4), (8,0,0)])
def test_harvest_resource_boundaries(resource, harvest, expected):
    sim = Simulation(config(resource=resource, harvest=harvest))
    world = sim.world
    result = world.apply(ActionIntent(0, Action.HARVEST))
    assert (result.status, result.reason, result.harvested, result.cost_paid) == ('applied', None, expected, 1)
    assert world.resource == resource - expected
    assert world.agents[0].energy == 9 + expected
    assert world.ledger.cumulative_dissipated_energy == 1
    world.verify(0)


def test_wait_action_and_insufficient_energy_no_transfer():
    world = Simulation(config(action=11)).world
    before = (world.resource, world.agents[0].energy, world.ledger.cumulative_dissipated_energy)
    for action, status, reason in [(Action.WAIT, 'applied', None), (Action.HARVEST, 'rejected', 'insufficient_energy')]:
        result = world.apply(ActionIntent(0, action))
        assert (result.status, result.reason, result.harvested, result.cost_paid) == (status, reason, 0, 0)
        assert before == (world.resource, world.agents[0].energy, world.ledger.cumulative_dissipated_energy)
    sim = Simulation(config(action=11, energy=2))
    for tick in range(3):
        sim.step()
        independent_balance(sim.snapshot())
    assert sim.snapshot()['agents'][0] == dict(id=0, energy=0, age=2, alive=False)


@pytest.mark.parametrize('intent,reason', [(ActionIntent(5, Action.HARVEST), 'unknown_agent'), (ActionIntent(True, Action.HARVEST), 'unknown_agent'), (ActionIntent(0, 'BAD'), 'invalid_action')])
def test_invalid_action_does_not_mutate(intent, reason):
    sim = Simulation(config())
    before = sim.snapshot()
    result = sim.world.apply(intent)
    assert (result.status, result.reason, result.harvested, result.cost_paid) == ('rejected', reason, 0, 0)
    from minigenesis.summary import project_state
    assert project_state(sim.world, 0) == before


def test_dead_agent_action_rejected_death_only_once_and_age_frozen():
    sim = Simulation(config(ticks=3, energy=10, age=1))
    sim.step()
    world = sim.world
    assert world.resource == 18  # 10 initial + 10 energy - action 1 - metabolism 1
    assert world.agents[0] == Agent(0, 0, 1, False)
    world.settle_death(world.agents[0])
    assert world.resource == 18
    result = world.apply(ActionIntent(0, Action.HARVEST))
    assert result.reason == 'dead_agent'
    sim.run()
    assert world.agents[0] == Agent(0, 0, 1, False)
    independent_balance(sim.snapshot())


@pytest.mark.parametrize('cfg,expected', [
    (config(resource=10, ticks=2), [(10,10,0,0,True), (6,12,1,2,True), (2,14,2,4,True)]),
    (config(resource=2,ticks=2), [(2,10,0,0,True), (0,10,1,2,True), (0,9,2,3,True)]),
    (config(resource=0,energy=1,ticks=2), [(0,1,0,0,True), (0,0,1,1,False), (0,0,1,1,False)]),
    (config(resource=0,energy=5,age=1,ticks=2), [(0,5,0,0,True), (4,0,1,1,False), (4,0,1,1,False)]),
    (config(resource=0,energy=1,age=1,ticks=2), [(0,1,0,0,True), (0,0,1,1,False), (0,0,1,1,False)]),
])
def test_lifecycle_hand_calculated_ledger_each_tick(cfg, expected):
    sim = Simulation(cfg)
    for tick, row in enumerate(expected):
        if tick:
            sim.step()
        state = sim.snapshot()
        a = state['agents'][0]
        assert (state['world_resource'], a['energy'], a['age'], state['ledger']['cumulative_dissipated_energy'], a['alive']) == row
        independent_balance(state)


def test_action_cost_zero_energy_is_not_mid_action_death():
    sim = Simulation(config(ticks=1, resource=4, energy=1, action=1))
    sim.run()
    assert sim.snapshot()['agents'][0] == dict(id=0, energy=3, age=1, alive=True)


def test_all_intents_before_actions_and_fixed_stage_order(monkeypatch):
    events = []
    sim = Simulation(config(ticks=1, resource=0, inflow=1, count=2, energy=3, harvest=1))
    originals = {name: getattr(World,name) for name in ('inject','apply','metabolize_and_age','settle_death','verify')}
    original_intent = Agent.intent
    def intent(agent, resource):
        events.append(('intent', agent.id, resource, agent.age))
        return original_intent(agent, resource)
    monkeypatch.setattr(Agent, 'intent', intent)
    for name, original in originals.items():
        def wrapper(world, *args, name=name, original=original):
            events.append((name,))
            result = original(world,*args)
            if name == 'apply':
                events.append(('result', result.harvested, result.cost_paid))
            return result
        monkeypatch.setattr(World,name,wrapper)
    sim.run()
    kinds = [e[0] for e in events]
    assert kinds == ['inject','intent','intent','apply','result','apply','result','metabolize_and_age','metabolize_and_age','settle_death','settle_death','verify','verify']
    assert [e[2:] for e in events if e[0]=='intent'] == [(1,0),(1,0)]
    assert [e[1:] for e in events if e[0]=='result'] == [(1,1),(0,1)]
    assert sim.snapshot()['ledger']['cumulative_dissipated_energy'] == 4
    independent_balance(sim.snapshot())


def assert_failure_latched(sim, previous):
    assert sim.failed
    assert sim.tick == previous['tick']
    assert sim.snapshot() is previous
    for operation in (sim.step, sim.run):
        with pytest.raises(SimulationStateError, match='failed'):
            operation()
    with pytest.raises(ValueError):
        build_summary(sim)


def test_ledger_fault_latches_without_publishing_or_correcting():
    sim = Simulation(config())
    sim.step()
    previous = sim.snapshot()
    sim.world.ledger.initial_resource += 1
    with pytest.raises(ConsistencyError, match='tick 2.*initial_resource.*left=.*right='):
        sim.step()
    assert sim.world.ledger.initial_resource == 11
    assert_failure_latched(sim, previous)


@pytest.mark.parametrize('fault', ['action', 'ownership', 'unknown', 'exception', 'projection'])
def test_pipeline_failure_latches(monkeypatch, fault):
    sim = Simulation(config())
    previous = sim.snapshot()
    if fault == 'exception':
        def fail(self):
            raise RuntimeError('injected')
        monkeypatch.setattr(World, 'inject', fail)
    elif fault == 'projection':
        import minigenesis.summary as summary
        def fail(*args):
            raise RuntimeError('injected projection')
        monkeypatch.setattr(summary, 'project_state', fail)
    else:
        monkeypatch.setattr(Agent, 'intent', lambda self, resource: ActionIntent(0 if fault=='action' else 99, 'BAD' if fault=='action' else Action.WAIT))
    with pytest.raises((ConsistencyError, RuntimeError)):
        sim.step()
    assert_failure_latched(sim, previous)


def test_cli_ledger_fault_stdout_empty_exit_one(monkeypatch, capsys):
    from minigenesis import cli
    original = World.inject
    def corrupt(world):
        original(world)
        world.resource += 1
    monkeypatch.setattr(World, 'inject', corrupt)
    assert cli.main(['--config','examples/v0.1/s2-resource-world.yaml','--output-format','json']) == 1
    captured = capsys.readouterr()
    assert captured.out == ''
    assert 'tick 1' in captured.err and 'left=' in captured.err and 'right=' in captured.err
    assert 'initial_resource' in captured.err and 'cumulative_dissipated_energy' in captured.err
