"""The filler letters of a physical layout (FresnelLayout fill_mean, control C of the pilot at 1.0 mm,
docs/exp_resolucao/CADERNO_PILOTO_1MM.md P2): off, the scene is the one of before the option existed; on, the scene
keeps every letter, dust particle and annotation and only gains un-annotated letters, never overlapping, in the
number asked. Fast, CPU, no data."""
import hashlib
import math

import numpy as np
import pandas as pd
import pytest

from holo_openset.sim.generate import generate
from holo_openset.sim.physics import Physics
from holo_openset.sim.scene import TILE, FresnelLayout, camera, make_scene

TINY = dict(window=(96, 96), margin=64, reach=32, z0=1.0e-3, dust_density=40.0, sensor_dust_density=60.0)
MID = dict(window=(256, 256), margin=160, reach=96, z0=1.0e-3)
# sha256 of the scenes (every object, dust particle, sensor dust and annotation row) made by the code BEFORE the
# filler option was added (commit 4a49578), with the same digest as `digest` below
BEFORE = {('tiny', 17_000_005): '6e524b60ff30aa590290c9a8c0fa11f5c51f11ad8bb8bbc05403b3f2c778bded',
          ('tiny', 17_000_625): '557e9395a4ea4526e59d33d376ccede853c2f5a163d932afff91ba1218af4c42',
          ('mid', 17_000_000): '395b153a2d659e3093d74fcc376ce66d95a0964c9b40b33fc9625b683c1abbaf',
          ('mid', 17_000_001): '69a70dc1783740c6a75c8c8227ed2b717952db630e4367237a7a5bfa04bcd1a3'}


def digest(sc, kinds=None):
    h = hashlib.sha256()
    for o in sc['objects'] + sc['dust'] + sc.get('sensor_dust', []):
        if kinds and o['kind'] not in kinds:
            continue
        h.update(np.ascontiguousarray(o['master']).tobytes())
        h.update(repr([o[k] for k in ('mx', 'my', 'factor', 'kind', 'absorption', 'phase', 'depth')]
                      + [o.get('classe')]).encode())
    h.update(repr(sc['rows']).encode())
    return h.hexdigest()


def scene(which, seed, **lay):
    p = Physics().replace(**(TINY if which == 'tiny' else MID))
    sc = make_scene(seed, p, lay=FresnelLayout(**lay))
    sc['sensor_dust'] = camera(7, p, FresnelLayout(**lay))['dust']
    return sc, p


@pytest.mark.parametrize('key', list(BEFORE))
def test_without_fillers_the_scene_is_the_one_of_before(key):
    for lay in ({}, dict(fill_mean=0)):
        sc, _ = scene(*key, **lay)
        assert digest(sc) == BEFORE[key] and 'fill' not in sc
    assert 'fill_mean' not in FresnelLayout().params() and FresnelLayout(fill_mean=154).params()['fill_mean'] == 154


def box(o):
    h, w = o['mask'].shape
    return o['x'], o['y'], o['x'] + w, o['y'] + h


@pytest.mark.parametrize('seed', [17_000_000, 17_000_001])
def test_the_fillers_are_the_only_change_and_never_overlap(seed):
    sc0, p = scene('mid', seed)
    sc, _ = scene('mid', seed, fill_mean=154)
    n = len(sc0['objects'])
    # everything of the scene without fillers is there, unchanged and in the same order; the fillers come after
    assert digest(dict(sc, objects=sc['objects'][:n])) == BEFORE[('mid', seed)] == digest(sc0)
    assert sc['rows'] == sc0['rows']
    fillers = sc['objects'][n:]
    assert fillers and {o['kind'] for o in fillers} == {'filler'}
    assert sc['fill']['placed_window'] + sc['fill']['placed_band'] == len(fillers)
    m0, (h, w) = p.margin, p.window
    lay = FresnelLayout(fill_mean=154)
    g = max(1, round(lay.margin))
    inside = 0
    for o in fillers:   # where the letters of the scene go: in the window with its border, or off the window
        x0, y0, x1, y1 = box(o)
        if m0 <= x0 and x1 <= m0 + w and m0 <= y0 and y1 <= m0 + h:
            inside += 1
            assert o['mx'] / lay.factor >= m0 + lay.border - 1e-9 and o['my'] / lay.factor >= m0 + lay.border - 1e-9
        else:
            assert not (x1 + g > m0 and x0 - g < m0 + w and y1 + g > m0 and y0 - g < m0 + h)
        assert 0 <= o['absorption'] <= 1 and abs(o['depth']) <= p.depth_max and o['classe'].isupper()
    assert inside == sc['fill']['placed_window']
    # the spacing rule of the layout between every two letters (annotated, around the window, fillers)
    boxes = np.array([box(o) for o in sc['objects']])
    for k in range(len(boxes)):
        a = boxes[k]
        b = boxes[k + 1:]
        sep = (b[:, 0] - g >= a[2] + g) | (a[0] - g >= b[:, 2] + g) | (b[:, 1] - g >= a[3] + g) | \
              (a[1] - g >= b[:, 3] + g)
        assert sep.all(), k


def test_the_number_of_letters_per_window():
    """Over 40 scenes, letters in the window (annotated + fillers) and letters in the band (around the window +
    fillers) have the Poisson means of fill_mean per 640 x 640 window, within 4 standard errors."""
    p = Physics().replace(window=(128, 128), margin=96, reach=64, z0=1.0e-3, dust_density=0.0)
    lay = FresnelLayout(fill_mean=154)
    lam_w = 154 * 128 * 128 / TILE
    lam_b = 154 * ((128 + 128) ** 2 - 128 * 128) / TILE
    win, band = [], []
    for k in range(40):
        sc = make_scene(17_000_000 + k, p, lay=lay)
        f = sc['fill']
        assert f['placed_window'] == f['target_window'] and f['placed_band'] == f['target_band']
        win.append(len(sc['rows']) + f['placed_window'])
        band.append(sum(o['kind'] == 'outside' for o in sc['objects']) + f['placed_band'])
    assert abs(np.mean(win) - lam_w) < 4 * math.sqrt(lam_w / 40)
    assert abs(np.mean(band) - lam_b) < 4 * math.sqrt(lam_b / 40)


def test_a_set_with_fillers_has_the_annotations_of_the_set_without(tmp_path):
    """generate() with fill_mean: the same annotations, YOLO labels, ground-truth maps, dust table and sessions as the
    same set without fillers; only the holograms differ, and metadata counts the fillers."""
    phys = dict(TINY, oversample=2, depth_std=2.6e-6, depth_max=7.8e-6)
    kw = dict(n_images=4, per_session=2, workers=1, layout='fresnel', log=lambda *a: None)
    generate(tmp_path / 'a', phys=phys, layout_params=dict(letters_mean=8), **kw)
    generate(tmp_path / 'b', phys=phys, layout_params=dict(letters_mean=8, fill_mean=154), **kw)
    a, b = tmp_path / 'a', tmp_path / 'b'
    for name in ['annotations.csv', 'dust.csv', 'sessions.csv', 'backgrounds.npy']:
        assert (a / name).read_bytes() == (b / name).read_bytes(), name
    for d in ['labels', 'objects']:
        files = sorted(p.name for p in (a / d).iterdir())
        assert files == sorted(p.name for p in (b / d).iterdir())
        assert all((a / d / x).read_bytes() == (b / d / x).read_bytes() for x in files), d
    ma, mb = pd.read_csv(a / 'metadata.csv'), pd.read_csv(b / 'metadata.csv')
    assert ma.equals(mb[ma.columns]) and 'n_fill_window' not in ma and (mb.n_fill_window > 0).all()
    assert not np.array_equal(np.load(a / 'holograms.npy'), np.load(b / 'holograms.npy'))
