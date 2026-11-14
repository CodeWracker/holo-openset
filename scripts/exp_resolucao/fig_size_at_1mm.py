"""Z9: at z = 1 mm, is there a holographic pattern at all? It depends on the size of the object.
One absorbing letter F (a = 0.6) of four sizes at 1 mm, against the median letter of the base set at 19.25 mm. The
1 mm recordings are honest (field on a grid 4x finer than the pixel, pixel = mean over 4 x 4, as in sim_sampling.py);
the 19.25 mm one is the simulator's own (there the two agree to 0.1-0.4 %, sim_sampling.csv). Share outside the crop:
pattern energy (I - 1)^2 outside the box + 25 % margin, over the 640 x 640 window (2048 x 2048 at 19.25 mm).
Writes only the figure.

    python scripts/exp_resolucao/fig_size_at_1mm.py docs/exp_resolucao/img/pattern_size_at_1mm.png cuda:N
"""
import math
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import torch
from scipy.special import j1

from holo_openset.sim.letters import FONTS, letter_mask
from holo_openset.sim.physics import PIXEL, WAVELENGTH, Physics, sensor_intensity, wavelengths

OUT = sys.argv[1]
DEV = torch.device(sys.argv[2])
S = 4
WINDOW, MARGIN = 640, 256
torch.set_num_threads(4)


def mask_of_side(side, scale=1):
    best = None
    for fs in range(8, 900):
        m = np.asarray(letter_mask('F', FONTS[0], fs, 0), np.float32) / 255
        d = abs(max(m.shape) - side * scale)
        if best is None or d < best[0]:
            best = (d, m)
        if max(m.shape) > side * scale + 2 * scale:
            break
    return best[1]


def fine(mask_fine, z, phys):
    n = (WINDOW + 2 * MARGIN) * S
    p = PIXEL / S
    obj = torch.zeros(n, n, dtype=torch.complex64, device=DEV)
    h, w = mask_fine.shape
    y0, x0 = (n - h) // 2, (n - w) // 2
    obj[y0:y0 + h, x0:x0 + w] = torch.as_tensor(mask_fine, device=DEV).to(torch.complex64) * (0.4 - 1)
    f = torch.fft.fftfreq(n, d=p, device=DEV, dtype=torch.float64)
    q = f[None, :] ** 2 + f[:, None] ** 2
    sp = torch.fft.fft2(obj)
    inten = torch.zeros(n, n, dtype=torch.float64, device=DEV)
    for lam, wgt in wavelengths(phys):
        u = 1 + torch.fft.ifft2(sp * torch.exp(-1j * (math.pi * lam * z) * q).to(torch.complex64))
        inten += wgt * (u.abs() ** 2).double()
    d = phys.pinhole * z / phys.source_distance
    x = (math.pi * d * torch.sqrt(q)).cpu().numpy()
    airy = torch.from_numpy(np.where(x > 1e-9, 2 * j1(x) / np.maximum(x, 1e-9), 1.0)).to(DEV)
    inten = torch.fft.ifft2(torch.fft.fft2(inten) * airy).real
    m = MARGIN * S
    win = inten[m:m + WINDOW * S, m:m + WINDOW * S]
    return win.reshape(WINDOW, S, WINDOW, S).mean((1, 3)).cpu().numpy()


def native(mask, z):
    phys = Physics().replace(window=(2048, 2048), margin=1024, dust_density=0, sensor_dust_density=0)
    o = dict(mask=mask, absorption=0.6, phase=0.0, x=1024 + (2048 - mask.shape[1]) // 2,
             y=1024 + (2048 - mask.shape[0]) // 2, depth=0.0, kind='letter')
    return sensor_intensity(dict(objects=[o], dust=[], sensor_dust=[]), dict(z=z), phys, DEV).cpu().numpy()


def outside(img, side, margin=0.25):
    e = (img - 1) ** 2
    c = img.shape[0] // 2
    a, b = int(c - side * (1 + margin) / 2), int(c + side * (1 + margin) / 2)
    return 1 - e[a:b, a:b].sum() / e.sum()


phys = Physics().replace(window=(WINDOW, WINDOW), margin=MARGIN, dust_density=0, sensor_dust_density=0)
panels = []
m = mask_of_side(77)
img = native(m, 19.25e-3)
panels.append(('(a) letter of 129 µm at 19.25 mm\n(the base set today)', img, max(m.shape), 19.25))
for tag, side in (('(b)', 77), ('(c)', 28), ('(d)', 15), ('(e)', 9)):
    mf = mask_of_side(side, S)
    s = max(mf.shape) / S
    img = fine(mf, 1e-3, phys)
    panels.append((f'{tag} letter of {s * PIXEL * 1e6:.0f} µm at 1 mm', img, s, 1.0))

fig, axes = plt.subplots(1, len(panels), figsize=(3.1 * len(panels), 3.6), constrained_layout=True)
for ax, (title, img, s, zmm) in zip(axes, panels):
    nf = (s * PIXEL / 2) ** 2 / (WAVELENGTH * zmm * 1e-3)
    out = outside(img, s)
    print(f'{title!r}: side {s:.1f} px, N_F {nf:.2f}, outside crop {out:.3f}, contrast rms {np.sqrt(((img - 1) ** 2).mean()):.4f}')
    c, r = img.shape[0] // 2, int(round(2.6 * s))
    v = img[c - r:c + r, c - r:c + r]
    ax.imshow(v, cmap='gray', vmin=np.percentile(v, 0.5), vmax=np.percentile(v, 99.5), interpolation='nearest')
    for k, ls in ((1.0, '-'), (1.25, '--')):
        h = s * k / 2
        ax.add_patch(plt.Rectangle((r - h - 0.5, r - h - 0.5), 2 * h, 2 * h, fill=False, ec='#e6550d', lw=0.9, ls=ls))
    ax.set_title(f'{title}\nFresnel number {nf:.2f} · {100 * out:.0f} % outside the crop', fontsize=8, loc='left')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel(f'field shown: {2 * r * PIXEL * 1e6:.0f} µm ({2 * r} pixels)', fontsize=7)
fig.savefig(OUT, dpi=200, bbox_inches='tight')
print('wrote', OUT)
