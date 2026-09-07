from dataclasses import FrozenInstanceError

import pytest
import yaml

from minigenesis.config import AgentConfig, ConfigError, ExperimentConfig, WorldConfig, load_config

WORLD = dict(initial_resource=100, resource_inflow_per_tick=10, harvest_amount=4, action_cost=1, metabolism_cost=1)
AGENT = dict(initial_count=3, initial_energy=10, max_age=20)


@pytest.mark.parametrize('section,field,low,high', [
    *[('world', key, 0, 1000000) for key in WORLD],
    ('agent', 'initial_count', 1, 1000),
    ('agent', 'initial_energy', 1, 1000000),
    ('agent', 'max_age', 1, 100000),
    ('experiment', 'max_ticks', 1, 100000),
])
@pytest.mark.parametrize('case', ['min', 'max', 'below', 'above', 'bool', 'float', 'string', 'null'])
def test_s2_field_boundaries(tmp_path, section, field, low, high, case):
    doc = dict(experiment=dict(name='test', seed=1, max_ticks=1), world=WORLD.copy(), agent={**AGENT, 'initial_count': 1})
    values = dict(min=low, max=high, below=low-1, above=high+1, bool=True, float=1.0, string='1', null=None)
    doc[section][field] = values[case]
    path = tmp_path / 'config.yaml'
    path.write_text(yaml.safe_dump(doc))
    if case in ('min', 'max'):
        assert load_config(path)
    else:
        with pytest.raises(ConfigError):
            load_config(path)


@pytest.mark.parametrize('section', ['world', 'agent'])
@pytest.mark.parametrize('kind', ['missing_section', 'missing_field', 'unknown_field', 'duplicate', 'tag', 'null'])
def test_s2_strict_sections(tmp_path, section, kind):
    doc = dict(experiment=dict(name='test', seed=1, max_ticks=1), world=WORLD.copy(), agent=AGENT.copy())
    field = next(iter(doc[section]))
    if kind == 'missing_section':
        del doc[section]
    elif kind == 'missing_field':
        del doc[section][field]
    elif kind == 'unknown_field':
        doc[section]['extra'] = 1
    elif kind == 'null':
        doc[section] = None
    body = yaml.safe_dump(doc, sort_keys=False)
    if kind == 'duplicate':
        body = body.replace(f'{section}:\n', f'{section}:\n  {field}: 1\n')
    if kind == 'tag':
        body = body.replace(f'{section}:\n', f'{section}: !!python/object:builtins.object\n')
    path = tmp_path / 'config.yaml'
    path.write_text(body)
    with pytest.raises(ConfigError):
        load_config(path)


def test_s2_direct_pair_budget_and_immutability():
    w, a = WorldConfig(**WORLD), AgentConfig(**AGENT)
    for kwargs in [dict(world=w), dict(agent=a), dict(world={}, agent={})]:
        with pytest.raises(ConfigError):
            ExperimentConfig('test', 1, 1, **kwargs)
    assert ExperimentConfig('test', 1, 100000, w, AgentConfig(10, 1, 1))
    with pytest.raises(ConfigError):
        ExperimentConfig('test', 1, 100000, w, AgentConfig(11, 1, 1))
    with pytest.raises(FrozenInstanceError):
        w.action_cost = 3
    for cls, values in [(WorldConfig, {**WORLD, 'action_cost': True}), (AgentConfig, {**AGENT, 'initial_count': 1001})]:
        with pytest.raises(ConfigError):
            cls(**values)


@pytest.mark.parametrize('section,field,value', [('agent','initial_count',1001),('experiment','max_ticks',100001),('agent','initial_count',1000)])
def test_s2_oversize_fails_before_world_allocation(tmp_path, monkeypatch, capsys, section, field, value):
    from minigenesis import cli
    import minigenesis.simulation as simulation
    doc = dict(experiment=dict(name='test',seed=1,max_ticks=100000),world=WORLD.copy(),agent=AGENT.copy())
    doc[section][field] = value
    path = tmp_path / 'oversize.yaml'
    path.write_text(yaml.safe_dump(doc))
    def forbidden(*args):
        raise AssertionError('World must not be allocated')
    monkeypatch.setattr(simulation,'World',forbidden)
    assert cli.main(['--config',str(path),'--output-format','json']) == 2
    captured = capsys.readouterr()
    assert captured.out == '' and 'error:' in captured.err


@pytest.mark.parametrize('field,value', [('name',' '),('name',False),('seed',True),('seed',-1),('seed',1.0),('seed','1'),('seed',None),('max_ticks',0),('max_ticks',True)])
def test_s2_direct_experiment_validation(field,value):
    kwargs = dict(name='test',seed=1,max_ticks=1,world=WorldConfig(**WORLD),agent=AgentConfig(**AGENT))
    kwargs[field] = value
    with pytest.raises(ConfigError):
        ExperimentConfig(**kwargs)
