"""Figure of T2: the ring spectra of the three sets against the noise floor, and the envelope of the model.
Reads $HOLO_RESULTS/{spectrum_rings,spectrum_cutoff,envelope_cutoff,envelope_curve}.csv;
writes docs/exp_resolucao/img/spectrum_cutoff.png.

    python scripts/exp_resolucao/fig_spectrum.py
"""
import matplotlib.pyplot as plt
import pandas as pd

from holo_openset import paths
from holo_openset.paper.style import COLORS, INK, MUTED, setup
from holo_openset.sim.physics import PIXEL

OUT = paths.PROJECT / 'docs' / 'exp_resolucao' / 'img' / 'spectrum_cutoff.png'
SETS = {'realistic': ('base set, z = 19.25 mm', 19.25), 'small_z0': ('small letters, z = 19.25 mm', 19.25),
        'small_near': ('small letters, z = 2 mm', 2.0)}
SIG = {'I/B': COLORS['learned'], 'I': COLORS['complex']}


def main():
    setup()
    R = paths.RESULTS
    rings, cut = pd.read_csv(R / 'spectrum_rings.csv'), pd.read_csv(R / 'spectrum_cutoff.csv')
    env, curve = pd.read_csv(R / 'envelope_cutoff.csv'), pd.read_csv(R / 'envelope_curve.csv')
    nyq = 1 / (2 * PIXEL) / 1e3
    fig, axes = plt.subplots(1, 4, figsize=(11, 2.8), constrained_layout=True)
    for ax, (s, (title, z)) in zip(axes, SETS.items()):
        for sig, color in SIG.items():
            d = rings[(rings.set == s) & (rings.signal == sig)]
            c = cut[(cut.set == s) & (cut.signal == sig) & cut.preregistered].iloc[0]
            ax.plot(d.f_cyc_per_mm, d.power / c.floor, color=color, lw=1.0,
                    label=f'{sig}: $f_c$ = {c.f_c_cyc_per_mm:.0f}, b = {c.b_blind}')
            ax.axvline(c.f_c_cyc_per_mm, color=color, lw=0.8, ls='--')
        m = env[(env.z_mm == z) & (env.threshold == 0.1)].iloc[0]
        ax.axvline(m.f_c_cyc_per_mm, color=INK, lw=0.8, ls=':', label=f'model, E < 0.1: {m.f_c_cyc_per_mm:.0f}')
        ax.axhline(2.0, color=MUTED, lw=0.8)
        ax.axhline(1.0, color=MUTED, lw=0.5, ls=':')
        ax.axvspan(nyq * 0.8, nyq, color=MUTED, alpha=0.08, lw=0)
        ax.set_yscale('log')
        ax.set_xlim(0, nyq)
        ax.set_xlabel('|f| (cycles/mm)')
        ax.set_title(f'({"abc"[list(SETS).index(s)]}) {title}')
        ax.legend(loc='upper right', fontsize=6)
    axes[0].set_ylabel('ring power / noise floor')
    ax = axes[3]
    for z, color in ((19.25, COLORS['rec_z0']), (2.0, COLORS['prop'])):
        ax.plot(curve.f_cyc_per_mm, curve[f'E_{z:g}mm'].abs(), color=color, lw=1.0, label=f'z = {z:g} mm')
        for thr, ls in ((0.1, '--'), (0.05, ':')):
            m = env[(env.z_mm == z) & (env.threshold == thr)].iloc[0]
            ax.axvline(m.f_c_cyc_per_mm, color=color, lw=0.8, ls=ls)
    ax.axhline(0.1, color=MUTED, lw=0.8, ls='--')
    ax.axhline(0.05, color=MUTED, lw=0.8, ls=':')
    ax.set_yscale('log')
    ax.set_ylim(1e-3, 1.2)
    ax.set_xlim(0, nyq)
    ax.set_xlabel('|f| (cycles/mm)')
    ax.set_ylabel('|E(f)| (model)')
    ax.set_title('(d) envelope of the source and the pixel')
    ax.legend(loc='lower left', fontsize=6)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches='tight')
    print('wrote', OUT)


if __name__ == '__main__':
    main()
