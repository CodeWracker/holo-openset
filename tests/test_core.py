"""Fast checks of what the results rest on; they need no data, no models and no GPU."""
import numpy as np
import torch

from holo_openset.model import FourierLayer
from holo_openset.protocol import classes
from holo_openset.reconstruct import backprop, kernel, remove_twin
from holo_openset.reproduce import check
from holo_openset.sim.physics import Physics, sensor_intensity
from holo_openset.sim.scene import make_scene, session
from holo_openset.spectrum import fast_pad, fast_shape

DEV = torch.device('cpu')
SMALL = dict(window=(320, 320), margin=128, reach=64, dust_density=0, sensor_dust_density=0)


def test_partitions_hold_out_five_classes():
    for r in range(1, 6):
        seen, unseen = map(set, classes(r))
        assert len(seen) == 21 and len(unseen) == 5 and not seen & unseen


def test_propagation_is_undone_by_the_opposite_distance():
    forward = kernel((32, 48), [0.01925], DEV, sign=-1)
    back = kernel((32, 48), [0.01925], DEV, sign=+1)
    assert torch.allclose(forward * back, torch.ones_like(forward), atol=1e-5)


def test_layer_starts_as_the_identity_on_any_size():
    layer = FourierLayer(mode='radial').eval()
    x = torch.randn(1, 96, 160)
    assert torch.allclose(layer(x)[0, 0], x, atol=1e-5)


def test_fast_sizes():
    assert fast_shape((2748, 3840)) == (2750, 3840) and fast_shape((640, 640)) == (640, 640)
    x = torch.randn(640, 640)
    assert fast_pad(x) is x


def test_a_size_with_a_large_prime_comes_back_with_its_size():
    x = torch.randn(1, 229, 160)
    assert torch.allclose(FourierLayer(mode='radial').eval()(x)[0, 0], x, atol=1e-5)
    a = torch.ones(229, 160)
    assert backprop(a, [0.01925]).shape == (1, 229, 160) and remove_twin(a, 0.01925, iters=2).shape == (229, 160)


def test_propagation_layer_at_the_physical_alpha_is_the_back_propagation():
    import math
    from holo_openset.sim.physics import PIXEL, WAVELENGTH, Z0
    layer = FourierLayer(mode='prop').eval()
    layer.alpha.data[:] = math.pi * WAVELENGTH * Z0 / (640 * PIXEL) ** 2
    x = torch.rand(640, 640)
    y, u = layer(x[None])[0], backprop(x, [Z0])[0]
    assert torch.allclose(y[0], u.real, atol=1e-3) and torch.allclose(y[1], u.imag, atol=1e-3)


def test_focal_stack_has_three_channels_per_distance():
    assert FourierLayer(mode='bank', n_dist=5).eval()(torch.randn(1, 96, 96)).shape == (1, 15, 96, 96)


def test_every_mode_builds_an_embedder():
    from holo_openset.model import HoloEmbedder
    for mode, n in [('none', None), ('radial', 1), ('complex', 3), ('prop', 3), ('bank', 15)]:
        m = HoloEmbedder(21, mode=mode, pretrained=False, n_dist=5)
        assert m.fourier.out_channels == n
    x = torch.randint(0, 255, (1, 3, 64, 64), dtype=torch.uint8)
    assert HoloEmbedder(21, mode='none', pretrained=False).filtered(x).shape == (1, 3, 64, 64)


def test_complex_layer_gives_three_channels():
    assert FourierLayer(mode='complex').eval()(torch.randn(2, 64, 64)).shape == (2, 3, 64, 64)


def test_simulation_repeats_from_its_seed():
    p = Physics().replace(**SMALL)
    a, b = [sensor_intensity(dict(make_scene(5, p), sensor_dust=[]), session(1, p), p, DEV).numpy() for _ in range(2)]
    assert np.array_equal(a, b)


def test_tables_of_the_paper_match_the_results():
    assert check() == 0


# ------------------------------------------------------------------------------------ the distance study
def _hologram(z, seed=5):
    """A noise-free hologram of a few letters in one plane at a known distance, under a coherent source, as the
    modulus sqrt(I) the autofocus receives."""
    p = Physics().replace(window=(640, 640), margin=256, reach=128, dust_density=0, sensor_dust_density=0,
                          session_z_std=0.0, depth_std=0.0, bandwidth=0.0, pinhole=0.0)
    ses = dict(session(1, p), z=z)
    return torch.sqrt(sensor_intensity(dict(make_scene(seed, p), sensor_dust=[]), ses, p, DEV).float())


def test_new_effects_are_off_by_default_and_leave_the_session_alone():
    from holo_openset.sim.generate import apply_tilt, frame_session
    p = Physics().replace(**SMALL)
    assert (p.frame_z_std, p.frame_z_walk, p.tilt_deg) == (0.0, 0.0, 0.0)
    ses = session(1, p)
    assert frame_session(ses, p, 17_000_123) is ses
    sc = make_scene(5, p)
    before = [o['depth'] for o in sc['objects']]
    apply_tilt(sc, p, 17_001)
    assert [o['depth'] for o in sc['objects']] == before


def test_distance_per_frame_changes_only_the_distance_and_repeats():
    from holo_openset.sim.generate import frame_session, session_walk
    p = Physics().replace(**SMALL, frame_z_std=0.05)
    ses = session(1, p)
    a, b, c = frame_session(ses, p, 17_000_123), frame_session(ses, p, 17_000_123), frame_session(ses, p, 17_000_124)
    assert a == b and a['z'] != ses['z'] and a['z'] != c['z']
    assert {k: v for k, v in a.items() if k != 'z'} == {k: v for k, v in ses.items() if k != 'z'}
    assert make_scene(5, p)['rows'] == make_scene(5, Physics().replace(**SMALL))['rows']   # the scene does not move
    w = session_walk(17_001, 100, 0.005)
    assert w[0] == 0.0 and w == session_walk(17_001, 100, 0.005) and len(set(w)) == 100
    q = p.replace(frame_z_std=0.0, frame_z_walk=0.005)
    assert frame_session(ses, q, 17_000_123, w[7])['z'] == ses['z'] * (1 + w[7])


def test_tilt_is_a_depth_proportional_to_the_position():
    import math
    from holo_openset.sim.generate import apply_tilt
    from holo_openset.sim.physics import PIXEL
    p0 = Physics().replace(window=(640, 640), margin=256, reach=128, sensor_dust_density=0)
    p = p0.replace(tilt_deg=5.0)
    flat, sc = make_scene(5, p0), make_scene(5, p)
    apply_tilt(sc, p, 17_001)
    things, before = sc['objects'] + sc['dust'], flat['objects'] + flat['dust']   # letters in and around, slide dust
    assert len(things) > 8 and {o['kind'] for o in things} >= {'letter', 'dust'}
    d = np.array([o['depth'] - f['depth'] for o, f in zip(things, before)])
    H, W = p.canvas
    x = np.array([o['x'] + o['mask'].shape[1] / 2 - W / 2 for o in things]) * PIXEL
    y = np.array([o['y'] + o['mask'].shape[0] / 2 - H / 2 for o in things]) * PIXEL
    gx, gy = np.linalg.lstsq(np.c_[x, y], d, rcond=None)[0]
    assert np.allclose(d, gx * x + gy * y, atol=1e-12)                      # a plane through the centre
    assert math.isclose(math.hypot(gx, gy), math.tan(math.radians(5.0)), rel_tol=1e-9)
    letters = [o for o in sc['objects'] if o['kind'] == 'letter']
    assert [r['depth'] for r in sc['rows']] == [o['depth'] for o in letters]
    assert [(r['x0'], r['y0'], r['classe']) for r in sc['rows']] == [(r['x0'], r['y0'], r['classe']) for r in flat['rows']]


def test_default_autofocus_is_the_blind_search_of_the_paper():
    from holo_openset.reconstruct import BLIND, COARSE, N_FINE, autofocus, scan
    a = _hologram(0.0185)
    c = float(COARSE[int(scan(a, 0.01925 * COARSE).argmax())])
    step = COARSE[1] - COARSE[0]
    fine = np.linspace(c - step, c + step, N_FINE)
    z = 0.01925 * float(fine[int(scan(a, 0.01925 * fine).argmax())])   # the search as the paper wrote it
    assert autofocus(a, 0.01925) == (z, 114) == autofocus(a, 0.01925, BLIND)
    assert abs(z - 0.0185) < 60e-6


def test_binned_search_finds_the_distance_with_the_scaled_pixel():
    from holo_openset.reconstruct import Focus, autofocus
    a = _hologram(0.0201)
    for b in (2, 4):   # over the blind range, which holds z / b^2: where the search lands with the pixel unscaled
        found, n = autofocus(a, 0.01925, Focus(bin=b))
        assert n == 114 and abs(found - 0.0201) < 60e-6, (b, found)
    assert abs(autofocus(a, 0.01925, Focus(lo=0.85, hi=1.15, n_coarse=15, n_fine=11, bin=4))[0] - 0.0201) < 60e-6


def test_masked_and_smoothed_sharpness_runs_and_needs_the_blank_frame():
    import pytest
    from holo_openset.reconstruct import Focus, autofocus
    a = _hologram(0.0185)
    bg = torch.ones_like(a)
    bg[:, :80] = 0.05                     # a dark band: no light, the pixels there do not count
    f = Focus(lo=0.85, hi=1.15, n_coarse=15, n_fine=11, mask=0.2, fill=True, sigma=1.5)
    assert abs(autofocus(a, 0.01925, f, bg)[0] - 0.0185) < 60e-6
    with pytest.raises(ValueError):
        autofocus(a, 0.01925, f)


def test_reusing_a_distance_follows_the_order_of_the_images_in_a_session():
    from holo_openset.reconstruct import Focus, focus_blocks
    ids = [205, 100, 101, 102, 103, 104, 200, 201, 202, 203, 204]
    session = {i: i // 100 for i in ids}
    assert focus_blocks(ids, session, Focus()) == [([i], [i]) for i in ids]
    assert focus_blocks(ids, session, Focus(every=0)) == [([100, 101, 102, 103, 104], [100]),
                                                          ([200, 201, 202, 203, 204, 205], [200])]
    assert focus_blocks(ids, session, Focus(every=0, first=3))[1][1] == [200, 201, 202]
    assert focus_blocks(ids, session, Focus(every=2))[:3] == [([100, 101], [100]), ([102, 103], [102]), ([104], [104])]


def test_frozen_searches_are_candidates_of_the_validation_sweep():
    import dataclasses
    from holo_openset.experiments.focus import GRID
    from holo_openset.reconstruct import BLIND, FOCUS
    assert FOCUS['afc'] == GRID['r10b-b4-tog'] and FOCUS['afr'] == GRID['r15b-b2-s2']
    assert FOCUS['afsc'] == dataclasses.replace(FOCUS['afc'], every=0, first=1)
    assert FOCUS['afs'] == dataclasses.replace(BLIND, every=0, first=1) and FOCUS['afM'] == dataclasses.replace(BLIND, every=10)
    assert (FOCUS['afc'].n, FOCUS['afc'].cost, FOCUS['afr'].n, FOCUS['afr'].cost) == (18, 1.125, 36, 9.0)


def test_study_flows_borrow_a_model_and_stay_out_of_the_queue_of_the_paper():
    from holo_openset.flows import FLOWS, PAPER_FLOWS, STUDY, weights_of
    from holo_openset.pipeline import ALL, jobs
    from holo_openset.sim.variants import ALL as ALL_VARIANTS, STUDY as STUDY_VARIANTS, VARIANTS
    assert weights_of('rec_af') == 'rec_af' and weights_of('rec_edfw') == 'rec_edf'
    assert all(weights_of(f) in PAPER_FLOWS for f in STUDY) and not set(STUDY) & set(ALL) and set(STUDY) <= set(FLOWS)
    assert len(VARIANTS) == 32 and not set(STUDY_VARIANTS) & set(VARIANTS) and len(ALL_VARIANTS) == 32 + len(STUDY_VARIANTS)
    assert len(jobs()) == 575   # as before the study
