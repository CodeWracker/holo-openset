"""Z6.2: how much of the pattern of one letter stays inside its crop, against the sample-to-sensor distance z (the premise
P2 of the paper). Same definition as fig_fresnel (c), whose 25 % value is the macro \\CropEnergyBench / Coherent:
one absorbing letter (a = 0.6, no phase) at the centre of a 2048 x 2048 window (margin 1024, no dust, no noise),
pattern energy e = (I - 1)^2, share = energy inside a square of side max(box) x (1 + margin) centred on the window
over the energy in the whole window; the source of the bench (10 nm, pinhole 100 um at 15 cm, pixel aperture) and a
point monochromatic source without pixel aperture. Letters F, A, O, W (DejaVuSans, upright), each rendered at the font
size whose box side is the target. Nothing is recorded to disk but the table and the figures.
Writes $HOLO_RESULTS/pattern_in_crop_z.csv, docs/exp_resolucao/img/pattern_in_crop_z.png and pattern_examples.png.

    python scripts/exp_resolucao/pattern_in_crop.py --device cuda:N
"""
import argparse
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.model import pick_device
from holo_openset.paper.style import COLORS, INK, MUTED, setup
from holo_openset.sim.letters import FONTS, letter_mask
from holo_openset.sim.physics import PIXEL, WAVELENGTH, Physics, sensor_intensity

ZS_MM = [0.7, 1.0, 1.5, 2.0, 5.0, 19.25]
# box sides (px): p5, p50, p95 of the small sets and of the base set (annotations.csv, all splits)
SIDES = {'small p5': 15, 'small p50': 28, 'small p95': 42, 'base p5': 57, 'base p50': 77, 'base p95': 103}
LETTERS = ['F', 'A', 'O', 'W']
MARGINS = np.linspace(0, 6, 61)
IMG = paths.PROJECT / 'docs' / 'exp_resolucao' / 'img'
BIG = Physics().replace(window=(2048, 2048), margin=1024, dust_density=0, sensor_dust_density=0)
SOURCES = {'bench': BIG, 'point': BIG.replace(bandwidth=0, pinhole=0, pixel_mtf=False)}


def mask_of_side(letter, side, font=FONTS[0]):
    """The letter at the font size whose box side (max of width and height) is closest to `side`."""
    best = None
    for fs in range(8, 200):
        m = np.asarray(letter_mask(letter, font, fs, 0), np.float32) / 255
        d = abs(max(m.shape) - side)
        if best is None or d < best[0]:
            best = (d, fs, m)
        if max(m.shape) > side + 2:
            break
    return best[1], best[2]


def single(mask, phys, z, dev):
    h, w = phys.window
    o = dict(mask=mask, absorption=0.6, phase=0.0, x=phys.margin + (w - mask.shape[1]) // 2,
             y=phys.margin + (h - mask.shape[0]) // 2, depth=0.0, kind='letter')
    return sensor_intensity(dict(objects=[o], dust=[], sensor_dust=[]), dict(z=z), phys, dev).cpu().numpy()


def shares(img, side):
    e = (img - 1) ** 2
    c = 1024
    out = []
    for m in MARGINS:
        a, b = int(c - side * (1 + m) / 2), int(c + side * (1 + m) / 2)
        out.append(e[a:b, a:b].sum() / e.sum())
    return np.array(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--device', default='cpu')
    a = ap.parse_args()
    torch.set_num_threads(4)
    dev = pick_device(a.device)
    rows, keep = [], {}
    t0 = time.time()
    for label, side in SIDES.items():
        for letter in LETTERS:
            fs, mask = mask_of_side(letter, side)
            s = max(mask.shape)
            for src, phys in SOURCES.items():
                for zmm in ZS_MM:
                    img = single(mask, phys, zmm * 1e-3, dev)
                    f = shares(img, s)
                    k25 = int(np.argmin(np.abs(MARGINS - 0.25)))
                    reach = {q: (float(MARGINS[np.argmax(f >= q)]) if (f >= q).any() else np.nan) for q in (0.5, 0.9)}
                    rows.append(dict(size=label, target_side_px=side, letter=letter, font_size=fs, side_px=s,
                                     side_um=s * PIXEL * 1e6, source=src, z_mm=zmm,
                                     fresnel_number=(s * PIXEL / 2) ** 2 / (WAVELENGTH * zmm * 1e-3),
                                     share_in_crop_25=float(f[k25]), share_in_box=float(f[0]),
                                     margin_for_50=reach[0.5], margin_for_90=reach[0.9]))
                    if letter == 'F' and label == 'base p50' and src == 'bench' and zmm in (19.25, 2.0, 1.0):
                        keep[zmm] = (img, s)
        print(label, f'{time.time() - t0:.0f}s', flush=True)
    t = pd.DataFrame(rows)
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    t.to_csv(paths.RESULTS / 'pattern_in_crop_z.csv', index=False, float_format='%.5g')
    g = t.groupby(['source', 'size', 'z_mm'], sort=False).agg(
        side_px=('side_px', 'mean'), fresnel=('fresnel_number', 'mean'), share_F=('share_in_crop_25', 'first'),
        share_mean=('share_in_crop_25', 'mean'), share_min=('share_in_crop_25', 'min'),
        share_max=('share_in_crop_25', 'max'), margin_90=('margin_for_90', 'mean')).reset_index()
    g.to_csv(paths.RESULTS / 'pattern_in_crop_z_summary.csv', index=False, float_format='%.4g')
    pd.set_option('display.width', 250)
    print(g.round(3).to_string(index=False))
    figure(g)
    examples(keep)


def figure(g):
    setup()
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.2), constrained_layout=True, sharey=True)
    colors = ['#9ecae1', '#4292c6', '#08519c', '#fdae6b', '#e6550d', '#a63603']
    for ax, src in zip(axes, ['bench', 'point']):
        for (label, side), c in zip(SIDES.items(), colors):
            d = g[(g.source == src) & (g['size'] == label)]
            ax.plot(d.z_mm, d.share_mean, 'o-', color=c, ms=4, label=f'{label} ({side} px)')
            ax.fill_between(d.z_mm, d.share_min, d.share_max, color=c, alpha=0.15, lw=0)
        ax.axhline(0.5, color=MUTED, lw=0.6, ls=':')
        ax.axhline(0.9, color=MUTED, lw=0.6, ls='--')
        ax.set_xscale('log')
        ax.set_xticks(ZS_MM)
        ax.set_xticklabels([f'{z:g}' for z in ZS_MM])
        ax.set_xlabel('sample-to-sensor distance z (mm)')
        ax.set_ylim(0, 1)
        ax.set_title(f'({"ab"[src == "point"]}) ' + ('source of the bench (10 nm, 100 µm pinhole, pixel)'
                                                     if src == 'bench' else 'point monochromatic source, no pixel'))
    axes[0].set_ylabel('share of the pattern inside the crop\n(box + 25 % margin)')
    axes[1].legend(loc='lower left', fontsize=6)
    fig.savefig(IMG / 'pattern_in_crop_z.png', dpi=200, bbox_inches='tight')
    plt.close(fig)


def examples(keep):
    setup()
    fig, axes = plt.subplots(1, 3, figsize=(9, 3.2), constrained_layout=True)
    for ax, zmm in zip(axes, [19.25, 2.0, 1.0]):
        img, s = keep[zmm]
        c, r = 1024, 200
        v = img[c - r:c + r, c - r:c + r]
        ax.imshow(v, cmap='gray', vmin=np.percentile(v, 0.5), vmax=np.percentile(v, 99.5))
        for k, ls in ((1.0, '-'), (1.25, '--')):
            h = s * k / 2
            ax.add_patch(plt.Rectangle((r - h, r - h), 2 * h, 2 * h, fill=False, ec=COLORS['complex'], lw=0.8, ls=ls))
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        ax.set_title(f'z = {zmm:g} mm', color=INK)
    fig.savefig(IMG / 'pattern_examples.png', dpi=200, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    main()
