"""A set at the resolution the source allows (docs/exp_resolucao): every image averaged over b x b blocks of pixels,
as a sensor that bins its pixels would record it.

The source of the bench leaves little contrast above about 70 cycles/mm, a quarter of the Nyquist frequency of the
sensor (299 cycles/mm), so the images can be averaged over b x b blocks with little loss. A reduced set is a NEW set
(data/<name>_b<b>); nothing of the source set is changed:

  holograms.npy      uint8: the mean of each b x b block, rounded half up (what an 8-bit camera that bins would store)
  backgrounds.npy    float32: the mean of each b x b block of the blank frame of each session
  annotations.csv    the boxes divided by b (floats); every other column as it was
  dust.csv           the same
  aux/<name>_*       the auxiliary training scenes asked for (images and boxes), reduced the same way
  metadata.csv, sessions.csv  copied; labels/ (YOLO boxes, normalised to the image size) linked
  physics.json       that of the source set (the acquisition it simulated, in sensor pixels) plus 'pixel', the
                     effective pixel pitch b * 1.67 um, and 'reduction' (b, source, how)
Not carried over: the reconstruction caches (rec_*.npy: rebuild them on the reduced set with the effective pixel,
`python -m holo_openset reconstruct --set <name>_b<b> --methods z0`), their autofocus logs, the detections of the
paper's YOLO (dets_yolo_*.csv) and objects/ (the amplitude of the letters at the resolution of the sensor).

Every frequency computed on a reduced set uses the effective pixel: the back-propagation (reconstruct.Holograms reads
'pixel') and the Fourier layer of the network, whose grid has side N_train / b (the same field, 640 x 1.67 um): index k
of that grid is the same physical frequency as index k of the 640 grid, and alpha = pi lambda z / (N pixel)^2 is the
same number at every b. With b = 1 the arrays and csv files are those of the source, byte for byte.
"""
import json
import os
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from holo_openset.sim.physics import PIXEL

BOX_COLUMNS = ['x0', 'y0', 'x1', 'y1']


def set_pixel(root):
    """The pixel pitch (m) of the images of a set: the sensor's unless the set was reduced."""
    cfg = Path(root) / 'physics.json'
    return float(json.load(open(cfg)).get('pixel', PIXEL)) if cfg.exists() else PIXEL


def grid_size(pixel, size):
    """Side of the frequency grid of the Fourier layer for images sampled every `pixel` m: the training grid of
    `size` sensor pixels covers size * PIXEL metres, whatever the sampling."""
    n = size * PIXEL / pixel
    if abs(n - round(n)) > 1e-6:
        raise ValueError(f'the training grid of {size} px is not a whole number of pixels of {pixel * 1e6:.3f} um')
    return int(round(n))


def bin_u8(x, b):
    """uint8 [..., h, w] -> uint8 [..., h/b, w/b]: the mean of each b x b block, rounded half up."""
    x = np.asarray(x)
    if b == 1:
        return x.copy()
    h, w = x.shape[-2:]
    if h % b or w % b:
        raise ValueError(f'{h} x {w} is not divisible by {b}')
    s = x.reshape(*x.shape[:-2], h // b, b, w // b, b).sum(axis=(-3, -1), dtype=np.int64)
    return ((s + b * b // 2) // (b * b)).astype(np.uint8)


def bin_float(x, b):
    """float [..., h, w] -> float32 [..., h/b, w/b]: the mean of each b x b block (computed in float64)."""
    x = np.asarray(x)
    if b == 1:
        return x.astype(np.float32, copy=True)
    h, w = x.shape[-2:]
    if h % b or w % b:
        raise ValueError(f'{h} x {w} is not divisible by {b}')
    return x.reshape(*x.shape[:-2], h // b, b, w // b, b).astype(np.float64).mean(axis=(-3, -1)).astype(np.float32)


def _array(src, dst, fn, b, chunk=100):
    a = np.load(src, mmap_mode='r')
    out = np.lib.format.open_memmap(dst, mode='w+', dtype=np.uint8 if a.dtype == np.uint8 else np.float32,
                                    shape=(*a.shape[:-2], a.shape[-2] // b, a.shape[-1] // b))
    for k in range(0, len(a), chunk):
        out[k:k + chunk] = fn(a[k:k + chunk], b)
    out.flush()
    del out


def _boxes(src, dst, b):
    if b == 1:
        shutil.copyfile(src, dst)
        return
    t = pd.read_csv(src)
    t[BOX_COLUMNS] = t[BOX_COLUMNS].astype(np.float64) / b
    t.to_csv(dst, index=False)


def default_name(name, b):
    """realistic -> realistic_b4; variants/fullwell_500 -> variants_b4/fullwell_500."""
    head, *rest = name.split('/')
    return '/'.join([f'{head}_b{b}', *rest])


def reduce_set(src, dst, b, aux=(), log=print):
    """Write the set src reduced b x b to dst (a new directory). aux: names of auxiliary scenes to carry (r1, ...)."""
    src, dst = Path(src), Path(dst)
    if src.resolve() == dst.resolve():
        raise SystemExit('the reduced set must be a new set')
    if (dst / 'physics.json').exists():
        raise SystemExit(f'{dst} exists')
    cfg = json.load(open(src / 'physics.json'))
    if cfg.get('pixel', PIXEL) != PIXEL:
        raise SystemExit(f'{src} is already reduced: reduce the set of the sensor')
    dst.mkdir(parents=True, exist_ok=True)
    _array(src / 'holograms.npy', dst / 'holograms.npy', bin_u8, b)
    log(f'holograms {dst}')
    _array(src / 'backgrounds.npy', dst / 'backgrounds.npy', bin_float, b)
    _boxes(src / 'annotations.csv', dst / 'annotations.csv', b)
    if (src / 'dust.csv').exists():
        _boxes(src / 'dust.csv', dst / 'dust.csv', b)
    for f in ['metadata.csv', 'sessions.csv']:
        shutil.copyfile(src / f, dst / f)
    if (src / 'labels').is_dir() and not (dst / 'labels').exists():
        os.symlink(os.path.relpath((src / 'labels').resolve(), dst), dst / 'labels')
    for name in aux:
        (dst / 'aux').mkdir(exist_ok=True)
        _array(src / 'aux' / f'{name}_images.npy', dst / 'aux' / f'{name}_images.npy', bin_u8, b)
        _boxes(src / 'aux' / f'{name}_boxes.csv', dst / 'aux' / f'{name}_boxes.csv', b)
        log(f'aux {name}')
    cfg['pixel'] = PIXEL * b
    cfg['reduction'] = dict(bin=b, source=str(src), holograms='uint8, mean of each b x b block rounded half up',
                            backgrounds='float32, mean of each b x b block', boxes='divided by b (float)')
    json.dump(cfg, open(dst / 'physics.json', 'w'), indent=1)
    log(f'wrote {dst} (b = {b}, pixel {PIXEL * b * 1e6:.2f} um)')
