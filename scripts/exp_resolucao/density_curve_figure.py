"""The figure of the density curve (CADERNO_CURVA.md, Q1), from the csv files only:
$HOLO_RESULTS/density_curve.csv (one row per level and flow) and density_curve_reps.csv (one row per repetition).

x: the mean number of overlapping neighbours pi D^2 sigma (the exponent of the overlap ratio of Seo et al. 2009,
1 - exp(-pi D^2 sigma); a log scale of the complementary log-log of the ratio), D = the effective hologram diameter
of the axis measure, sigma the obtained density; ticks at the levels, labelled with their overlap ratio; top axis:
the density in objects per mm^2. Panels: F1 (open set) and rejection of the unseen, on the test split; crops (raw),
layer (prop), reconstruction (rec_z0); open markers r1, filled markers and bars the mean, min and max where the
level has five repetitions.
-> docs/exp_resolucao/img/density_curve.png and .pdf
    python scripts/exp_resolucao/density_curve_figure.py
"""
import argparse

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt   # noqa: E402
import pandas as pd   # noqa: E402

from holo_openset import paths   # noqa: E402

STYLE = {'raw': ('crops (raw)', '#d95f02', 'o'), 'prop': ('layer (prop)', '#1b9e77', 's'),
         'rec_z0': ('reconstruction (rec_z0)', '#7570b3', '^')}
IMG = paths.PROJECT / 'docs' / 'exp_resolucao' / 'img'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--prefix', default='density_curve')
    a = ap.parse_args()
    s = pd.read_csv(paths.RESULTS / f'{a.prefix}.csv')
    s = s[s.flow.isin(STYLE)]
    lv = s.drop_duplicates('level').sort_values('level')
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), constrained_layout=True)
    for ax, (m, name) in zip(axes, [('f1', 'open-set F1 (test)'), ('rejection', 'rejection of the unseen (test)')]):
        for k, (f, (label, col, mk)) in enumerate(STYLE.items()):
            g = s[s.flow == f].sort_values('level')
            x = g.pi_D2_sigma * (1 + 0.025 * (k - 1))   # a small horizontal offset per flow
            ax.plot(x, g[f'{m}_r1'], ls=':', color=col, lw=0.8)
            ax.scatter(x, g[f'{m}_r1'], marker=mk, facecolors='none', edgecolors=col, s=36,
                       label=f'{label}, r1')
            five = g[g.n_reps == 5]
            if len(five):
                xf = five.pi_D2_sigma * (1 + 0.025 * (k - 1))
                ax.errorbar(xf, five[f'{m}_mean'], yerr=[five[f'{m}_mean'] - five[f'{m}_min'],
                                                         five[f'{m}_max'] - five[f'{m}_mean']],
                            fmt=mk, color=col, ms=5, capsize=2, lw=1, label=f'{label}, mean of 5 (min-max)')
        ax.set_xscale('log')
        ax.set_xticks(lv.pi_D2_sigma)
        ax.set_xticklabels([f'{o:.3f}' if o < 0.9995 else f'{o:.4f}' for o in lv.overlap], fontsize=7)
        ax.minorticks_off()
        ax.set_xlabel('overlap ratio 1 - exp(-pi D^2 sigma) (axis: pi D^2 sigma, log)', fontsize=8)
        ax.set_ylabel(name, fontsize=9)
        ax.set_ylim(0, 1.02)
        ax.grid(alpha=0.3)
        top = ax.secondary_xaxis('top')
        top.set_xticks(lv.pi_D2_sigma)
        top.set_xticklabels([f'{d:.0f}' for d in lv.per_mm2], fontsize=7)
        top.minorticks_off()
        top.set_xlabel('objects per mm^2 (obtained)', fontsize=8)
    axes[1].legend(fontsize=6.5, loc='lower left')
    D = None
    try:
        import json
        D = json.load(open(paths.RESULTS / 'hologram_diameter_summary.json'))['D_ef_um']['D_rms_192']
    except (OSError, KeyError):
        pass
    fig.suptitle('Density curve at 1.0 mm (letters with the Fresnel numbers of the base set, depth uniform in the '
                 f'50 um channel){"; D = %.1f um" % D if D else ""}', fontsize=9)
    IMG.mkdir(parents=True, exist_ok=True)
    for ext in ('png', 'pdf'):
        fig.savefig(IMG / f'density_curve.{ext}', dpi=150)
    print('wrote', IMG / 'density_curve.png', IMG / 'density_curve.pdf')


if __name__ == '__main__':
    main()
