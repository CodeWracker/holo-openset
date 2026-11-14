"""Z8.2: "what changes with the set-up", one figure from the result files (no number typed by hand):
  (a) one letter recorded at 19.25, 2 and 1 mm with its crop (simulated here, sim.physics.sensor_intensity);
  (b) the contrast envelope E(f) of the source of the bench at those distances (sim.envelope), with the Nyquist
      frequency of the sensor and the largest reduction factor each distance allows;
  (c) the share of a pattern outside its crop against the distance ($HOLO_RESULTS/pattern_in_crop_z_summary.csv);
  (d) open-set F1 of three flows on the three existing sets ($HOLO_RESULTS/small_preview.csv, from results/eval);
  (e) the idealised model against the bench (results/eval/{ideal,realistic}, as tables.tab_ideal reads them).
Writes docs/exp_resolucao/img/fig_setup.{pdf,png}. Not wired into the generators of the paper.

    python scripts/exp_resolucao/fig_setup.py [--device cuda:N]
"""
import argparse
import glob
import json

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.model import pick_device
from holo_openset.paper.style import COLORS, GRID, INK, MUTED, panel, plt, setup
from holo_openset.sim.envelope import Setup, envelope, summary
from holo_openset.sim.letters import FONTS, letter_mask
from holo_openset.sim.physics import PIXEL, Physics, sensor_intensity

OUT = paths.PROJECT / 'docs' / 'exp_resolucao' / 'img' / 'fig_setup'
ZS = [19.25, 2.0, 1.0]                      # mm
ZCOL = {19.25: '#6250d6', 2.0: '#0097a7', 1.0: '#e87ba4'}
FLOW_NAME = {'raw': 'hologram crops', 'learned': 'learned filter', 'complex': 'learned complex filter',
             'wiener': 'Wiener filter', 'prop': 'propagation layer', 'rec_z0': 'reconstruction (calibrated)'}
SETS = [('realistic', 'large letters\n19.25 mm'), ('small_z0', 'small letters\n19.25 mm'),
        ('small_near', 'small letters\n2 mm')]


def letter_images(dev):
    phys = Physics().replace(window=(640, 640), dust_density=0, sensor_dust_density=0)
    t = pd.read_csv(paths.RESULTS / 'pattern_in_crop_z.csv')   # 'F' with the median box of the base set
    fs = int(t[(t.letter == 'F') & (t['size'] == 'base p50')].font_size.iloc[0])
    m = np.asarray(letter_mask('F', FONTS[0], fs, 0), np.float32) / 255
    o = dict(mask=m, absorption=0.6, phase=0.0, x=phys.margin + (640 - m.shape[1]) // 2,
             y=phys.margin + (640 - m.shape[0]) // 2, depth=0.0, kind='letter')
    return {z: sensor_intensity(dict(objects=[o], dust=[], sensor_dust=[]), dict(z=z * 1e-3), phys, dev).cpu().numpy()
            for z in ZS}, max(m.shape)


def evals(set_, train_set=None):
    out = {}
    for f in FLOW_NAME:
        name = f'{f}_from_{train_set}' if train_set else f
        v = [json.load(open(p))['novel_open_macro_f1'] for p in
             sorted(glob.glob(str(paths.PROJECT / 'results' / 'eval' / set_ / f'{name}_r[1-5].json')))]
        out[f] = (np.mean(v), np.std(v, ddof=1)) if len(v) == 5 else None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--device', default='cpu')
    a = ap.parse_args()
    torch.set_num_threads(4)
    dev = pick_device(a.device)
    setup()
    plt.rcParams.update({'font.size': 9, 'axes.titlesize': 9, 'axes.labelsize': 9, 'legend.fontsize': 8,
                         'xtick.labelsize': 8, 'ytick.labelsize': 8})
    imgs, side = letter_images(dev)
    fig = plt.figure(figsize=(10.5, 7.2))
    top = fig.add_gridspec(1, 3, left=0.02, right=0.99, top=0.95, bottom=0.57, width_ratios=[1.55, 1, 1], wspace=0.3)
    bot = fig.add_gridspec(1, 2, left=0.07, right=0.99, top=0.44, bottom=0.08, width_ratios=[1, 1.15], wspace=0.28)

    # (a) one letter at three distances
    sub = top[0, 0].subgridspec(1, 3, wspace=0.04)
    r = 150
    for k, z in enumerate(ZS):
        ax = fig.add_subplot(sub[0, k])
        v = imgs[z][320 - r:320 + r, 320 - r:320 + r]
        ax.imshow(v, cmap='gray', vmin=np.percentile(v, 0.5), vmax=np.percentile(v, 99.5), interpolation='nearest')
        h = side * 1.25 / 2
        ax.add_patch(plt.Rectangle((r - h, r - h), 2 * h, 2 * h, fill=False, ec='#eb6834', lw=1.2, ls='--'))
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title(f'{z:g} mm', fontsize=9, loc='center', color=ZCOL[z], fontweight='bold')
        if k == 0:
            panel(ax, 'a')
            ax.text(0.0, -0.05, f'the same letter ({side * PIXEL * 1e6:.0f} µm) at three sample-to-sensor distances;'
                    '\ndashed: the crop the classifier sees', transform=ax.transAxes, fontsize=8, va='top', color=INK)

    # (b) the envelope of the source
    ax = fig.add_subplot(top[0, 1])
    f = np.linspace(0, 600e3, 1201)
    for z in ZS:
        s = Setup(z=z * 1e-3)
        b = summary(s)['b_max_0.1']
        ax.plot(f / 1e3, np.abs(envelope(s, f)), color=ZCOL[z], lw=1.6,
                label=f'{z:g} mm: reduce up to {b}×' if b > 1 else f'{z:g} mm: no reduction')
    nyq = Setup().nyquist / 1e3
    ax.axvspan(nyq, 600, color=GRID, alpha=0.6, lw=0)
    ax.axvline(nyq, color=MUTED, lw=0.8)
    ax.text(nyq + 8, 0.66, 'beyond what\nthe pixels\ncan sample', fontsize=7.5, color=MUTED, va='top')
    ax.axhline(0.1, color=MUTED, lw=0.6, ls=':')
    ax.set_xlim(0, 600)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel('fineness of the fringes (cycles/mm)')
    ax.set_ylabel('contrast the source keeps')
    ax.legend(loc='upper right', fontsize=7.5, handlelength=1.2, framealpha=1, frameon=True, edgecolor=GRID)
    panel(ax, 'b')

    # (c) the share of a pattern outside its crop
    ax = fig.add_subplot(top[0, 2])
    pc = pd.read_csv(paths.RESULTS / 'pattern_in_crop_z_summary.csv')
    for size, color in [('base p50', '#e6550d'), ('small p50', '#4292c6')]:
        d = pc[(pc.source == 'bench') & (pc['size'] == size)].sort_values('z_mm')
        px = int(round(d.side_px.iloc[0]))
        ax.plot(d.z_mm, 1 - d.share_mean, 'o-', color=color, ms=4,
                label=f'{"large" if "base" in size else "small"} letter ({px * PIXEL * 1e6:.0f} µm)')
        ax.fill_between(d.z_mm, 1 - d.share_max, 1 - d.share_min, color=color, alpha=0.15, lw=0)
    ax.set_xscale('log')
    zt = sorted(pc.z_mm.unique())
    ax.set_xticks(zt)
    ax.set_xticklabels([f'{z:g}' for z in zt])
    ax.minorticks_off()
    ax.set_ylim(0, 1)
    ax.set_xlabel('sample-to-sensor distance (mm)')
    ax.set_ylabel('share of the pattern outside the crop')
    ax.legend(loc='upper left', fontsize=7.5)
    panel(ax, 'c')

    # (d) open-set F1 on the three existing sets
    ax = fig.add_subplot(bot[0, 0])
    t = pd.read_csv(paths.RESULTS / 'small_preview.csv')
    flows = ['raw', 'prop', 'rec_z0']
    w = 0.26
    for j, fl in enumerate(flows):
        m = [t[(t.set == s) & (t.flow == fl) & (t.metric == 'novel_open_macro_f1')].iloc[0] for s, _ in SETS]
        x = np.arange(len(SETS)) + (j - 1) * w
        ax.bar(x, [v['mean'] for v in m], w * 0.92, yerr=[v['std'] for v in m], color=COLORS[fl],
               error_kw=dict(lw=0.8, capsize=2, ecolor=INK), label=FLOW_NAME[fl])
        for xi, v in zip(x, m):
            ax.text(xi, v['mean'] + 0.02, f"{v['mean']:.2f}", ha='center', va='bottom', fontsize=7, color=INK)
    ax.set_xticks(range(len(SETS)))
    ax.set_xticklabels([n for _, n in SETS])
    ax.set_ylim(0, 1.12)
    ax.set_ylabel('open-set F1 (5 class splits)')
    ax.legend(loc='upper center', ncol=3, fontsize=7.5, bbox_to_anchor=(0.5, 1.13), handlelength=1.2,
              columnspacing=1.0)
    ax.grid(axis='x', visible=False)
    panel(ax, 'd')

    # (e) idealised model against the bench
    ax = fig.add_subplot(bot[0, 1])
    ideal, bench, cross = evals('ideal'), evals('realistic'), evals('realistic', 'ideal')
    xs = [0, 1, 2]
    for fl in FLOW_NAME:
        c = COLORS[fl]
        ax.plot(xs[:2], [ideal[fl][0], bench[fl][0]], '-o', color=c, lw=1.6, ms=5, label=FLOW_NAME[fl])
        if cross[fl]:
            ax.plot([xs[1], xs[2]], [bench[fl][0], cross[fl][0]], ':', color=c, lw=0.6, alpha=0.6)
            ax.plot(xs[2], cross[fl][0], 'o', mfc='white', mec=c, mew=1.4, ms=6)
    wi, wb = ideal['wiener'][0], bench['wiener'][0]
    others_i = [ideal[f][0] for f in FLOW_NAME if f != 'wiener']
    others_b = [bench[f][0] for f in FLOW_NAME if f not in ('wiener', 'raw')]
    ax.annotate(f'Wiener filter: best on the\nidealised model ({wi:.3f})', (0, wi), xytext=(0.12, 0.70),
                textcoords='data', fontsize=7.5, color=COLORS['wiener'],
                arrowprops=dict(arrowstyle='-', color=COLORS['wiener'], lw=0.6))
    if wi > max(others_i) and wb < min(others_b):
        ax.annotate(f'last but the crops\non the bench ({wb:.3f})', (1, wb), xytext=(0.62, 0.62),
                    textcoords='data', fontsize=7.5, color=COLORS['wiener'],
                    arrowprops=dict(arrowstyle='-', color=COLORS['wiener'], lw=0.6))
    ax.text(2, 0.985, 'open circles:\nno retraining', ha='center', va='top', fontsize=7.5, color=MUTED)
    ax.set_xticks(xs)
    ax.set_xticklabels(['trained and tested\non the idealised model', 'trained and tested\non the bench',
                        'trained on the idealised\nmodel, tested on the bench'])
    ax.set_xlim(-0.3, 2.3)
    ax.set_ylim(0.3, 1.02)
    ax.set_ylabel('open-set F1 (5 class splits)')
    ax.grid(axis='x', visible=False)
    ax.legend(loc='lower left', fontsize=7.5, ncol=2, handlelength=1.4, columnspacing=1.0)
    panel(ax, 'e')

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT.with_suffix('.pdf'), bbox_inches='tight', pad_inches=0.03)
    fig.savefig(OUT.with_suffix('.png'), bbox_inches='tight', pad_inches=0.03, dpi=200)
    print('wrote', OUT.with_suffix('.png'))


if __name__ == '__main__':
    main()
