"""Athena independent acceptance: hand oracles, separate scalar model, real CLI."""
import dataclasses, gc, hashlib, json, platform, random, subprocess, sys, time, tracemalloc
from pathlib import Path
from collections.abc import Mapping
from unittest.mock import patch
import yaml, pytest, minigenesis
from minigenesis.config import AgentConfig, WorldConfig, ExperimentConfig, load_config
from minigenesis.simulation import Simulation
from minigenesis.summary import build_summary, canonical_output_bytes
from minigenesis.cli import execute
from minigenesis.world import World
from minigenesis.agent import Agent
import minigenesis.simulation as pipeline
OUT=Path(__file__).parent

def plain(x):
    if isinstance(x,Mapping): return {k:plain(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)): return [plain(v) for v in x]
    return x

def emit(name,data):
    (OUT/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def cfg(name='review',seed=11,ticks=3,r=7,i=2,h=3,c=2,m=1,n=1,e=6,a=10):
    return ExperimentConfig(name,seed,ticks,WorldConfig(r,i,h,c,m),AgentConfig(n,e,a))

def balance(s):
    l=s['ledger']; live=sum(a['energy'] for a in s['agents'] if a['alive'])
    assert s['living_agent_energy']==live
    assert l['initial_resource']+l['initial_agent_energy']+l['cumulative_external_inflow']==s['world_resource']+live+l['cumulative_dissipated_energy']
    assert all(type(a['energy']) is int and a['energy']>=0 for a in s['agents'])

# Hand-calculated tuples: resource,energy,age,inflow,dissipation,alive.
rows=[
 ('normal',cfg(ticks=2),[(7,6,0,0,0,True),(6,6,1,2,3,True),(5,6,2,4,6,True)]),
 ('scarce',cfg(ticks=2,r=1,i=0),[(1,6,0,0,0,True),(0,4,1,0,3,True),(0,3,2,0,4,True)]),
 ('reject',cfg(ticks=2,r=5,i=0,c=7),[(5,6,0,0,0,True),(5,5,1,0,1,True),(5,4,2,0,2,True)]),
 ('metabolic',cfg(ticks=2,r=0,i=0,e=2,m=3),[(0,2,0,0,0,True),(0,0,1,0,2,False),(0,0,1,0,2,False)]),
 ('age',cfg(ticks=2,r=2,i=1,c=1,m=2,e=4,a=1),[(2,4,0,0,0,True),(4,0,1,1,3,False),(5,0,1,2,3,False)]),
 ('simultaneous',cfg(ticks=2,r=0,i=0,e=2,m=2,a=1),[(0,2,0,0,0,True),(0,0,1,0,2,False),(0,0,1,0,2,False)])]
hand=[]
for name,conf,expected in rows:
    sim=Simulation(conf); actual=[]
    for t,want in enumerate(expected):
        if t: sim.step()
        s=sim.snapshot(); balance(s); a=s['agents'][0]; l=s['ledger']
        got=(s['world_resource'],a['energy'],a['age'],l['cumulative_external_inflow'],l['cumulative_dissipated_energy'],a['alive'])
        assert got==want,(name,t,got,want)
        actual.append(got)
    hand.append(dict(name=name,config=dataclasses.asdict(conf),expected=expected,actual=actual))
emit('hand-ledgers',hand)

# Independent scalar reference model uses stdlib RNG and arrays, no product rules.
def oracle(conf):
    w=conf.world; ac=conf.agent; r=w.initial_resource; es=[ac.initial_energy]*ac.initial_count; ages=[0]*len(es); live=[True]*len(es); diss=0; rng=random.Random(conf.seed)
    for tick in range(1,conf.max_ticks+1):
        r+=w.resource_inflow_per_tick
        order=[k for k in range(len(es)) if live[k]]
        if len(order)>1:rng.shuffle(order)
        harvest=r>0
        for k in order:
            if harvest and es[k]>=w.action_cost:
                es[k]-=w.action_cost; diss+=w.action_cost; take=min(w.harvest_amount,r); r-=take; es[k]+=take
        for k in order:
            cost=min(es[k],w.metabolism_cost); es[k]-=cost; diss+=cost; ages[k]+=1
        for k in order:
            if es[k]==0 or ages[k]>=ac.max_age: r+=es[k]; es[k]=0; live[k]=False
        yield order,(r,es.copy(),ages.copy(),live.copy(),diss),rng.getstate()

def trace(conf,reverse=False):
    sim=Simulation(conf)
    if reverse:sim.world.agents=dict(reversed(list(sim.world.agents.items())))
    result=[]; original=pipeline.schedule
    for expected_order,expected,rng in oracle(conf):
        orders=[]
        def spy(agents,context):
            ordered=original(agents,context);orders.extend(a.id for a in ordered);return ordered
        before=sim.snapshot(); oldrng=sim.rng.getstate()
        assert sim.snapshot() is before and sim.rng.getstate()==oldrng
        with patch.object(pipeline,'schedule',spy):sim.step()
        s=sim.snapshot(); balance(s)
        actual=(s['world_resource'],[a['energy'] for a in s['agents']],[a['age'] for a in s['agents']],[a['alive'] for a in s['agents']],s['ledger']['cumulative_dissipated_energy'])
        assert actual==expected and orders==expected_order and sim.rng.getstate()==rng
        assert before['tick']==sim.tick-1
        result.append(dict(order=orders,state=plain(s)))
    return result,canonical_output_bytes(build_summary(sim)).decode()
conf=cfg(ticks=6,r=1,i=1,h=1,c=0,m=0,n=3)
global_rng=random.getstate(); first=trace(conf); second=trace(dataclasses.replace(conf,seed=12)); assert first!=second
assert first==trace(conf)==trace(conf,True)
s1=ExperimentConfig('S1 mixed',4,8); a1=canonical_output_bytes(execute(s1)); trace(conf); assert a1==canonical_output_bytes(execute(s1)); assert first==trace(conf)
assert global_rng==random.getstate()
emit('trajectories',dict(seed11=first,seed12=second,aba_equal=True,reversed_equal=True,mixed_equal=True))
# Wide finite deterministic matrix, not random property sampling.
for j in range(120):trace(cfg(seed=j,ticks=9,r=j%8,i=j%3,h=j%5,c=j%4,m=(j//4)%4,n=1+j%4,e=1+j%7,a=1+j%10))

# True CLI byte oracles assembled from specified constants, not parsed key order.
def canon(x):return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()
def expected_output(s2):
    x=dict(schema_version='minigenesis.summary.v2' if s2 else 'minigenesis.summary.v1',experiment_name='s2-resource-world' if s2 else 's1-baseline',seed=1,rng_implementation='python.random.Random/MT19937',requested_ticks=30 if s2 else 10,completed_ticks=30 if s2 else 10,status='completed')
    if s2:
        x['config']=dict(world=dict(initial_resource=100,resource_inflow_per_tick=10,harvest_amount=4,action_cost=1,metabolism_cost=1),agent=dict(initial_count=3,initial_energy=10,max_age=20))
        x['state']=dict(tick=30,world_resource=310,living_count=0,dead_count=3,living_agent_energy=0,ledger=dict(initial_resource=100,initial_agent_energy=30,cumulative_external_inflow=300,cumulative_dissipated_energy=120,valid=True),agents=[dict(id=i,energy=0,age=20,alive=False) for i in range(3)])
    x['digest']='sha256:'+hashlib.sha256(canon(x)).hexdigest();return canon(x)+b'\n'
commands=[]
def child(label,args,code):
    p=subprocess.run([sys.executable,*args],capture_output=True)
    (OUT/(label+'.stdout')).write_bytes(p.stdout);(OUT/(label+'.stderr')).write_bytes(p.stderr)
    commands.append(dict(label=label,argv=[sys.executable,*args],exit=p.returncode,stdout_sha256=hashlib.sha256(p.stdout).hexdigest()))
    assert p.returncode==code,(label,p.stderr)
    return p
for s2 in (False,True):
    example='examples/v0.1/'+('s2-resource-world' if s2 else 's1-baseline')+'.yaml'
    for repeat in (1,2):
        p=child(f'cli-v{2 if s2 else 1}-{repeat}',['-m','minigenesis','--config',example,'--output-format','json'],0)
        assert p.stdout==expected_output(s2) and not p.stderr
p=child('cli-text',['-m','minigenesis','--config','examples/v0.1/s2-resource-world.yaml'],0)
assert all(v in p.stdout for v in (b'30/30',b'resource=310',b'living=0',b'dead=3',b'living_energy=0',b'ledger_valid=True',b'sha256:'))
# Fail at tick 2 after one successful publication; no rollback or recovery.
sim=Simulation(cfg());sim.step();previous=sim.snapshot();sim.world.ledger.cumulative_external_inflow+=1
try:sim.step();raise AssertionError('fault ignored')
except RuntimeError as e:error=str(e)
assert sim.failed and sim.tick==1 and sim.snapshot() is previous
for op in (sim.step,sim.run,lambda:build_summary(sim)):
    try:op();raise AssertionError('failed run accepted')
    except (RuntimeError,ValueError):pass
emit('fault-latch',dict(error=error,tick=sim.tick,failed=sim.failed,snapshot_unchanged=sim.snapshot() is previous))
faultcode='''from minigenesis.world import World
from minigenesis.cli import main
original=World.inject
def fault(self):
 original(self)
 self.ledger.cumulative_external_inflow+=1
World.inject=fault
raise SystemExit(main(['--config','examples/v0.1/s2-resource-world.yaml','--output-format','json']))
'''
p=child('cli-ledger-fault',['-c',faultcode],1); assert p.stdout==b'' and all(s in p.stderr for s in (b'tick 1',b'initial_resource',b'initial_agent_energy',b'cumulative_external_inflow',b'world_resource',b'living_agent_energy',b'cumulative_dissipated_energy',b'left=',b'right='))
emit('commands',commands)
emit('environment',dict(python=sys.version,executable=sys.executable,platform=platform.platform(),pytest=pytest.__version__,yaml=yaml.__version__,module=minigenesis.__file__))
print('PASS: six hand ledgers; 120 scalar-model trajectories; actual scheduler comparison; v1/v2 CLI exact bytes; mixed isolation; fault CLI/latch',flush=True)
