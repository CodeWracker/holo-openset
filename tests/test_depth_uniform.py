"""The uniform depth law over a channel (Physics.depth_uniform, Q1 of docs/exp_resolucao/CADERNO_CURVA.md): off, every
scene is the one of before; on, the same scenes with only the depths changed, each depth uniform in +-depth_uniform,
mapped from the same normal draw. Fast, CPU, no data."""
import math
import random

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from holo_openset.sim.generate import generate
from holo_openset.sim.physics import Physics, physics_dict
from holo_openset.sim.scene import FresnelLayout, Layout, camera, make_scene, material
from test_fill import BEFORE, MID, TINY, digest

U = 25e-6


@pytest.mark.parametrize('key', list(BEFORE))
def test_off_the_scenes_are_the_ones_of_before(key):
    which, seed = key
    p = Physics().replace(**(TINY if which == 'tiny' else MID), depth_uniform=0.0)
    sc = make_scene(seed, p, lay=FresnelLayout())
    sc['sensor_dust'] = camera(7, p, FresnelLayout())['dust']
    assert digest(sc) == BEFORE[key]
    assert 'depth_uniform' not in physics_dict(p) and physics_dict(p.replace(depth_uniform=U))['depth_uniform'] == U


def _strip(o):
    return {k: (v.tobytes() if isinstance(v, np.ndarray) else v) for k, v in o.items() if k != 'depth'}


@pytest.mark.parametrize('layout', ['fresnel', 'default'])
def test_on_only_the_depths_move_and_they_follow_the_same_draw(layout):
    lay = FresnelLayout(fill_mean=154) if layout == 'fresnel' else Layout
    p = Physics().replace(**MID, depth_std=2.6e-6, depth_max=7.8e-6)
    for seed in (17_000_000, 17_000_001):
        a = make_scene(seed, p, lay=lay)
        b = make_scene(seed, p.replace(depth_uniform=U), lay=lay)
        assert [{k: v for k, v in r.items() if k != 'depth'} for r in a['rows']] == \
            [{k: v for k, v in r.items() if k != 'depth'} for r in b['rows']]
        assert len(a['objects']) == len(b['objects']) and len(a['dust']) == len(b['dust'])
        kinds = set()
        for oa, ob in zip(a['objects'], b['objects']):
            assert _strip(oa) == _strip(ob)
            assert abs(ob['depth']) <= U
            g = oa['depth'] / 2.6e-6
            if abs(g) < 3 - 1e-9:   # not clipped by depth_max: the same g, mapped by erf
                assert ob['depth'] == pytest.approx(U * math.erf(g / math.sqrt(2)), rel=1e-9, abs=1e-15)
            kinds.add(oa['kind'])
        assert kinds >= ({'letter', 'outside', 'filler'} if layout == 'fresnel' else {'letter', 'outside'})
        for da, db in zip(a['dust'], b['dust']):   # the dust stays on the planes of the glass
            assert _strip(da) == _strip(db) and da['depth'] == db['depth']
        assert [r['depth'] for r in b['rows']] == [o['depth'] for o in b['objects'] if o['kind'] == 'letter']


def test_the_depths_are_uniform():
    p = Physics().replace(depth_uniform=U)
    rng = random.Random(0)
    d = np.array([material(rng, p)['depth'] for _ in range(5000)])
    assert np.abs(d).max() <= U
    assert stats.kstest(d / U, 'uniform', args=(-1, 2)).pvalue > 0.01
    assert d.std() == pytest.approx(U / math.sqrt(3), rel=0.03)   # 14.4 um


def test_a_set_with_the_uniform_law(tmp_path):
    kw = dict(n_images=4, per_session=2, workers=1, layout='fresnel', log=lambda *a: None)
    phys = dict(TINY, oversample=2, depth_std=2.6e-6, depth_max=7.8e-6)
    generate(tmp_path / 'a', phys=phys, layout_params=dict(letters_mean=8), **kw)
    generate(tmp_path / 'b', phys=dict(phys, depth_uniform=U), layout_params=dict(letters_mean=8), **kw)
    A, B = pd.read_csv(tmp_path / 'a' / 'annotations.csv'), pd.read_csv(tmp_path / 'b' / 'annotations.csv')
    same = [c for c in A.columns if c not in ('depth', 'z')]
    assert A[same].equals(B[same]) and (B.depth.abs() <= U).all() and not A.depth.equals(B.depth)
    for name in ['dust.csv', 'sessions.csv', 'backgrounds.npy']:
        assert (tmp_path / 'a' / name).read_bytes() == (tmp_path / 'b' / name).read_bytes(), name
    import json
    ja, jb = (json.load(open(tmp_path / x / 'physics.json'))['physics'] for x in 'ab')
    assert 'depth_uniform' not in ja and jb.pop('depth_uniform') == U and ja == jb
