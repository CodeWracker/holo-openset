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

The distance study (docs/exp_distancia) asks what the autofocus costs when it is done as a laboratory would do it, not
at its most expensive. `Focus` describes one way of finding the distance, and FOCUS names the ones compared:
  when      every hologram (the blind autofocus above), once per session with the distance reused, or every M images;
  where     the blind range, or a narrow range around the nominal distance with fewer candidates;
  on what   the amplitude as recorded, or averaged in blocks (the source of the bench leaves little above 70 cycles/mm,
            so a coarser grid loses little), with the pixel pitch scaled accordingly;
  how       the sharpness of the whole field, or only where the blank frame says there was light, on a smoothed field.
Each has its cache rec_<name>.npy and its log autofocus_<name>.csv; autofocus.csv stays the log of the blind autofocus.

Everything works on any image size (a 640 x 640 window or a full 3840 x 2748 frame) and in complex64.
"""
import dataclasses
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

from holo_openset.sim.physics import PIXEL, WAVELENGTH, Z0, freq_sq
from holo_openset.spectrum import fast_pad

COARSE = np.linspace(0.004, 0.04, 73) / 0.01925   # candidate distances, in units of z0
N_FINE = 41
EDF_REL, EDF_N = 0.012, 25
TWIN_ITERS = 50
CDT = torch.complex64

_Q = {}


def _q(shape, dev, pixel=PIXEL):
    key = (tuple(shape), str(dev), pixel)
    if key not in _Q:
        _Q[key] = freq_sq(shape, dev, pixel)
    return _Q[key]


def normalise(holo, bg, intensity=True):
    """holo [..., h, w] (camera units), bg blank frame of its session -> modulus of the field on the sensor."""
    h = holo.float()
    if not intensity:
        return h / h.mean(dim=(-2, -1), keepdim=True).clamp(min=1e-6)
    return torch.sqrt((h / bg.float().clamp(min=1.0)).clamp(min=0))


def kernel(shape, zs, dev, sign=+1, pixel=PIXEL):
    """exp(sign i pi lambda z |f|^2) for each z of zs -> [K, h, w] complex64 (sign +1 = back-propagation), on a
    grid sampled every `pixel` metres."""
    z = torch.as_tensor(np.asarray(zs, dtype=np.float64), device=dev)[:, None, None]
    return torch.exp(sign * 1j * math.pi * WAVELENGTH * z * _q(shape, dev, pixel)[None]).to(CDT)


def backprop(a, zs, pixel=PIXEL):
    """a [h, w] real, sampled every `pixel` metres -> U [K, h, w]: the field in the object plane at each distance of
    zs."""
    h, w = a.shape[-2:]
    p = fast_pad(a).to(CDT)
    return torch.fft.ifft2(torch.fft.fft2(p)[None] * kernel(p.shape[-2:], zs, a.device, pixel=pixel))[..., :h, :w]


def tog(u, boxes=None, mask=None):
    """Tamura coefficient of the gradient modulus of complex fields u [K, h, w] -> [K] (or [K, nb] in boxes).
    mask: bool [h, w], the pixels that count (default: all)."""
    gx = u[..., :, 1:] - u[..., :, :-1]
    gy = u[..., 1:, :] - u[..., :-1, :]
    g = torch.sqrt(gx[..., :-1, :].abs() ** 2 + gy[..., :, :-1].abs() ** 2)
    if boxes is None:
        g = g.flatten(1) if mask is None else g[:, mask[:-1, :-1]]
        return torch.sqrt(g.std(1) / g.mean(1))
    out = []
    for x0, y0, x1, y1 in boxes:
        r = g[:, y0:y1, x0:x1].flatten(1)
        out.append(torch.sqrt(r.std(1) / r.mean(1).clamp(min=1e-12)))
    return torch.stack(out, 1)


def _chunk(shape):
    return max(1, int(1.5e8 // (shape[-1] * shape[-2])))


def scan(a, zs, pixel=PIXEL, mask=None, sigma=0.0):
    """Sharpness (ToG) of the reconstruction of a at every distance of zs (one FFT of a, one inverse per z).
    pixel: the sampling of a (m); mask: the pixels that count; sigma: Gaussian smoothing of every reconstruction, in
    sensor pixels (it commutes with the propagation, so it is applied once, to the spectrum of a)."""
    h, w = a.shape[-2:]
    A = torch.fft.fft2(fast_pad(a).to(CDT))[None]
    if sigma > 0:
        A = A * torch.exp(-2 * math.pi ** 2 * (sigma * PIXEL) ** 2 * _q(A.shape[-2:], a.device, pixel)).to(CDT)
    c = _chunk(a.shape)
    return torch.cat([tog(torch.fft.ifft2(A * kernel(A.shape[-2:], zs[k:k + c], a.device, pixel=pixel))[..., :h, :w],
                          mask=mask) for k in range(0, len(zs), c)])


@dataclasses.dataclass(frozen=True)
class Focus:
    """One way of finding the distance of a hologram. The defaults are the blind autofocus of the paper."""
    lo: float = None       # search range in units of z0 (None: the blind grid COARSE, 0.2-2.1 z0)
    hi: float = None
    n_coarse: int = len(COARSE)
    n_fine: int = N_FINE   # candidates of the second pass, between the neighbours of the best coarse one (0: none)
    bin: int = 1           # the amplitude is averaged in bin x bin blocks before the search
    mask: float = 0.0      # sharpness only where the blank frame is above this fraction of its maximum (0: everywhere)
    fill: bool = False     # with mask: the amplitude outside it is set to 1 (no object) before it is propagated
    sigma: float = 0.0     # Gaussian smoothing of the reconstructed field before its gradient (sensor pixels)
    every: int = 1         # 1: every hologram; 0: once per session; M > 1: every M images of a session
    first: int = 1         # with every != 1: the median of the search on the first `first` images of each block

    @property
    def candidates(self):
        return COARSE if self.lo is None else np.linspace(self.lo, self.hi, self.n_coarse)

    @property
    def n(self):
        """Reconstructions of one search."""
        return len(self.candidates) + max(self.n_fine, 0)

    @property
    def cost(self):
        """Reconstructions of one search in units of one reconstruction of the whole image (the search runs on
        1 / bin^2 of the pixels)."""
        return self.n / self.bin ** 2


BLIND = Focus()


def autofocus(a, z0=Z0, focus=None, bg=None):
    """Autofocus of one hologram a [h, w] -> z (m) and the number of reconstructions it took. By default blind: the
    candidates span 0.2-2.1 times the nominal distance z0 of the set-up. focus: another search (Focus; its `every`
    and `first` are the business of the caller); bg: the blank frame of the session, for a masked sharpness."""
    f = focus or BLIND
    coarse = f.candidates
    x, pixel, mask = a, PIXEL, None
    if f.mask > 0:
        if bg is None:
            raise ValueError('a masked sharpness needs the blank frame')
        b = torch.as_tensor(np.asarray(bg) if not torch.is_tensor(bg) else bg, device=a.device).float()
        mask = b >= f.mask * b.max()
        if f.fill:
            x = torch.where(mask, x, torch.ones_like(x))
    if f.bin > 1:
        x = F.avg_pool2d(x[None, None], f.bin)[0, 0]
        pixel = PIXEL * f.bin
        if mask is not None:
            mask = F.avg_pool2d(mask[None, None].float(), f.bin)[0, 0] > 0.999

    def best(cand):
        return int(scan(x, z0 * cand, pixel, mask, f.sigma).argmax())
    c = float(coarse[best(coarse)])
    if f.n_fine <= 0:
        return z0 * c, len(coarse)
    step = coarse[1] - coarse[0]
    fine = np.linspace(c - step, c + step, f.n_fine)
    return z0 * float(fine[best(fine)]), len(coarse) + f.n_fine


def int_boxes(xyxy, shape, buffer=0.25):
    from holo_openset.model import square_boxes
    b = square_boxes(xyxy, buffer).round().astype(int)
    h, w = shape
    return [(max(0, x0), max(0, y0), min(w, x1), min(h, y1)) for x0, y0, x1, y1 in b]


def per_object(a, z, xyxy, rel=EDF_REL, n=EDF_N):
    """Extended depth of field: each box taken from the reconstruction (+-1.2 % of z, 25 steps, unless rel and n say
    otherwise) in which it is sharpest. -> composite U [h, w], the distance chosen for each box."""
    zs = z * (1 + np.linspace(-rel, rel, n))
    boxes = int_boxes(xyxy, a.shape)
    h, w = a.shape[-2:]
    A = torch.fft.fft2(fast_pad(a).to(CDT))[None]
    c = _chunk(a.shape)
    best = [-1.0] * len(boxes)
    kbest = [n // 2] * len(boxes)
    region = [None] * len(boxes)
    out = None
    for k in range(0, n, c):   # the stack is scanned in chunks: on a full frame it does not fit at once
        u = torch.fft.ifft2(A * kernel(A.shape[-2:], zs[k:k + c], a.device))[..., :h, :w]
        if k <= n // 2 < k + c:
            out = u[n // 2 - k].clone()
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
    h, w = a.shape[-2:]
    a = fast_pad(a)
    back = kernel(a.shape[-2:], [z], a.device)[0]
    fwd = torch.conj(back)
    phase = torch.zeros_like(a)
    for k in range(1, iters + 1):
        u = torch.fft.ifft2(torch.fft.fft2(a * torch.exp(1j * phase)) * back)
        m = u.abs()
        u = torch.where(m > 1, u / m.clamp(min=1e-12), u)       # absorption cannot be negative
        if trace:
            trace(k, u[..., :h, :w])
        if k < iters:
            phase = torch.angle(torch.fft.ifft2(torch.fft.fft2(u) * fwd))
    return u[..., :h, :w]


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


METHODS = ('z0', 'af', 'edf', 'twin')   # the reconstructions of the paper

# The ways of finding the distance compared in the distance study, by cache name (rec_<name>.npy). The free choices
# (how many images a session is focused on, how often a drifting distance is refocused, the cheap and the robust
# searches) were made on the VALIDATION split and frozen before any of them met the test split: see
# docs/exp_distancia/CADERNO.md for the sweep, the rules and the dates.
FOCUS = {
    # when: the blind search of the paper, once per session on its first image, or every 10 images of a session
    'afs': Focus(every=0, first=1),
    'afM': Focus(every=10),
    # how, on every hologram: the cheapest search that finds the distance on validation (+-10 % of z0, 7 + 11
    # candidates, amplitude averaged 4 x 4), which is also the cheapest that resists noise and a narrow beam; and the
    # one with the fewest gross failures under noise (+-15 %, 15 + 21, averaged 2 x 2, field smoothed by 2 px)
    'afc': Focus(lo=0.90, hi=1.10, n_coarse=7, n_fine=11, bin=4),
    'afr': Focus(lo=0.85, hi=1.15, n_coarse=15, n_fine=21, bin=2, sigma=2.0),
    # the cheap search once per session
    'afsc': Focus(lo=0.90, hi=1.10, n_coarse=7, n_fine=11, bin=4, every=0, first=1),
}
# per-object focus over a range wide enough for a tilted slide: name -> (relative half range, steps)
EDF = {'edf': (EDF_REL, EDF_N), 'edfw': (0.06, 49)}


class Holograms:
    """Holograms of a set (or of its auxiliary scenes), each with the blank frame of its session and its boxes."""

    def __init__(self, root, aux=None):
        self.root = Path(root)
        cfg = json.load(open(self.root / 'physics.json'))
        self.intensity = cfg['physics']['intensity']
        self.z0 = cfg['physics'].get('z0', Z0)
        self.pixel = cfg.get('pixel', PIXEL)   # a set reduced b x b (holo_openset.resolution): b x the sensor's
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

    def blank(self, i, dev):
        return torch.from_numpy(np.array(self.bg[self.session.get(i, 0)])).to(dev)

    def amplitude(self, i, dev):
        h = torch.from_numpy(np.array(self.holo[self.row[i]])).to(dev)
        b = torch.from_numpy(np.array(self.bg[self.session.get(i, 0)])).to(dev)
        return normalise(h, b, self.intensity)


def reconstruct(a, method, z_af=None, boxes=None, z0=Z0, pixel=PIXEL):
    """One hologram amplitude a [h, w] -> U [h, w] by a method of METHODS (z_af: the autofocus distance; pixel: the
    sampling of a, for 'z0' only)."""
    if method == 'z0':
        return backprop(a, [z0], pixel)[0]
    if pixel != PIXEL:
        raise ValueError(f'{method} is implemented at the pixel of the sensor only')
    if method == 'af':
        return backprop(a, [z_af])[0]
    if method == 'edf':
        return per_object(a, z_af, boxes if boxes is not None else np.zeros((0, 4)))[0]
    if method == 'twin':
        return remove_twin(a, z_af)
    raise ValueError(method)


def focus_blocks(ids, session, focus):
    """Who is focused and who reuses the distance: [(images that share one distance, the ones it is searched on)].
    Images are taken in the order of their ids within each session (ids are contiguous per session), so the first
    image of a session is the one with the smallest id of that session in the set."""
    ids = [int(i) for i in ids]
    if focus.every == 1:
        return [([i], [i]) for i in ids]
    by = {}
    for i in sorted(ids):
        by.setdefault(session[i], []).append(i)
    out = []
    for members in by.values():
        size = len(members) if focus.every == 0 else focus.every
        out += [(members[k:k + size], members[k:k + size][:focus.first]) for k in range(0, len(members), size)]
    return out


def distances(src, focus, dev, ids=None, log=None):
    """The distance at which each hologram of src is reconstructed under a way of focusing -> one row per image, in
    the order of ids: image_id, session, true_z, z_af (the distance used) and n_reconstructions (what the search cost
    on THIS image: 0 when it reuses the distance found on another)."""
    ids = [int(i) for i in (src.ids if ids is None else ids)]
    rows = {}
    for b, (members, focused) in enumerate(focus_blocks(ids, src.session, focus)):
        found = {}
        for i in focused:
            found[i] = autofocus(src.amplitude(i, dev), src.z0, focus, src.blank(i, dev) if focus.mask > 0 else None)
        z = float(np.median([v[0] for v in found.values()]))
        for i in members:
            rows[i] = dict(image_id=i, session=src.session.get(i), true_z=src.true_z.get(i), z_af=z,
                           n_reconstructions=found[i][1] if i in found else 0)
        if log and b % 500 == 0:
            log(f'focus {len(rows)}/{len(ids)}')
    return [rows[i] for i in ids]


def build_caches(root, methods, dev, aux=None, log=print):
    """Write <root>/rec_<method>.npy (or <root>/aux/<aux>_rec_<method>.npy), uint8 [N, 3, h, w], and the autofocus
    log (autofocus.csv / aux/<aux>_autofocus.csv). The per-object method uses the annotated boxes.
    The methods of FOCUS write their own log, autofocus_<method>.csv, and leave autofocus.csv alone; so do the
    per-object methods of the study in EDF (edfw: blind autofocus, then the per-object focus over its own range, as
    on the full frames)."""
    wide = [m for m in methods if m in EDF and m not in METHODS]
    unknown = [m for m in methods if m not in METHODS and m not in FOCUS and m not in wide]
    if unknown:
        raise SystemExit(f'unknown reconstruction {unknown}: one of {list(METHODS) + list(FOCUS) + list(EDF)}')
    study = [m for m in methods if m in FOCUS]
    methods = [m for m in methods if m in METHODS]
    src = Holograms(root, aux)
    if src.pixel != PIXEL and (set(methods) - {'z0'} or wide or study):
        raise SystemExit(f'{root} is reduced (pixel {src.pixel * 1e6:.2f} um): only the back-propagation at z0 '
                         'uses the effective pixel so far')
    pre = f"{src.root / 'aux' / aux}_" if aux else f'{src.root}/'
    h, w = src.holo.shape[1:]
    for m in wide:
        arr = np.lib.format.open_memmap(f'{pre}rec_{m}.npy', mode='w+', dtype=np.uint8, shape=(len(src.ids), 3, h, w))
        rows = []
        for k, i in enumerate(src.ids):
            i = int(i)
            a = src.amplitude(i, dev)
            z_af, n = autofocus(a, src.z0)
            u, zb = per_object(a, z_af, src.boxes.get(i, np.zeros((0, 4))), *EDF[m])
            arr[k] = channels(u).cpu().numpy()
            rows.append(dict(image_id=i, true_z=src.true_z.get(i), z_af=z_af, n_reconstructions=n,
                             z_objects=';'.join(f'{v:.7f}' for v in zb)))
            if k % 500 == 0:
                log(f'{m} {k}/{len(src.ids)}')
        arr.flush()
        pd.DataFrame(rows).to_csv(f'{pre}autofocus_{m}.csv', index=False)
    for m in study:
        if aux and FOCUS[m].every != 1:
            raise SystemExit(f'{m} reuses a distance within a session; the auxiliary scenes are not acquired in order')
        arr = np.lib.format.open_memmap(f'{pre}rec_{m}.npy', mode='w+', dtype=np.uint8, shape=(len(src.ids), 3, h, w))
        rows = distances(src, FOCUS[m], dev, log=log)
        for k, r in enumerate(rows):
            arr[k] = channels(backprop(src.amplitude(r['image_id'], dev), [r['z_af']])[0]).cpu().numpy()
            if k % 500 == 0:
                log(f'{m} {k}/{len(rows)}')
        arr.flush()
        pd.DataFrame(rows).to_csv(f'{pre}autofocus_{m}.csv', index=False)
    if not methods:
        return
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
                u = reconstruct(a, m, z_af, z0=src.z0, pixel=src.pixel)
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
