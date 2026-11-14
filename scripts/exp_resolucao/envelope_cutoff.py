"""The factor b from the model of the bench (docs/exp_resolucao/PROTOCOLO.md, A.2.1): the envelope E(f) of the source and
the pixel (eq. envelope of the paper, the same numbers as fig_fresnel panel b), its cut-off f_c (the lowest radial
frequency, along a sensor axis, at which |E| falls below a threshold) and b_max = floor(1 / (2 pixel f_c)).
Writes $HOLO_RESULTS/envelope_cutoff.csv and $HOLO_RESULTS/envelope_curve.csv.

    python scripts/exp_resolucao/envelope_cutoff.py
"""
import math

import numpy as np
import pandas as pd
from scipy.special import j1

from holo_openset import paths
from holo_openset.sim.physics import PIXEL, WAVELENGTH, Physics

P = Physics()
DISTANCES = {'base (z0 = 19.25 mm)': P.z0, 'small_near (z = 2 mm)': 2e-3}
THRESHOLDS = (0.1, 0.05)
NYQUIST = 1 / (2 * PIXEL)


def components(f, z, phys=P):
    """bandwidth, pinhole image and pixel factors of E at radial frequency f (1/m) along a sensor axis."""
    sig = phys.bandwidth / (2 * math.sqrt(2 * math.log(2))) / WAVELENGTH
    band = np.exp(-0.5 * (math.pi * WAVELENGTH * z * f ** 2 * sig) ** 2)
    d = phys.pinhole * z / phys.source_distance
    x = math.pi * d * f
    airy = np.where(x > 1e-12, 2 * j1(x) / np.maximum(x, 1e-12), 1.0)
    pix = np.sinc(f * PIXEL)
    return band, airy, pix


def main():
    f = np.linspace(0, NYQUIST, 299001)   # steps of about 0.001 cycles/mm
    rows, curve = [], {'f_cyc_per_mm': f / 1e3}
    for name, z in DISTANCES.items():
        band, airy, pix = components(f, z)
        e = band * airy * pix
        curve[f'E_{z * 1e3:g}mm'] = e
        for thr in THRESHOLDS:
            below = np.abs(e) < thr
            k = int(np.argmax(below)) if below.any() else None
            fc = f[k] if k is not None else np.nan
            stays = bool(below[k:].all()) if k is not None else False
            bmax = math.floor(1 / (2 * PIXEL * fc)) if k is not None else 1
            rows.append(dict(set=name, z_mm=z * 1e3, threshold=thr, f_c_cyc_per_mm=fc / 1e3,
                             stays_below_up_to_nyquist=stays, b_max=bmax,
                             band_at_fc=float(band[k]) if k is not None else np.nan,
                             pinhole_at_fc=float(airy[k]) if k is not None else np.nan,
                             pixel_at_fc=float(pix[k]) if k is not None else np.nan,
                             pinhole_image_um=P.pinhole * z / P.source_distance * 1e6,
                             E_at_nyquist=float(e[-1]),
                             E_at_nyquist_diagonal=float(np.prod(components(np.array([NYQUIST * math.sqrt(2)]), z)[:2])
                                                         * np.sinc(0.5) ** 2)))
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    t = pd.DataFrame(rows)
    t.to_csv(paths.RESULTS / 'envelope_cutoff.csv', index=False, float_format='%.6g')
    pd.DataFrame(curve).iloc[::100].to_csv(paths.RESULTS / 'envelope_curve.csv', index=False, float_format='%.6g')
    pd.set_option('display.width', 250)
    print(t.to_string(index=False))


if __name__ == '__main__':
    main()
