"""The lengths of a physical layout given instead of derived from its scale (FresnelLayout font_min, font_max, border,
margin; control S of Q2, docs/exp_resolucao/CADERNO_CURVA.md: the laws of SmallLayout in physical units). Fast,
CPU, no data."""
import json

import numpy as np
import pytest

from holo_openset.sim.generate import generate, layout_of, make_layout
from holo_openset.sim.physics import Physics
from holo_openset.sim.scene import FresnelLayout, SmallLayout, camera, make_scene
from test_fill import BEFORE, MID, TINY, digest

SMALL = dict(font_min=16, font_max=48, border=6, margin=4)


@pytest.mark.parametrize('key', list(BEFORE))
def test_without_given_lengths_the_scenes_are_the_ones_of_before(key):
    which, seed = key
    p = Physics().replace(**(TINY if which == 'tiny' else MID))
    for lay in (FresnelLayout(), FresnelLayout(lengths_given={}), make_layout('fresnel', FresnelLayout().params())):
        sc = make_scene(seed, p, lay=lay)
        sc['sensor_dust'] = camera(7, p, lay)['dust']
        assert digest(sc) == BEFORE[key]
    assert 'lengths_given' not in FresnelLayout().params()
    # a physics.json of before records the derived lengths: they are not read as given
    assert make_layout('fresnel', FresnelLayout(scale=0.5).params()).lengths_given == {}


def test_the_given_lengths_reach_the_scene():
    lay = FresnelLayout(scale=1, factor=8, **SMALL)
    assert (lay.font_min, lay.font_max, lay.border, lay.margin) == (16, 48, 6, 4)
    assert (lay.font_min, lay.font_max, lay.border, lay.margin) == (SmallLayout.font_min, SmallLayout.font_max,
                                                                    SmallLayout.border, SmallLayout.margin)
    assert lay.params()['lengths_given'] == {k: float(v) for k, v in SMALL.items()}
    again = make_layout('fresnel', json.loads(json.dumps(lay.params())))   # through physics.json
    assert again.lengths_given == lay.lengths_given and again.font_max == 48
    p = Physics().replace(window=(256, 256), margin=160, reach=96, z0=2.0e-3)
    m0, (h, w) = p.margin, p.window
    sizes = []
    for seed in range(17_000_000, 17_000_012):
        sc = make_scene(seed, p, lay=lay)
        sizes += [r['font_size'] for r in sc['rows']]
        for r in sc['rows']:   # the border of the window (ink box, to 1/factor px)
            assert r['bx0'] >= 6 - 1 / 8 and r['by0'] >= 6 - 1 / 8
            assert r['bx1'] <= w - 6 + 1 / 8 and r['by1'] <= h - 6 + 1 / 8
        boxes = []
        for o in sc['objects']:
            mh, mw = o['mask'].shape
            boxes.append((o['x'], o['y'], o['x'] + mw, o['y'] + mh))
        boxes = np.array(boxes)
        g = 4
        for k in range(len(boxes)):   # the spacing rule between every two letters
            a, b = boxes[k], boxes[k + 1:]
            sep = (b[:, 0] - g >= a[2] + g) | (a[0] - g >= b[:, 2] + g) | (b[:, 1] - g >= a[3] + g) | \
                  (a[1] - g >= b[:, 3] + g)
            assert sep.all()
    sizes = np.array(sizes)
    assert len(sizes) > 15 and sizes.min() >= 16 and sizes.max() <= 48 and sizes.max() - sizes.min() > 20


def test_a_set_with_given_lengths_records_them(tmp_path):
    lp = dict(scale=1, factor=4, letters_mean=8, lengths_given=SMALL)
    generate(tmp_path / 's', phys=dict(TINY, z0=2.0e-3, oversample=2), n_images=2, per_session=2, workers=1,
             layout='fresnel', layout_params=lp, log=lambda *a: None)
    cfg = json.load(open(tmp_path / 's' / 'physics.json'))
    assert cfg['layout_params']['lengths_given'] == {k: float(v) for k, v in SMALL.items()}
    lay = layout_of(cfg)
    assert (lay.font_min, lay.font_max, lay.border, lay.margin, lay.factor, lay.scale) == (16, 48, 6, 4, 4, 1)
