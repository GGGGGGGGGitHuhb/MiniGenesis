from dataclasses import replace
import hashlib
import json
import random

import pytest

from minigenesis.cli import execute
from minigenesis.config import ExperimentConfig, load_config
from minigenesis.rng import RNGContext
from minigenesis.scheduler import schedule
from minigenesis.simulation import Simulation
from minigenesis.summary import build_summary, canonical_output_bytes
from test_lifecycle import config, independent_balance


def trajectory(cfg, reverse=False):
    sim = Simulation(cfg)
    if reverse:
        sim.world.agents = dict(reversed(list(sim.world.agents.items())))
    states, orders = [sim.snapshot()], []
    probe = RNGContext(cfg.seed)
    for _ in range(cfg.max_ticks):
        orders.append([a.id for a in schedule(sim.world.agents.values(), probe)])
        sim.step()
        assert sim.rng.getstate() == probe.getstate()
        independent_balance(sim.snapshot())
        states.append(sim.snapshot())
    return states, orders, canonical_output_bytes(build_summary(sim))


def test_scheduler_determinism_container_order_and_competition():
    cfg = config(count=3, resource=1, inflow=1, energy=10, harvest=1, ticks=6)
    global_before = random.getstate()
    a = trajectory(cfg)
    assert a == trajectory(cfg)
    assert a == trajectory(cfg, reverse=True)
    b = trajectory(replace(cfg, seed=7))
    assert a[1] != b[1]
    assert a[0] != b[0]
    assert random.getstate() == global_before


def test_scheduler_zero_one_agent_does_not_consume_rng():
    sim = Simulation(config(count=1))
    before = sim.rng.getstate()
    assert schedule([], sim.rng) == []
    assert [a.id for a in schedule(sim.world.agents.values(), sim.rng)] == [0]
    sim.world.agents[0].alive = False
    assert schedule(sim.world.agents.values(), sim.rng) == []
    assert sim.rng.getstate() == before


def test_snapshot_nested_read_only_no_rng_or_history_and_ids():
    sim = Simulation(config(count=3))
    before, rng = sim.snapshot(), sim.rng.getstate()
    for _ in range(10):
        assert sim.snapshot() is before
    with pytest.raises(TypeError):
        before['tick'] = 8
    with pytest.raises(TypeError):
        before['ledger']['valid'] = False
    with pytest.raises(TypeError):
        before['agents'][0]['energy'] = 99
    assert sim.rng.getstate() == rng
    sim.step()
    assert before['tick'] == 0 and before['agents'][0]['age'] == 0
    assert [a['id'] for a in sim.snapshot()['agents']] == [0,1,2]


def test_determinism_s2_and_mixed_a_b_a():
    a = config(seed=2)
    first = trajectory(a)
    trajectory(config(seed=5, count=2))
    assert first == trajectory(a)
    s1 = ExperimentConfig('s1', 9, 2)
    old = canonical_output_bytes(execute(s1))
    trajectory(a)
    assert old == canonical_output_bytes(execute(s1))
    execute(s1)
    assert first == trajectory(a)


def test_v2_exact_field_order_bytes_and_independent_digest():
    cfg = config(ticks=1, resource=2, harvest=4, energy=10, age=20)
    actual = execute(cfg)
    expected = {
        'schema_version':'minigenesis.summary.v2', 'experiment_name':'test', 'seed':1,
        'rng_implementation':'python.random.Random/MT19937', 'requested_ticks':1,
        'completed_ticks':1, 'status':'completed',
        'config':{'world':{'initial_resource':2,'resource_inflow_per_tick':0,'harvest_amount':4,'action_cost':1,'metabolism_cost':1},'agent':{'initial_count':1,'initial_energy':10,'max_age':20}},
        'state':{'tick':1,'world_resource':0,'living_count':1,'dead_count':0,'living_agent_energy':10,
                 'ledger':{'initial_resource':2,'initial_agent_energy':10,'cumulative_external_inflow':0,'cumulative_dissipated_energy':2,'valid':True},
                 'agents':[{'id':0,'energy':10,'age':1,'alive':True}]},
    }
    payload = json.dumps(expected, ensure_ascii=False, separators=(',', ':')).encode()
    expected['digest'] = 'sha256:' + hashlib.sha256(payload).hexdigest()
    raw = json.dumps(expected, ensure_ascii=False, separators=(',', ':')).encode() + b'\n'
    assert canonical_output_bytes(actual) == raw
    assert not raw.endswith(b'\n\n')
    changed = replace(cfg, world=replace(cfg.world, harvest_amount=5))
    assert execute(changed)['state'] == actual['state']
    assert execute(changed)['digest'] != actual['digest']
    with pytest.raises(ValueError):
        canonical_output_bytes(dict(reversed(list(actual.items()))))


def test_v1_baseline_historical_exact_bytes():
    output = canonical_output_bytes(execute(load_config('examples/v0.1/s1-baseline.yaml')))
    assert hashlib.sha256(output).hexdigest() == '4de55827ebbd9719a6bc42d8f426cf72307a0172603c3ba0090c2bbe166f6b34'
    assert json.loads(output)['digest'] == 'sha256:93deab1c067673d192661637a2938bd919c768a8392d69d3513cf32fa10f12cb'


def test_s2_cli_json_text_and_host_boundary(monkeypatch, capsys):
    import builtins
    import socket
    import subprocess
    from pathlib import Path
    from minigenesis import cli
    def forbidden(*args, **kwargs):
        raise AssertionError('forbidden host operation')
    original = builtins.open
    def guarded(file, mode='r', *args, **kwargs):
        assert not any(flag in mode for flag in ('w','a','x','+'))
        return original(file,mode,*args,**kwargs)
    monkeypatch.setattr(builtins,'open',guarded)
    for target, name in [(Path,'write_text'),(Path,'write_bytes'),(socket,'socket'),(socket,'create_connection'),(subprocess,'Popen'),(subprocess,'run')]:
        monkeypatch.setattr(target,name,forbidden)
    assert cli.main(['--config','examples/v0.1/s2-resource-world.yaml']) == 0
    captured = capsys.readouterr()
    assert '30/30 ticks' in captured.out and 'resource=310' in captured.out
    assert 'living=0' in captured.out and 'dead=3' in captured.out and 'ledger_valid=True' in captured.out
    assert captured.err == ''
