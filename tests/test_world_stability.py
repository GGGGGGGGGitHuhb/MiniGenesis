"""Online assertions retain only counters and three memory observations."""
from dataclasses import replace
import gc
import json
import sys
import time
import tracemalloc
from collections.abc import Mapping

import pytest

from minigenesis.config import load_config
from minigenesis.simulation import Simulation
from minigenesis.summary import build_summary
from minigenesis.world import World
from test_lifecycle import config, independent_balance


def retained_size(value, seen=None):
    if seen is None:
        seen = set()
    if id(value) in seen:
        return 0
    seen.add(id(value))
    size = sys.getsizeof(value)
    if isinstance(value, Mapping):
        size += sum(retained_size(k, seen)+retained_size(v, seen) for k,v in value.items())
    elif isinstance(value, (tuple, list)):
        size += sum(retained_size(item, seen) for item in value)
    elif hasattr(type(value), '__slots__'):
        size += sum(retained_size(getattr(value, slot), seen) for slot in type(value).__slots__ if hasattr(value,slot))
    return size


@pytest.mark.slow
@pytest.mark.parametrize('live', [False, True], ids=['example-after-death','active-every-tick'])
def test_100000_tick_world_stability(live, monkeypatch):
    cfg = config(ticks=100000, count=1, energy=10, age=100000, resource=0, inflow=1, harvest=1, action=0, metabolism=1) if live else replace(load_config('examples/v0.1/s2-resource-world.yaml'), max_ticks=100000)
    counts = dict(actions=0, harvest_units=0, metabolism_calls=0, metabolism_units=0)
    apply, metabolize = World.apply, World.metabolize_and_age
    def counted_apply(world, intent):
        result = apply(world, intent)
        if result.status == 'applied':
            counts['actions'] += 1
            counts['harvest_units'] += result.harvested
        return result
    def counted_metabolism(world, agent):
        before = agent.energy
        metabolize(world, agent)
        counts['metabolism_calls'] += 1
        counts['metabolism_units'] += before - agent.energy
    monkeypatch.setattr(World,'apply',counted_apply)
    monkeypatch.setattr(World,'metabolize_and_age',counted_metabolism)
    sim = Simulation(cfg)
    observations = []
    start = time.perf_counter()
    tracemalloc.start()
    try:
        independent_balance(sim.snapshot())
        for tick in range(1,100001):
            sim.step()
            state = sim.snapshot()
            independent_balance(state)
            assert state['tick'] == tick
            if live:
                assert state['living_count'] == (tick < 100000)
                assert state['agents'][0]['age'] == tick
                assert counts['actions'] == counts['metabolism_calls'] == tick
                assert counts['harvest_units'] == counts['metabolism_units'] == tick
                assert state['agents'][0]['energy'] == (10 if tick < 100000 else 0)
            else:
                assert state['living_count'] == (3 if tick < 20 else 0)
                assert state['agents'][0]['age'] == min(tick,20)
            if tick in (1000,10000,100000):
                gc.collect()
                current, peak = tracemalloc.get_traced_memory()
                observations.append(dict(tick=tick, retained_bytes=retained_size(sim), traced_current=current, traced_peak=peak, agents=len(sim.world.agents), snapshot_agents=len(state['agents'])))
        summary = build_summary(sim)
        assert summary['state']['world_resource'] == (10 if live else 1000010)
        assert counts == (dict(actions=100000,harvest_units=100000,metabolism_calls=100000,metabolism_units=100000) if live else dict(actions=60,harvest_units=240,metabolism_calls=60,metabolism_units=60))
        assert max(o['retained_bytes'] for o in observations)-min(o['retained_bytes'] for o in observations) < 4096
        assert observations[-1]['traced_current']-observations[0]['traced_current'] < 65536
        print(json.dumps(dict(scenario='live' if live else 'example',seconds=time.perf_counter()-start,counts=counts,memory=observations,summary=summary), separators=(',', ':')))
    finally:
        tracemalloc.stop()
