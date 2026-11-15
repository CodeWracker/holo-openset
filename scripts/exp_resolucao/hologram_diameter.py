"""The effective diameter of the hologram of one letter of the 1.0 mm sets, and the overlap ratio of Seo et al. 2009
(CADERNO_CURVA.md, Q0, "Diâmetro efetivo do holograma e razão de sobreposição"). No data set is read; nothing of a
test split enters.

Letters: 260 isolated letters (10 of each class) drawn with the laws of the layout of bench_1mm (FresnelLayout of its
physics.json: continuous font size, font, rotation, absorption and phase of the set; master raster 16x), seed SEED,
depth 0 (the sample plane), each alone at the centre of a 768 x 768 window (margin 394: the disc of R = 256 px and the
reach of the finest fringe stay inside the canvas, no wrap of the FFT), z = 1.0 mm, the recorder of the set (s = 4,
the LED band and the pinhole), no noise, no dust, no sensor dust, no beam profile. Pattern p = I / B - 1 (B: the same
recording without the letter), energy e = p^2.

Per letter, around the centroid of e (computed in the disc of 256 px around the centre of the window):
  D_rms(R)  2 sqrt(2) sqrt(sum e r^2 / sum e) over the disc of radius R (R = 96, 128, 192, 256 px): the D4sigma
            convention (the diameter of a uniform disc)
  D_vis     2 x the radius from which the azimuthal mean of sqrt(e) (1 px rings) stays below the noise of the set
            (NOISE = 2.1 grey levels in 101.5 = 2.07 % of the mean level) out to R_OUT = 352 px
  D_86      the diameter of the disc that holds 86.5 % of the energy inside R = 256 px
  side      the larger side of the ink box (px)
Set: D_ef^2 = mean over pairs i != j of ((D_i + D_j) / 2)^2 for D_rms(192), D_vis, D_86 (and the other R, for the
record). Axis (rule of Q0): D_rms(192) if D_rms(256) differs from it by at most 5 % (checked on D_ef, and reported per
letter), else D_vis. Overlap ratio 1 - exp(-pi D_ef^2 sigma) for sigma = 7, 13, 60, 135, 300 per mm^2.
-> $HOLO_RESULTS/hologram_diameter.csv, hologram_diameter_summary.json, docs/exp_resolucao/img/hologram_diameter.png

    python scripts/exp_resolucao/hologram_diameter.py --device cuda:N
"""
import argparse
import json
import math
import random
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np   # noqa: E402
import pandas as pd   # noqa: E402
import torch   # noqa: E402

from holo_openset import paths   # noqa: E402
from holo_openset.model import pick_device   # noqa: E402
from holo_openset.sim.generate import layout_of   # noqa: E402
from holo_openset.sim.letters import CLASSES, FONTS, letter_master   # noqa: E402
from holo_openset.sim.physics import PIXEL, physics_from_dict, sensor_intensity   # noqa: E402
from holo_openset.sim.scene import material, physical_object   # noqa: E402

SEED = 20261115
PER_CLASS = 10
WINDOW, MARGIN = 768, 394
RADII = [96, 128, 192, 256]
R_OUT = 352
NOISE = 2.1 / 101.5
SIGMAS = [7, 13, 60, 135, 300]   # objects per mm^2
IMG = paths.PROJECT / 'docs' / 'exp_resolucao' / 'img'


def measures(e):
    """The measures of one energy map e (float64 [h, w], the letter near the centre) -> dict, radial profile."""
    h, w = e.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    c0 = ((h - 1) / 2, (w - 1) / 2)
    disc = (yy - c0[0]) ** 2 + (xx - c0[1]) ** 2 <= 256 ** 2
    cy, cx = (e * yy)[disc].sum() / e[disc].sum(), (e * xx)[disc].sum() / e[disc].sum()
    r = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    out = dict(cy_off=cy - c0[0], cx_off=cx - c0[1])
    for R in RADII:
        m = r <= R
        out[f'D_rms_{R}'] = 2 * math.sqrt(2) * math.sqrt((e[m] * r[m] ** 2).sum() / e[m].sum())
    ring = np.floor(r).astype(int)
    amp = np.sqrt(e)
    n = np.bincount(ring.ravel(), minlength=R_OUT + 1)[:R_OUT + 1]
    prof = np.bincount(ring.ravel(), weights=amp.ravel(), minlength=R_OUT + 1)[:R_OUT + 1] / np.maximum(n, 1)
    above = np.nonzero(prof >= NOISE)[0]
    out['r_vis'] = float(above.max() + 1) if len(above) else 0.0
    out['D_vis'] = 2 * out['r_vis']
    m = r <= 256
    ord_ = np.argsort(r[m])
    cum = np.cumsum(e[m][ord_])
    k = np.searchsorted(cum, 0.865 * cum[-1])
    out['D_86'] = 2 * float(r[m][ord_][k])
    out['vis_at_R_OUT'] = bool(prof[-1] >= NOISE)
    return out, prof


def pair_rule(d):
    """sqrt(mean over pairs i != j of ((d_i + d_j) / 2)^2)."""
    d = np.asarray(d, float)
    s, s2, n = d.sum(), (d ** 2).sum(), len(d)
    pairs = (s ** 2 - s2) / 2      # sum over i < j of d_i d_j
    tot = ((n - 1) * s2 + 2 * pairs) / 4   # sum over i < j of (d_i + d_j)^2 / 4
    return math.sqrt(tot / (n * (n - 1) / 2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--set', default='bench_1mm', help='the set whose layout and physics give the laws')
    a = ap.parse_args()
    torch.set_num_threads(4)
    dev = pick_device(a.device)
    cfg = json.load(open(paths.dataset(a.set) / 'physics.json'))
    lay = layout_of(cfg)
    phys = physics_from_dict(cfg['physics']).replace(
        window=(WINDOW, WINDOW), margin=MARGIN, reach=0, depth_std=0.0, depth_max=0.0, dust_density=0.0,
        sensor_dust_density=0.0, full_well=0.0, read_noise=0.0, prnu=0.0, bits=0)
    ses = dict(z=1.0e-3)
    f = lay.factor
    rng = random.Random(SEED)
    blank = sensor_intensity(dict(objects=[], dust=[], sensor_dust=[]), ses, phys, dev, sample=False).cpu().numpy()
    rows, profs = [], []
    t0 = time.time()
    for letter in CLASSES:
        for k in range(PER_CLASS):
            size, font = rng.uniform(lay.font_min, lay.font_max), rng.choice(FONTS)
            angle = rng.uniform(-lay.rotation, lay.rotation)
            master = letter_master(letter, font, size * f, angle)
            mat = material(rng, phys)
            mat['depth'] = 0.0
            c = MARGIN + WINDOW / 2
            o = physical_object(master, round(c * f - master.shape[1] / 2), round(c * f - master.shape[0] / 2), f,
                                kind='letter', classe=letter, **mat)
            inten = sensor_intensity(dict(objects=[o], dust=[], sensor_dust=[]), ses, phys, dev).cpu().numpy()
            e = (inten / blank - 1) ** 2
            m, prof = measures(e)
            side = max(master.shape) / f
            rows.append(dict(classe=letter, k=k, font=font.stem, font_size=size, rotation=angle,
                             absorption=mat['absorption'], phase=mat['phase'], side_px=side, **m))
            profs.append(prof)
        print(letter, f'{time.time() - t0:.0f} s', {q: round(rows[-1][q], 1) for q in
                                                     ['side_px', 'D_rms_192', 'D_rms_256', 'D_vis', 'D_86']}, flush=True)
    t = pd.DataFrame(rows)
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    t.to_csv(paths.RESULTS / 'hologram_diameter.csv', index=False, float_format='%.6g')
    um = PIXEL * 1e6
    cols = ['side_px'] + [f'D_rms_{R}' for R in RADII] + ['D_vis', 'D_86']
    stats = {c: dict(mean=float(t[c].mean()), median=float(t[c].median()), p5=float(t[c].quantile(.05)),
                     p95=float(t[c].quantile(.95)), min=float(t[c].min()), max=float(t[c].max())) for c in cols}
    d_ef = {c: pair_rule(t[c]) for c in cols[1:]}
    conv_set = abs(d_ef['D_rms_256'] - d_ef['D_rms_192']) / d_ef['D_rms_192']
    conv_letters = (t.D_rms_256 - t.D_rms_192).abs() / t.D_rms_192
    axis = 'D_rms_192' if conv_set <= 0.05 else 'D_vis'
    overlap = {c: {str(s): 1 - math.exp(-math.pi * (d_ef[c] * PIXEL * 1e3) ** 2 * s) for s in SIGMAS}
               for c in ['D_rms_192', 'D_vis', 'D_86', 'D_rms_256']}
    summary = dict(
        seed=SEED, letters=len(t), per_class=PER_CLASS, laws_from=a.set, z_mm=1.0, oversample=phys.oversample,
        window=WINDOW, margin=MARGIN, noise_level=NOISE, r_out=R_OUT, pixel_um=um, stats_px=stats,
        D_ef_px=d_ef, D_ef_um={c: v * um for c, v in d_ef.items()},
        convergence=dict(rule='D_rms(256) within 5 % of D_rms(192), on D_ef', rel_diff_D_ef=conv_set,
                         rel_diff_letters_median=float(conv_letters.median()),
                         rel_diff_letters_p95=float(conv_letters.quantile(.95)),
                         letters_within_5pct=float((conv_letters <= 0.05).mean())),
        axis=axis, letters_visible_at_r_out=int(t.vis_at_R_OUT.sum()),
        overlap_ratio=overlap, sigmas_per_mm2=SIGMAS, seconds=time.time() - t0)
    json.dump(summary, open(paths.RESULTS / 'hologram_diameter_summary.json', 'w'), indent=1)
    print(json.dumps(summary, indent=1))
    # figure: radial profile of sqrt(e) for a few letters against the noise
    fig, ax = plt.subplots(figsize=(7, 4.2), constrained_layout=True)
    pick = t.side_px.sort_values().index[np.linspace(0, len(t) - 1, 6).astype(int)]
    for i in pick:
        ax.semilogy(np.arange(R_OUT + 1), np.maximum(profs[i], 1e-6), lw=1,
                    label=f"{t.classe[i]}, side {t.side_px[i]:.1f} px, D_rms(192) {t.D_rms_192[i]:.0f}, "
                          f"D_vis {t.D_vis[i]:.0f}, D_86 {t.D_86[i]:.0f}")
    ax.axhline(NOISE, color='k', ls='--', lw=0.8, label='noise of the set (2.1 / 101.5)')
    for R in RADII:
        ax.axvline(R, color='0.8', lw=0.6, zorder=0)
    ax.set_xlabel('radius from the energy centroid (px of 1.67 um)')
    ax.set_ylabel('azimuthal mean of |I / B - 1|')
    ax.set_ylim(1e-4, 2)
    ax.set_title('One isolated letter at 1.0 mm (s = 4, no noise): radial profile of the pattern', fontsize=9)
    ax.legend(fontsize=6.5, loc='upper right')
    IMG.mkdir(parents=True, exist_ok=True)
    fig.savefig(IMG / 'hologram_diameter.png', dpi=150)
    print('wrote', IMG / 'hologram_diameter.png')


if __name__ == '__main__':
    main()
