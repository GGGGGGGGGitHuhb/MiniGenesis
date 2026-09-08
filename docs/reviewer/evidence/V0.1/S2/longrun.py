"""Independent long-run observability: real transitions, bounded evidence."""
import dataclasses, gc, json, sys, time, tracemalloc
from collections.abc import Mapping
from pathlib import Path
from unittest.mock import patch
from minigenesis.config import ExperimentConfig,AgentConfig,WorldConfig,load_config
from minigenesis.simulation import Simulation
from minigenesis.world import World
from minigenesis.summary import build_summary
OUT=Path(__file__).parent

def size(x,seen=None):
    if seen is None:seen=set()
    if id(x) in seen:return 0
    seen.add(id(x)); total=sys.getsizeof(x)
    if isinstance(x,Mapping):children=[v for kv in x.items() for v in kv]
    elif isinstance(x,(list,tuple)):children=x
    else:children=[getattr(x,k) for k in getattr(type(x),'__slots__',()) if hasattr(x,k)]
    return total+sum(size(v,seen) for v in children)

results=[]
for live in (False,True):
    conf=ExperimentConfig('review-live',1,100000,WorldConfig(0,1,1,0,1),AgentConfig(1,10,100000)) if live else dataclasses.replace(load_config('examples/v0.1/s2-resource-world.yaml'),max_ticks=100000)
    counts=dict(applied=0,harvested=0,metabolism_calls=0,metabolism_units=0,death_transitions=0)
    apply,metabolism,death=World.apply,World.metabolize_and_age,World.settle_death
    def pa(w,i):
        r=apply(w,i);counts['applied']+=r.status=='applied';counts['harvested']+=r.harvested;return r
    def pm(w,a):
        before=a.energy;metabolism(w,a);counts['metabolism_calls']+=1;counts['metabolism_units']+=before-a.energy
    def pd(w,a):
        before=a.alive;death(w,a);counts['death_transitions']+=before and not a.alive
    sim=Simulation(conf);obs=[];start=time.perf_counter();tracemalloc.start()
    with patch.object(World,'apply',pa),patch.object(World,'metabolize_and_age',pm),patch.object(World,'settle_death',pd):
        for tick in range(1,100001):
            sim.step();s=sim.snapshot();l=s['ledger'];agents=s['agents']
            living=sum(a['energy'] for a in agents if a['alive'])
            assert conf.world.initial_resource+conf.agent.initial_count*conf.agent.initial_energy+tick*conf.world.resource_inflow_per_tick==s['world_resource']+living+l['cumulative_dissipated_energy']
            assert s['tick']==tick and l['cumulative_external_inflow']==tick*conf.world.resource_inflow_per_tick
            if live:
                assert counts['applied']==counts['harvested']==counts['metabolism_calls']==counts['metabolism_units']==tick
                assert agents[0]==dict(id=0,energy=10 if tick<100000 else 0,age=tick,alive=tick<100000)
            else:
                assert all(a['age']==min(tick,20) and a['alive']==(tick<20) for a in agents)
                assert counts['applied']==counts['metabolism_calls']==3*min(tick,20)
            if tick in (1000,10000,100000):
                gc.collect();current,peak=tracemalloc.get_traced_memory()
                obs.append(dict(tick=tick,retained_bytes=size(sim),traced_current=current,traced_peak=peak,world_agents=len(sim.world.agents),snapshot_agents=len(agents)))
    tracemalloc.stop()
    assert counts['death_transitions']==conf.agent.initial_count
    assert max(o['retained_bytes'] for o in obs)-min(o['retained_bytes'] for o in obs)<4096
    assert obs[-1]['traced_current']-obs[0]['traced_current']<65536
    summary=build_summary(sim);assert summary['state']['world_resource']==(10 if live else 1000010)
    row=dict(scene='live' if live else 'example',seconds=time.perf_counter()-start,counts=counts,memory=obs,summary=summary)
    results.append(row);print(json.dumps(row),flush=True)
(OUT/'independent-longrun.json').write_text(json.dumps(results,indent=2)+'\n')
