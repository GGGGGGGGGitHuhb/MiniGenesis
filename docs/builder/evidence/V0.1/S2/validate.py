"""Reproducible Builder CLI, fault, ledger and deterministic evidence harness."""
from dataclasses import replace
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

from minigenesis.config import load_config
from minigenesis.rng import RNGContext
from minigenesis.scheduler import schedule
from minigenesis.simulation import Simulation
from minigenesis.summary import _plain

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
assert ROOT == Path.cwd()
print('platform', platform.platform())
print('python', sys.version)
print('executable',sys.executable)
import minigenesis
print('package',minigenesis.__file__)
for package in ['pip','PyYAML','pytest','setuptools','minigenesis']:
    try:
        print(package,importlib.metadata.version(package))
    except importlib.metadata.PackageNotFoundError:
        print(package,'isolated build dependency only')


def command(name,args):
    print('COMMAND', [sys.executable,*args])
    result = subprocess.run([sys.executable,*args],capture_output=True)
    (OUT/f'{name}.stdout').write_bytes(result.stdout)
    (OUT/f'{name}.stderr').write_bytes(result.stderr)
    print(name,'exit',result.returncode,'stdout_sha256',hashlib.sha256(result.stdout).hexdigest())
    if result.stderr:
        print('stderr',result.stderr.decode())
    return result

for stage in ['s1-baseline','s2-resource-world']:
    args = ['-m','minigenesis','--config',f'examples/v0.1/{stage}.yaml','--output-format','json']
    first, second = command(stage+'-a',args), command(stage+'-b',args)
    assert first.returncode == second.returncode == 0 and first.stderr == second.stderr == b''
    assert first.stdout == second.stdout and first.stdout.endswith(b'\n') and not first.stdout.endswith(b'\n\n')
    summary = json.loads(first.stdout)
    digest = summary.pop('digest')
    independent = 'sha256:' + hashlib.sha256(json.dumps(summary,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    assert digest == independent
    if stage=='s1-baseline':
        assert hashlib.sha256(first.stdout).hexdigest() == '4de55827ebbd9719a6bc42d8f426cf72307a0172603c3ba0090c2bbe166f6b34'
    print('identical bytes; independent digest',digest)
    print('JSON',first.stdout.decode().strip())
text = command('s2-text',['-m','minigenesis','--config','examples/v0.1/s2-resource-world.yaml'])
assert text.returncode == 0 and b'resource=310' in text.stdout
fault_code = '''from minigenesis.world import World
from minigenesis.cli import main
original = World.inject
def corrupt(world):
    original(world)
    world.resource += 1
World.inject = corrupt
raise SystemExit(main(['--config','examples/v0.1/s2-resource-world.yaml','--output-format','json']))
'''
fault = command('ledger-fault',['-c',fault_code])
assert fault.returncode == 1 and fault.stdout == b'' and b'tick 1' in fault.stderr and b'left=' in fault.stderr and b'right=' in fault.stderr
cfg = load_config('examples/v0.1/s2-resource-world.yaml')
traces = []
for seed in [1,7,1]:
    sim = Simulation(replace(cfg,seed=seed,max_ticks=4,world=replace(cfg.world,initial_resource=1,resource_inflow_per_tick=1,harvest_amount=1)))
    probe = RNGContext(seed)
    trace = []
    for tick in range(4):
        order = [a.id for a in schedule(sim.world.agents.values(),probe)]
        sim.step()
        state = _plain(sim.snapshot())
        ledger = state['ledger']
        assert ledger['initial_resource']+ledger['initial_agent_energy']+ledger['cumulative_external_inflow'] == state['world_resource']+sum(a['energy'] for a in state['agents'] if a['alive'])+ledger['cumulative_dissipated_energy']
        trace.append(dict(order=order,state=state))
    traces.append(trace)
assert traces[0] == traces[2] and traces[0] != traces[1]
(OUT/'competition-trajectories.json').write_text(json.dumps(traces,indent=2)+'\n')
print('competition orders seed1', [t['order'] for t in traces[0]],'seed7',[t['order'] for t in traces[1]],'A-B-A equal',traces[0]==traces[2])
print('All CLI, digest, fault and trajectory assertions passed')
