"""The figure of the density curve for the paper (CADERNO_CURVA.md, Q0 b and the axis of Q1), from
results_exp_resolucao/density_curve.csv (density_curve_table.py) only: (a) open-set F1 and (b) rejection of never-seen
patterns against the share of overlapping holograms (x: pi D^2 sigma on a log scale, ticks labelled with the share;
top axis: objects per mm^2), for the hologram crops, the propagation layer and the reconstruction at z0; r1 at every
level (open), the mean of five with min and max where five repetitions exist (filled). Without the csv it writes
nothing and says so.

    python scripts/exp_resolucao/fig_density_curve.py --out <paper>/figures/paper
    -> <out>/fig_density_curve.pdf, .png
The sets that existed before (the geometry of CBMS 2024, r1 with the recipe of the curve; the small letters at 2 mm,
mean of five) are drawn at their own pi D^2 sigma (hologram_diameter_<set>_summary.json).
"""
import argparse
from pathlib import Path

from matplotlib.lines import Line2D

import fig_simulation as fs
import paper_resolucao as pr
from holo_openset import paths
from holo_openset.paper.style import COLORS, MUTED, panel, plt, setup


def main(out):
    t = pr.csv('density_curve')
    if not len(t):
        print('WARNING: density_curve.csv missing: fig_density_curve not written')
        return
    setup()
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), constrained_layout=True)
    for ax, (metric, label), letter in zip(axes, [('f1', 'open-set F1'), ('rejection', 'rejection of never-seen '
                                                                                         'patterns')], 'ab'):
        fs.curve_axes(ax, t, metric, label)
        fs.draw_old(ax, fs.old_sets(metric))
        panel(ax, letter)
    h = [Line2D([], [], color=COLORS[f], lw=1.0, label=fs.NAME[f]) for f in pr.FLOWS]
    h += [Line2D([], [], color=MUTED, marker='o', mfc='white', lw=0, ms=4, label='one repetition (r1)'),
          Line2D([], [], color=MUTED, marker='o', lw=0, ms=4, label='mean of five (min--max)'),
          Line2D([], [], color=MUTED, marker='D', mfc='white', lw=0, ms=4.5, label='CBMS 2024 geometry, r1'),
          Line2D([], [], color=MUTED, marker='s', lw=0, ms=4.5, label='small letters at 2 mm (off the curve)')]
    axes[0].legend(handles=h, loc='lower left', fontsize=5.8)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / 'fig_density_curve.pdf', bbox_inches='tight', pad_inches=0.02)
    fig.savefig(out / 'fig_density_curve.png', bbox_inches='tight', pad_inches=0.02, dpi=200)
    print('wrote', out / 'fig_density_curve.pdf')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', default=str(paths.PAPER))
    main(ap.parse_args().out)
