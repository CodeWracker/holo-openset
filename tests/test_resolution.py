"""Sets reduced b x b (holo_openset.resolution, docs/exp_resolucao): b = 1 changes nothing, the effective pixel reaches
every frequency computation, and alpha is the same number at every b."""
import json
import math

import numpy as np
import pandas as pd
import pytest
import torch

from holo_openset.model import FourierLayer, HoloEmbedder, load_model
from holo_openset.reconstruct import Holograms, backprop
from holo_openset.resolution import bin_float, bin_u8, default_name, grid_size, reduce_set, set_pixel
from holo_openset.sim.physics import PIXEL, WAVELENGTH, Z0, propagate

DEV = torch.device('cpu')


def test_block_mean_rounds_half_up_and_b1_is_the_identity():
    x = np.array([[[0, 1, 2, 2], [0, 1, 2, 3], [255, 255, 7, 8], [255, 254, 9, 9]]], np.uint8)
    assert np.array_equal(bin_u8(x, 1), x)
    assert bin_u8(x, 2).tolist() == [[[1, 2], [255, 8]]]   # 0.5 -> 1, 2.25 -> 2, 254.75 -> 255, 8.25 -> 8
    assert bin_float(x.astype(np.float32), 2).tolist() == [[[0.5, 2.25], [254.75, 8.25]]]
    with pytest.raises(ValueError):
        bin_u8(np.zeros((6, 6), np.uint8), 4)


def test_names_and_grid_of_a_reduced_set():
    assert default_name('realistic', 4) == 'realistic_b4'
    assert default_name('variants/fullwell_500', 2) == 'variants_b2/fullwell_500'
    assert [grid_size(PIXEL * b, 640) for b in (1, 2, 4, 8)] == [640, 320, 160, 80]
    with pytest.raises(ValueError):
        grid_size(PIXEL * 3, 640)


def _toy_set(root, n=4, size=16):
    rng = np.random.RandomState(0)
    root.mkdir()
    np.save(root / 'holograms.npy', rng.randint(0, 256, (n, size, size)).astype(np.uint8))
    np.save(root / 'backgrounds.npy', rng.uniform(50, 200, (2, size, size)).astype(np.float32))
    pd.DataFrame(dict(image_id=[0, 1], classe=['A', 'B'], x0=[1, 3], y0=[2, 4], x1=[9, 11], y1=[10, 15],
                      split=['train', 'val'])).to_csv(root / 'annotations.csv', index=False)
    pd.DataFrame(dict(image_id=range(n), split='train', session=[0, 0, 1, 1], z=Z0)).to_csv(root / 'metadata.csv',
                                                                                           index=False)
    pd.DataFrame(dict(session=[0, 1], z=Z0)).to_csv(root / 'sessions.csv', index=False)
    json.dump(dict(physics=dict(intensity=True, z0=Z0)), open(root / 'physics.json', 'w'))
    return root


def test_reduced_set_b1_is_the_set_and_b2_halves_images_and_boxes(tmp_path):
    src = _toy_set(tmp_path / 'toy')
    reduce_set(src, tmp_path / 'toy_b1', 1, log=lambda *_: None)
    for f in ['holograms.npy', 'backgrounds.npy', 'annotations.csv', 'metadata.csv', 'sessions.csv']:
        assert (src / f).read_bytes() == (tmp_path / 'toy_b1' / f).read_bytes(), f
    assert set_pixel(src) == PIXEL and set_pixel(tmp_path / 'toy_b1') == PIXEL
    reduce_set(src, tmp_path / 'toy_b2', 2, log=lambda *_: None)
    d = tmp_path / 'toy_b2'
    assert np.load(d / 'holograms.npy').shape == (4, 8, 8) and np.load(d / 'backgrounds.npy').dtype == np.float32
    assert pd.read_csv(d / 'annotations.csv')[['x0', 'y0', 'x1', 'y1']].values.tolist() == [[0.5, 1, 4.5, 5],
                                                                                         [1.5, 2, 5.5, 7.5]]
    assert set_pixel(d) == 2 * PIXEL and Holograms(d).pixel == 2 * PIXEL
    with pytest.raises(SystemExit):
        reduce_set(src, src, 2)
    with pytest.raises(SystemExit):
        reduce_set(d, tmp_path / 'again', 2)


def test_index_k_of_a_reduced_grid_is_the_frequency_k_of_the_training_grid():
    small, big = FourierLayer(160, mode='prop'), FourierLayer(640, mode='prop')
    k = np.r_[0:80, -79:0]   # the indices both grids hold
    qs = small.grid_q((160, 160))[np.ix_(k % 160, k % 160)]
    qb = big.grid_q((640, 640))[np.ix_(k % 640, k % 640)]
    assert torch.equal(qs, qb)


def test_back_propagation_at_the_effective_pixel_commutes_with_the_block_mean():
    # a field with nothing above 1/8 of the Nyquist frequency: back-propagating it and then averaging 4 x 4 is the same
    # as averaging and then back-propagating with the pixel 4 x larger
    rng = np.random.RandomState(1)
    spec = np.zeros((640, 640), complex)
    k = np.r_[0:30, -29:0]
    spec[np.ix_(k, k)] = rng.randn(len(k), len(k)) + 1j * rng.randn(len(k), len(k))
    a = torch.from_numpy(np.fft.ifft2(spec).real * 640 + 1).float()
    full = backprop(a, [Z0])[0]
    small = backprop(torch.nn.functional.avg_pool2d(a[None, None], 4)[0, 0], [Z0], pixel=4 * PIXEL)[0]
    ref = torch.complex(torch.nn.functional.avg_pool2d(full.real[None, None], 4)[0, 0],
                        torch.nn.functional.avg_pool2d(full.imag[None, None], 4)[0, 0])
    assert (small - ref).abs().max() < 0.05 * (ref - 1).abs().max()
    assert torch.equal(backprop(a, [Z0], pixel=PIXEL), backprop(a, [Z0]))   # b = 1: the same numbers


def test_calibrated_alpha_is_the_same_at_every_b():
    from holo_openset.train import calibrate_alpha
    rng = np.random.RandomState(2)
    yy, xx = np.mgrid[:640, :640]
    imgs = []
    for _ in range(2):   # discs that absorb, recorded with a source that keeps < 60 cycles/mm
        o = np.zeros((640, 640), np.complex64)
        for cx, cy, r in zip(rng.uniform(80, 560, 12), rng.uniform(80, 560, 12), rng.uniform(8, 25, 12)):
            o[(xx - cx) ** 2 + (yy - cy) ** 2 < r * r] = -0.5
        i = (1 + propagate(torch.from_numpy(o), Z0)).abs() ** 2
        f = torch.fft.fftfreq(640, d=PIXEL, dtype=torch.float64)
        lp = torch.exp(-(f[None, :] ** 2 + f[:, None] ** 2) / (40e3) ** 2)
        i = torch.fft.ifft2(torch.fft.fft2(i.double()) * lp).real
        imgs.append((i * 100).round().clamp(0, 255).to(torch.uint8).numpy())
    imgs = np.stack(imgs)
    alphas = {b: calibrate_alpha(torch.from_numpy(bin_u8(imgs, b)), DEV, size=640 // b) for b in (1, 2, 4)}
    truth = math.pi * WAVELENGTH * Z0 / (640 * PIXEL) ** 2
    for b, v in alphas.items():
        assert abs(v / truth - 1) < 0.02, (b, v, truth)
        assert abs(v / alphas[1] - 1) < 0.01, (b, v, alphas[1])


def test_a_checkpoint_keeps_the_grid_of_its_set(tmp_path):
    m = HoloEmbedder(3, mode='prop', pretrained=False, size=160)
    torch.save({'state_dict': m.state_dict(), 'meta': {}}, tmp_path / 'm.pt')
    back = load_model(tmp_path / 'm.pt')[0]
    assert back.fourier.inv.shape == (160, 160)
