"""Z6.3 (a): does the simulator, which propagates the field on a grid with the pitch of the sensor and applies the
pixel aperture as a filter (sim/physics.py: freq_sq, coherence_mtf), record what an honest simulation would at small
z? An honest recording: the same single letter (the same raster, each pixel an s x s block) on a grid s times finer
(pitch 1.67 um / s), the
same physics (7 wavelengths of the 10 nm band, the image of the pinhole), the pixel aperture as the mean over s x s
blocks (which also aliases what lies above the Nyquist frequency of the sensor, as a real sensor does). Measured:
  above_nyquist   share of the pattern energy (I - 1)^2 of the fine recording, before the pixel, above 299 cycles/mm
                  (either axis), and after the pixel mean (what aliases)
  rel_rms         rms of (native - honest) over the rms of the honest pattern, on the window
  time / memory   of one recording of the single letter on the GPU (a proxy for one window: the transforms dominate)
Nothing is saved but the table: $HOLO_RESULTS/sim_sampling.csv.

    python scripts/exp_resolucao/sim_sampling.py --device cuda:N
"""
import argparse
import math
import time

import numpy as np
import pandas as pd
import torch
from scipy.special import j1

from holo_openset import paths
from holo_openset.model import pick_device
from holo_openset.sim.letters import FONTS, letter_mask
from holo_openset.sim.physics import PIXEL, Physics, sensor_intensity, wavelengths

WINDOW, MARGIN = 640, 256


def fine_recording(mask_fine, s, z, phys, dev, pos, window=WINDOW, margin=MARGIN):
    """Intensity of one absorbing letter (a = 0.6) at the centre, on a grid of pitch PIXEL / s, side (window + 2 margin) s,
    with the image of the pinhole; -> (fine intensity on the window, before the pixel; recording: mean over s x s)."""
    n = (window + 2 * margin) * s
    p = PIXEL / s
    obj = torch.zeros(n, n, dtype=torch.complex64, device=dev)
    h, w = mask_fine.shape
    y0, x0 = pos[0] * s, pos[1] * s   # the native canvas position of the letter, on the fine grid
    obj[y0:y0 + h, x0:x0 + w] = torch.as_tensor(mask_fine, device=dev).to(torch.complex64) * (0.4 - 1)
    fy = torch.fft.fftfreq(n, d=p, device=dev, dtype=torch.float64)
    q = fy[None, :] ** 2 + fy[:, None] ** 2
    S = torch.fft.fft2(obj)
    inten = torch.zeros(n, n, dtype=torch.float64, device=dev)
    for lam, wgt in wavelengths(phys):
        u = 1 + torch.fft.ifft2(S * torch.exp(-1j * (math.pi * lam * z) * q).to(torch.complex64))
        inten += wgt * (u.abs() ** 2).double()
    d = phys.pinhole * z / phys.source_distance
    x = (math.pi * d * torch.sqrt(q)).cpu().numpy()
    airy = torch.from_numpy(np.where(x > 1e-9, 2 * j1(x) / np.maximum(x, 1e-9), 1.0)).to(dev)
    inten = torch.fft.ifft2(torch.fft.fft2(inten) * airy).real
    m = margin * s
    fine = inten[m:m + window * s, m:m + window * s]
    rec = fine.reshape(window, s, window, s).mean((1, 3))
    return fine, rec


def above_nyquist(img, pitch):
    e = torch.fft.fft2(img - 1).abs() ** 2
    f = torch.fft.fftfreq(img.shape[0], d=pitch, device=img.device, dtype=torch.float64).abs()
    hi = (f[None, :] > 1 / (2 * PIXEL)) | (f[:, None] > 1 / (2 * PIXEL))
    return float(e[hi].sum() / e.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--device', default='cpu')
    a = ap.parse_args()
    torch.set_num_threads(4)
    dev = pick_device(a.device)
    phys = Physics().replace(window=(WINDOW, WINDOW), margin=MARGIN, dust_density=0, sensor_dust_density=0)
    rows = []
    for name, fs in [('base p50 (77 px)', 106), ('small p50 (28 px)', 38)]:
        for zmm in [0.7, 1.0, 2.0, 19.25]:
            z = zmm * 1e-3
            m1 = np.asarray(letter_mask('F', FONTS[0], fs, 0), np.float32) / 255
            o = dict(mask=m1, absorption=0.6, phase=0.0, x=MARGIN + (WINDOW - m1.shape[1]) // 2,
                     y=MARGIN + (WINDOW - m1.shape[0]) // 2, depth=0.0, kind='letter')
            big = phys if zmm < 5 else phys.replace(margin=1728)   # the simulator's own margin at 19.25 mm
            if zmm >= 5:
                o.update(x=1728 + (WINDOW - m1.shape[1]) // 2, y=1728 + (WINDOW - m1.shape[0]) // 2)
            native = sensor_intensity(dict(objects=[o], dust=[], sensor_dust=[]), dict(z=z), big, dev)
            for s in (2, 3, 4):
                mf = np.kron(m1, np.ones((s, s), np.float32))   # the same object, sampled s times finer
                if dev.type == 'cuda':
                    torch.cuda.synchronize()
                    torch.cuda.reset_peak_memory_stats()
                t0 = time.time()
                fine, rec = fine_recording(mf, s, z, phys, dev, (o['y'], o['x']), margin=MARGIN if zmm < 5 else 1728)
                if dev.type == 'cuda':
                    torch.cuda.synchronize()
                dt = time.time() - t0
                mem = torch.cuda.max_memory_allocated() / 2 ** 30 if dev.type == 'cuda' else math.nan
                diff = native - rec
                rows.append(dict(letter=name, z_mm=zmm, s=s, side_px=max(m1.shape),
                                 above_nyquist_fine=above_nyquist(fine, PIXEL / s),
                                 above_nyquist_native=above_nyquist(native, PIXEL),
                                 rel_rms_native_vs_honest=float(diff.std() / (rec - 1).std()),
                                 pattern_energy_ratio=float(((native - 1) ** 2).sum() / ((rec - 1) ** 2).sum()),
                                 grid=(WINDOW + 2 * (MARGIN if zmm < 5 else 1728)) * s, seconds=dt, peak_gib=mem))
                print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(paths.RESULTS / 'sim_sampling.csv', index=False, float_format='%.5g')


if __name__ == '__main__':
    main()
