"""The conventional reconstruction of an in-line hologram, as a laboratory does it, and the caches of its outputs.

  normalise    a = sqrt(I / B): the hologram divided by the blank frame of its session (flat field), taken as the
               modulus of the field on the sensor (Latychevskaia & Fink 2007). For the idealised model, which records
               2 Re(U) - 1 instead of |U|^2, a = I / mean(I).
  propagate    back to the object plane at a distance z: U = P_{-z}[a], the transmission estimate 1 + q. One
               reconstruction is one complex transform pair (angular spectrum, Fresnel approximation).
  autofocus    blind: reconstruct at every candidate distance and keep the sharpest by the Tamura coefficient of the
               gradient of the complex field (Zhang et al. 2017), which peaks in focus for objects that absorb and for
               objects that only delay the light. 73 candidates in [0.2, 2.1] z0, then 41 around the best: 114
               reconstructions per hologram.
  per object   (extended depth of field) a stack of 25 reconstructions within +-1.2 % of the hologram's focus; each
               object is taken from the one in which ITS box is sharpest (objects lie at different depths).
  twin image   iterative removal (Latychevskaia & Fink 2007): keep the measured modulus on the sensor and, in the
               object plane, forbid negative absorption (|U| <= 1), keeping the phase. 50 passes.
The network receives three channels of q = U - 1: real part, imaginary part and modulus (an object that absorbs
appears in the real part, one that delays the light in the imaginary part).

Everything works on any image size (a 640 x 640 window or a full 3840 x 2748 frame) and in complex64.
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from holo_openset.sim.physics import WAVELENGTH, Z0, freq_sq

COARSE = np.linspace(0.004, 0.04, 73) / 0.01925   # candidate distances, in units of z0
N_FINE = 41
EDF_REL, EDF_N = 0.012, 25
TWIN_ITERS = 50
CDT = torch.complex64

_Q = {}


def _q(shape, dev):
    key = (tuple(shape), str(dev))
    if key not in _Q:
        _Q[key] = freq_sq(shape, dev)
    return _Q[key]


def normalise(holo, bg, intensity=True):
    """holo [..., h, w] (camera units), bg blank frame of its session -> modulus of the field on the sensor."""
    h = holo.float()
    if not intensity:
        return h / h.mean(dim=(-2, -1), keepdim=True).clamp(min=1e-6)
    return torch.sqrt((h / bg.float().clamp(min=1.0)).clamp(min=0))


def kernel(shape, zs, dev, sign=+1):
    """exp(sign i pi lambda z |f|^2) for each z of zs -> [K, h, w] complex64 (sign +1 = back-propagation)."""
    z = torch.as_tensor(np.asarray(zs, dtype=np.float64), device=dev)[:, None, None]
    return torch.exp(sign * 1j * math.pi * WAVELENGTH * z * _q(shape, dev)[None]).to(CDT)


def backprop(a, zs):
    """a [h, w] real -> U [K, h, w]: the field in the object plane at each distance of zs."""
    return torch.fft.ifft2(torch.fft.fft2(a.to(CDT))[None] * kernel(a.shape[-2:], zs, a.device))


def tog(u, boxes=None):
    """Tamura coefficient of the gradient modulus of complex fields u [K, h, w] -> [K] (or [K, nb] in boxes)."""
    gx = u[..., :, 1:] - u[..., :, :-1]
    gy = u[..., 1:, :] - u[..., :-1, :]
    g = torch.sqrt(gx[..., :-1, :].abs() ** 2 + gy[..., :, :-1].abs() ** 2)
    if boxes is None:
        g = g.flatten(1)
        return torch.sqrt(g.std(1) / g.mean(1))
    out = []
    for x0, y0, x1, y1 in boxes:
        r = g[:, y0:y1, x0:x1].flatten(1)
        out.append(torch.sqrt(r.std(1) / r.mean(1).clamp(min=1e-12)))
    return torch.stack(out, 1)


def _chunk(shape):
    return max(1, int(1.5e8 // (shape[-1] * shape[-2])))


def scan(a, zs):
    """Sharpness (ToG) of the reconstruction of a at every distance of zs (one FFT of a, one inverse per z)."""
    A = torch.fft.fft2(a.to(CDT))[None]
    c = _chunk(a.shape)
    return torch.cat([tog(torch.fft.ifft2(A * kernel(a.shape[-2:], zs[k:k + c], a.device)))
                      for k in range(0, len(zs), c)])


def autofocus(a, z0=Z0):
    """Blind autofocus of one hologram a [h, w] -> z (m) and the number of reconstructions it took. The candidates
    span 0.2-2.1 times the nominal distance z0 of the set-up."""
    c = float(COARSE[int(scan(a, z0 * COARSE).argmax())])
    step = COARSE[1] - COARSE[0]
    fine = np.linspace(c - step, c + step, N_FINE)
    return z0 * float(fine[int(scan(a, z0 * fine).argmax())]), len(COARSE) + N_FINE


def int_boxes(xyxy, shape, buffer=0.25):
    from holo_openset.model import square_boxes
    b = square_boxes(xyxy, buffer).round().astype(int)
    h, w = shape
    return [(max(0, x0), max(0, y0), min(w, x1), min(h, y1)) for x0, y0, x1, y1 in b]


def per_object(a, z, xyxy):
    """Extended depth of field: each box taken from the reconstruction (+-1.2 % of z, 25 steps) in which it is
    sharpest. -> composite U [h, w], the distance chosen for each box."""
    zs = z * (1 + np.linspace(-EDF_REL, EDF_REL, EDF_N))
    boxes = int_boxes(xyxy, a.shape)
    A = torch.fft.fft2(a.to(CDT))[None]
    c = _chunk(a.shape)
    best = [-1.0] * len(boxes)
    kbest = [EDF_N // 2] * len(boxes)
    region = [None] * len(boxes)
    out = None
    for k in range(0, EDF_N, c):   # the stack is scanned in chunks: on a full frame it does not fit at once
        u = torch.fft.ifft2(A * kernel(a.shape[-2:], zs[k:k + c], a.device))
        if k <= EDF_N // 2 < k + c:
            out = u[EDF_N // 2 - k].clone()
        if boxes:
            v, j = tog(u, boxes).max(0)
            for b, (vb, jb) in enumerate(zip(v.tolist(), j.tolist())):
                if vb > best[b]:
                    x0, y0, x1, y1 = boxes[b]
                    best[b], kbest[b], region[b] = vb, k + jb, u[jb, y0:y1, x0:x1].clone()
    for (x0, y0, x1, y1), r in zip(boxes, region):
        out[y0:y1, x0:x1] = r
    return out, [float(zs[kk]) for kk in kbest]


def remove_twin(a, z, iters=TWIN_ITERS, trace=None):
    """Iterative twin-image removal of one hologram -> transmission U [h, w] (|U| <= 1).
    trace: optional callback(k, U) after pass k (k = 1 is the conventional reconstruction, clipped)."""
    back = kernel(a.shape[-2:], [z], a.device)[0]
    fwd = torch.conj(back)
    phase = torch.zeros_like(a)
    for k in range(1, iters + 1):
        u = torch.fft.ifft2(torch.fft.fft2(a * torch.exp(1j * phase)) * back)
        m = u.abs()
        u = torch.where(m > 1, u / m.clamp(min=1e-12), u)       # absorption cannot be negative
        if trace:
            trace(k, u)
        if k < iters:
            phase = torch.angle(torch.fft.ifft2(torch.fft.fft2(u) * fwd))
    return u


def channels(u):
    """U [h, w] complex -> uint8 [3, h, w]: real and imaginary part of q = U - 1 (centred at 128) and |q|, each
    scaled to its own 99.9th percentile."""
    q = u - 1
    out = []
    for c, signed in [(q.real, True), (q.imag, True), (q.abs(), False)]:
        s = torch.quantile(c.abs().flatten().float()[::7][:16_000_000], 0.999).clamp(min=1e-9)
        v = 128 + 127 * c / s if signed else 255 * c / s
        out.append(v.round().clamp(0, 255).to(torch.uint8))
    return torch.stack(out)


METHODS = ('z0', 'af', 'edf', 'twin')


class Holograms:
    """Holograms of a set (or of its auxiliary scenes), each with the blank frame of its session and its boxes."""

    def __init__(self, root, aux=None):
        self.root = Path(root)
        cfg = json.load(open(self.root / 'physics.json'))
        self.intensity = cfg['physics']['intensity']
        self.z0 = cfg['physics'].get('z0', Z0)
        self.bg = np.load(self.root / 'backgrounds.npy', mmap_mode='r')
        if aux is None:
            self.holo = np.load(self.root / 'holograms.npy', mmap_mode='r')
            meta = pd.read_csv(self.root / 'metadata.csv')
            ann = pd.read_csv(self.root / 'annotations.csv')
            self.ids = meta.image_id.to_numpy()
            self.session = dict(zip(meta.image_id, meta.session))
            self.true_z = dict(zip(meta.image_id, meta.z))
        else:
            self.holo = np.load(self.root / 'aux' / f'{aux}_images.npy', mmap_mode='r')
            ann = pd.read_csv(self.root / 'aux' / f'{aux}_boxes.csv')
            self.ids = np.arange(len(self.holo))
            self.session = ann.groupby('image_id').session.first().to_dict()
            ses = pd.read_csv(self.root / 'sessions.csv')
            zs = dict(zip(ses.session, ses.z))
            self.true_z = {i: zs[s] for i, s in self.session.items()}
        self.boxes = {i: g[['x0', 'y0', 'x1', 'y1']].to_numpy() for i, g in ann.groupby('image_id')}
        self.row = {int(i): k for k, i in enumerate(self.ids)}

    def amplitude(self, i, dev):
        h = torch.from_numpy(np.array(self.holo[self.row[i]])).to(dev)
        b = torch.from_numpy(np.array(self.bg[self.session.get(i, 0)])).to(dev)
        return normalise(h, b, self.intensity)


def reconstruct(a, method, z_af=None, boxes=None, z0=Z0):
    """One hologram amplitude a [h, w] -> U [h, w] by a method of METHODS (z_af: the autofocus distance)."""
    if method == 'z0':
        return backprop(a, [z0])[0]
    if method == 'af':
        return backprop(a, [z_af])[0]
    if method == 'edf':
        return per_object(a, z_af, boxes if boxes is not None else np.zeros((0, 4)))[0]
    if method == 'twin':
        return remove_twin(a, z_af)
    raise ValueError(method)


def build_caches(root, methods, dev, aux=None, log=print):
    """Write <root>/rec_<method>.npy (or <root>/aux/<aux>_rec_<method>.npy), uint8 [N, 3, h, w], and the autofocus
    log (autofocus.csv / aux/<aux>_autofocus.csv). The per-object method uses the annotated boxes."""
    src = Holograms(root, aux)
    pre = f"{src.root / 'aux' / aux}_" if aux else f'{src.root}/'
    h, w = src.holo.shape[1:]
    arrs = {m: np.lib.format.open_memmap(f'{pre}rec_{m}.npy', mode='w+', dtype=np.uint8, shape=(len(src.ids), 3, h, w))
            for m in methods}
    rows = []
    for k, i in enumerate(src.ids):
        i = int(i)
        a = src.amplitude(i, dev)
        z_af, n = autofocus(a, src.z0) if set(methods) - {'z0'} else (src.z0, 0)
        row = dict(image_id=i, true_z=src.true_z.get(i), z_af=z_af, n_reconstructions=n)
        for m in methods:
            if m == 'edf':
                u, zb = per_object(a, z_af, src.boxes.get(i, np.zeros((0, 4))))
                row['z_objects'] = ';'.join(f'{v:.7f}' for v in zb)
            else:
                u = reconstruct(a, m, z_af, z0=src.z0)
            arrs[m][k] = channels(u).cpu().numpy()
        rows.append(row)
        if k % 500 == 0:
            log(f'{k}/{len(src.ids)}')
    for v in arrs.values():
        v.flush()
    pd.DataFrame(rows).to_csv(f'{pre}autofocus.csv', index=False)


def fidelity(root, dev, n=None, out=None):
    """PSNR (after the best affine fit, over the window) of each reconstruction's modulus against the amplitude of
    the letters, on the test split; the twin-image iteration traced pass by pass."""
    from PIL import Image
    src = Holograms(root)
    meta = pd.read_csv(src.root / 'metadata.csv')
    ids = meta[meta.split == 'test'].image_id.to_numpy()[:n]
    passes = [1, 2, 5, 10, 20, 50, 100]
    acc = {k: [] for k in ['hologram', 'z0', 'af', 'edf'] + [f'twin{p}' for p in passes]}

    def psnr(rec, ref):
        r, t = rec.flatten() - rec.mean(), ref.flatten() - ref.mean()
        s = (r * t).sum() / (r * r).sum().clamp(min=1e-12)
        return float(10 * torch.log10(1.0 / ((s * r - t) ** 2).mean()))
    af = pd.read_csv(src.root / 'autofocus.csv').set_index('image_id')
    for i in ids:
        i = int(i)
        amp = torch.from_numpy(np.asarray(Image.open(src.root / 'objects' / f'{i:06d}_amp.png'), np.float32) / 255).to(dev)
        a = src.amplitude(i, dev)
        z = float(af.loc[i, 'z_af'])
        acc['hologram'].append(psnr(a, amp))
        acc['z0'].append(psnr(backprop(a, [src.z0])[0].abs(), amp))
        acc['af'].append(psnr(backprop(a, [z])[0].abs(), amp))
        acc['edf'].append(psnr(per_object(a, z, src.boxes.get(i, np.zeros((0, 4))))[0].abs(), amp))
        remove_twin(a, z, iters=max(passes), trace=lambda k, u: acc[f'twin{k}'].append(psnr(u.abs(), amp))
                    if k in passes else None)
    res = dict(n_images=len(ids), twin_iterations_used=TWIN_ITERS,
               psnr_db={k: float(np.mean(v)) for k, v in acc.items()},
               autofocus_abs_error_um_median=float((af.z_af - af.true_z).abs().median() * 1e6),
               autofocus_rel_error_median=float(((af.z_af - af.true_z).abs() / af.true_z).median()))
    if out:
        json.dump(res, open(out, 'w'), indent=1)
    return res
