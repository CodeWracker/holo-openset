"""The oversampled recording (Physics.oversample) and the scenes in physical units of the pilot at 1.0 mm
(docs/exp_resolucao/CADERNO_PILOTO_1MM.md). Fast, CPU, no data."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

from holo_openset.sim.letters import FONTS, letter_master
from holo_openset.sim.physics import Physics, fine_intensity, sample_mask, sensor_intensity
from holo_openset.sim.scene import FresnelLayout, camera, make_scene, physical_object, session

DEV = torch.device('cpu')
HERE = Path(__file__).resolve().parent
TINY = dict(window=(96, 96), margin=64, reach=32, z0=1.0e-3, dust_density=40.0, sensor_dust_density=60.0)


def rel(a, b, ref):
    return float((a - b).std() / ref.std())


def test_oversample_1_is_exactly_the_simulator_of_the_paper(tmp_path):
    """sensor_intensity, record, the blank frame and a whole small set made by generate(), against the arrays stored
    before the oversampled path existed (tests/fixtures/make_native_reference.py)."""
    sys.path.insert(0, str(HERE / 'fixtures'))
    try:
        import make_native_reference as M
    finally:
        sys.path.pop(0)
    ref = np.load(HERE / 'fixtures' / 'native_reference.npz')
    a, ann = M.arrays(tmp_path)
    for k, v in a.items():
        assert np.array_equal(np.asarray(v), ref[k]), k
    assert ann == str(ref['annotations_sha256'])
    cfg = json.load(open(tmp_path / 'set' / 'physics.json'))   # the file of a set of the paper keeps its keys
    assert 'oversample' not in cfg['physics'] and 'layout_params' not in cfg


def _tiny(depth=True):
    lay = FresnelLayout()
    p = Physics().replace(**TINY, **({} if depth else dict(depth_std=0.0)))
    sc = make_scene(17_000_005, p, lay=lay)
    sc['sensor_dust'] = camera(7, p, lay)['dust']
    return sc, session(17_000, p), p


def test_the_scene_is_the_same_for_every_grid_and_distance():
    sc, _, p = _tiny()
    other = make_scene(17_000_005, p.replace(z0=0.7e-3, oversample=4), lay=FresnelLayout())
    assert sc['rows'] == other['rows'] and len(sc['dust']) == len(other['dust']) and len(sc['rows']) >= 1
    things = sc['objects'] + sc['dust'] + sc['sensor_dust']
    assert {o['kind'] for o in things} >= {'letter', 'dust'}
    for o in things:
        for s in (1, 2, 4):   # the grid of s is the area mean of the grid of 2s: one object, nested samplings
            m, x, y = sample_mask(o, s)
            m2, x2, y2 = sample_mask(o, 2 * s)
            pad = np.zeros((m.shape[0] * 2, m.shape[1] * 2), np.float32)
            dy, dx = y2 - 2 * y, x2 - 2 * x
            pad[dy:dy + m2.shape[0], dx:dx + m2.shape[1]] = m2
            assert np.allclose(pad.reshape(m.shape[0], 2, m.shape[1], 2).mean((1, 3)), m, atol=1e-6)
    r = sc['rows'][0]   # positions to 1/16 of a pixel, inside the integer box the pipeline reads
    assert r['x0'] <= r['bx0'] < r['bx1'] <= r['x1'] and r['y0'] <= r['by0'] < r['by1'] <= r['y1']
    assert FresnelLayout().font_min == pytest.approx(15.9545, abs=1e-3)
    assert FresnelLayout().font_max == pytest.approx(26.8947, abs=1e-3)


def test_the_oversampled_path_is_aligned_with_the_pixel_grid():
    """A smooth object (a Gaussian of 4 px) is recorded alike by the native path and by the oversampled one: the cells
    of the fine grid sit inside their pixel (a shift of one pixel would give ~18 %)."""
    f = FresnelLayout.factor
    n = 40 * f
    yy, xx = np.mgrid[0:n, 0:n]
    c = (n - 1) / 2
    g = np.exp(-(((xx - c) / f) ** 2 + ((yy - c) / f) ** 2) / (2 * 4.0 ** 2)).astype(np.float32)
    p = Physics().replace(window=(128, 128), margin=64, reach=0, z0=1e-3, dust_density=0, sensor_dust_density=0)
    o = physical_object(g, 104 * f + 5, 104 * f + 3, f, absorption=0.5, phase=0.5, depth=0.0, kind='letter')
    sc = dict(objects=[o], dust=[], sensor_dust=[])
    i1 = sensor_intensity(sc, dict(z=1e-3), p, DEV)
    i4 = sensor_intensity(sc, dict(z=1e-3), p.replace(oversample=4), DEV)
    assert rel(i1, i4, i4 - 1) < 0.01


def test_oversampling_converges_on_a_tiny_scene():
    """The pair (4, 8) agrees within the tolerance of P0 (1 %) with every effect of the set on; (2, 4) agrees less
    (on the scenes of the set it does not pass: oversampling_convergence.csv)."""
    sc, ses, p = _tiny()
    i = {s: sensor_intensity(sc, ses, p.replace(oversample=s), DEV) for s in (2, 4, 8)}
    pattern = i[8] - sensor_intensity(sc, ses, p.replace(oversample=8), DEV, sample=False)
    assert rel(i[4], i[8], pattern) <= 0.01
    assert rel(i[2], i[4], pattern) > rel(i[4], i[8], pattern)


def test_fresnel_similarity():
    """A point monochromatic source, no pixel: a letter of side L at z and the same letter of side 2L at 4z give the
    same pattern scaled by 2 (compared on the fine grids, the large one averaged 2 x 2). The large letter is the small
    one's master raster with each cell a 2 x 2 block, placed at twice the distance from the window's corner (to the cell:
    an error of 1/32 px in the position alone gives 3.6 %; measured 0.9 %). A wrong distance (2z) does not match."""
    f = FresnelLayout.factor
    small = letter_master('F', FONTS[0], 20 * f, 10.0).astype(np.float32) / 255
    big = np.kron(small, np.ones((2, 2), np.float32))
    base = dict(reach=0, dust_density=0, sensor_dust_density=0, bandwidth=0.0, pinhole=0.0, oversample=4)
    p1 = Physics().replace(window=(64, 64), margin=64, **base)
    p2 = Physics().replace(window=(128, 128), margin=128, **base)
    k = (64 + 32) * f - small.shape[0] // 2   # master cell of the corner of the small letter (canvas of p1)

    def pattern(mst, p, mx, z):
        o = physical_object(mst, mx, mx, f, absorption=0.6, phase=0.8, depth=0.0, kind='letter')
        return fine_intensity(dict(objects=[o], dust=[], sensor_dust=[]), dict(z=z), p, DEV)
    i1 = pattern(small, p1, k, 1e-3)
    i2 = pattern(big, p2, 2 * k, 4e-3)    # the corner twice as far from the corner of the canvas (and of the window)
    i2 = i2.reshape(i1.shape[0], 2, i1.shape[1], 2).mean((1, 3))
    assert rel(i1, i2, i1 - 1) < 0.03
    wrong = pattern(big, p2, 2 * k, 2e-3).reshape(i1.shape[0], 2, i1.shape[1], 2).mean((1, 3))
    assert rel(i1, wrong, i1 - 1) > 0.3


def test_oversampling_needs_the_pixel_aperture():
    sc, ses, p = _tiny()
    with pytest.raises(ValueError):
        sensor_intensity(sc, ses, p.replace(oversample=2, pixel_mtf=False), DEV)


def test_a_fresnel_set_and_its_recording_at_another_distance(tmp_path):
    """generate() with the layout of the pilot, oversampled: physics.json keeps the factor and the layout; the same
    scenes recorded again at 0.7 mm (like=) have the same annotations; the boxes are integers that enclose the ink."""
    import pandas as pd
    from holo_openset.sim.generate import generate
    small = dict(TINY, oversample=2)
    generate(tmp_path / 'a', phys=small, n_images=4, per_session=2, workers=1, dev=DEV, layout='fresnel',
             layout_params=dict(letters_mean=8.0), log=lambda *a: None)
    generate(tmp_path / 'b', phys=dict(z0=0.7e-3), like=tmp_path / 'a', split='test', workers=1, dev=DEV,
             log=lambda *a: None)
    ca, cb = (json.load(open(tmp_path / d / 'physics.json')) for d in 'ab')
    assert ca['physics']['oversample'] == 2 and ca['layout'] == cb['layout'] == 'fresnel'
    assert ca['layout_params'] == cb['layout_params'] and cb['physics']['z0'] == 0.7e-3
    a, b = (pd.read_csv(tmp_path / d / 'annotations.csv') for d in 'ab')
    keys = ['image_id', 'classe', 'x0', 'y0', 'x1', 'y1', 'bx0', 'by0', 'bx1', 'by1', 'font_size', 'rotation']
    assert len(b) and (a[a.split == 'test'][keys].reset_index(drop=True) == b[keys].reset_index(drop=True)).all().all()
    assert all(pd.api.types.is_integer_dtype(a[c]) for c in ['x0', 'y0', 'x1', 'y1'])
    assert ((a.x0 <= a.bx0) & (a.bx1 <= a.x1) & (a.y0 <= a.by0) & (a.by1 <= a.y1)).all()
    assert (tmp_path / 'a' / 'labels' / '000000.txt').exists()


def test_the_extended_calibration_grid_keeps_its_points_and_reaches_0_7_mm():
    import math
    from holo_openset.sim.physics import PIXEL, WAVELENGTH
    from holo_openset.train import calibrate_alpha
    lo, hi, n, k = 0.001, 0.08, 80, 12
    r = (hi / lo) ** (1 / (n - 1))
    ext = np.geomspace(lo / r ** k, hi, n + k)
    assert np.allclose(ext[k:], np.geomspace(lo, hi, n), rtol=1e-12, atol=0)
    z = ext[0] * (640 * PIXEL) ** 2 / (math.pi * WAVELENGTH)
    assert 0.48e-3 < z < 0.49e-3   # 0.7 mm and 1.0 mm well inside
    x = torch.randint(0, 255, (2, 64, 64), dtype=torch.uint8)
    assert calibrate_alpha(x, DEV, n_fine=3) == calibrate_alpha(x, DEV, n_fine=3, extend=0)
