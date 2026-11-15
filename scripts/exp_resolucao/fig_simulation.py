"""The summary figure of the section "The simulation changes the answer" (PROTOCOLO_CURVA.md, "ESCRITA"): one panel per
piece of evidence, every number read from the stored results (CPU only; no hologram is simulated here).

  (a) the idealised model against the bench: open-set F1 of six flows trained and tested on each, and trained on the
      idealised holograms and tested on the bench (results/eval/{ideal,realistic}, as Table tab:ideal)
  (b) the distance: the contrast the source keeps at 19.25 mm and at 1.0 mm (envelope of eq. envelope, with the rows of
      envelope_z.csv), the Nyquist frequency, what a 4x reduction keeps, and the cut-off measured blind on the spectrum
      of the holograms of the CBMS geometry (spectrum_cutoff.csv)
  (c) the relative size: share of a letter's own pattern outside its crop against the Fresnel number, for six letter
      sizes at six distances (pattern_in_crop_z_summary.csv), with the sets of the paper (sets_by_fresnel.csv)
  (d) the density: rejection of never-seen patterns against the density of objects, for every set of the 1.0 mm family
      found in results_exp_resolucao/eval (r1, or the mean of five when r1-r5 exist), and the CBMS geometry at its
      density scaled to the size of those letters
  (e) the depth: open-set F1 when training and test differ in the depth spread of the sample (depth_training.csv, r1)

    python scripts/exp_resolucao/fig_simulation.py --out <paper>/figures/paper
    -> <out>/fig_simulation.pdf, .png
"""
import argparse
from pathlib import Path

import numpy as np
from matplotlib.lines import Line2D

import paper_resolucao as pr
from holo_openset import paths
from holo_openset.paper.style import COLORS, GRID, INK, MUTED, panel, plt, setup
from holo_openset.sim.envelope import Setup, envelope

NAME = {'raw': 'hologram crops', 'learned': 'learned layer (real)', 'complex': 'learned layer (complex)',
        'wiener': 'Wiener filter', 'prop': 'propagation layer', 'rec_z0': 'reconstruction at $z_0$'}
ZC = {19.25: '#6250d6', 1.0: '#e87ba4'}


def panel_a(ax):
    ib = pr.ideal_vs_bench()
    xs = [0, 1, 2]
    for f in pr.IDEAL_FLOWS:
        v = [ib['ideal'][f], ib['bench'][f], ib['cross'][f]]
        if None in v:
            continue
        lw = 2.2 if f == 'wiener' else 1.0
        ax.plot(xs[:2], v[:2], '-o', color=COLORS[f], lw=lw, ms=3.5, zorder=3 if f == 'wiener' else 2)
        ax.plot([1, 2], v[1:], ':', color=COLORS[f], lw=0.8)
        ax.plot(2, v[2], 'o', mfc='white', mec=COLORS[f], ms=4)
    ax.set_xticks(xs, ['idealised', 'bench', 'idealised\n$\\to$ bench'])
    ax.tick_params(axis='x', labelsize=6.5)
    ax.set_xlim(-0.3, 2.3)
    ax.set_ylabel('open-set F1')
    ax.set_title('idealised model against the bench', fontsize=7.5)


def panel_b(ax):
    ez = pr.csv('envelope_z')
    f = np.linspace(0, 420, 2101)
    nyq = float(ez.nyquist_cyc_per_mm.iloc[0])
    for z in (19.25, 1.0):
        r = ez[np.isclose(ez.z_mm, z)].iloc[0]
        s = Setup(wavelength=r.wavelength_nm * 1e-9, bandwidth=r.bandwidth_nm * 1e-9, pinhole=r.pinhole_um * 1e-6,
                  source_distance=r.source_distance_mm * 1e-3, z=z * 1e-3, pixel=r.pixel_um * 1e-6)
        e = np.abs(envelope(s, f * 1e3))
        ax.plot(f, e, color=ZC[z], lw=1.3)
        b = int(r['b_max_0.1'])
        ax.annotate(f'{z:g} mm: largest\nreduction {b}$\\times$' if b > 1 else f'{z:.1f} mm:\nno reduction',
                    xy=(r['f_c_0.1'], 0.1), xytext=(95, 0.55) if z > 10 else (150, 0.88), fontsize=6,
                    color=ZC[z], arrowprops=dict(arrowstyle='-', color=ZC[z], lw=0.6) if b > 1 else None)
    ax.axvspan(nyq, 420, color=GRID, lw=0)
    ax.text(nyq + 4, 0.30, 'beyond\nthe pixel', fontsize=6, color=MUTED, va='top')
    ax.axvline(nyq / 4, color=INK, lw=0.8, ls='--')
    ax.text(nyq / 4 + 4, 0.22, 'kept by a 4$\\times$\nreduction', fontsize=6, color=INK)
    ax.axhline(0.1, color=MUTED, lw=0.6, ls=':')
    sc = pr.csv('spectrum_cutoff')
    r = sc[(sc.set == 'realistic') & (sc.signal == 'I/B') & (sc.preregistered.astype(str) == 'True')]
    if len(r):
        ax.plot(r.f_c_cyc_per_mm.iloc[0], 0.1, 'v', color=ZC[19.25], ms=5, mfc='white', zorder=4)
    ax.set_xlim(0, 420)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel('fineness of the fringes (cycles/mm)')
    ax.set_ylabel('contrast kept by the source')
    ax.set_title('the distance', fontsize=7.5)


def panel_c(ax):
    pz = pr.csv('pattern_in_crop_z_summary')
    pz = pz[pz.source == 'bench']
    for size, d in pz.groupby('size'):
        d = d.sort_values('fresnel')
        big = size.startswith('base')
        ax.plot(d.fresnel, 100 * (1 - d.share_mean), '-', color=MUTED if big else '#b9b7b0', lw=0.8, zorder=1)
        ax.scatter(d.fresnel, 100 * (1 - d.share_mean), s=6, c=[MUTED if big else '#b9b7b0'], zorder=2, lw=0)
    sb = pr.csv('sets_by_fresnel')
    for s, label, col, xy in [(pr.CBMS, 'letters of the\nCBMS geometry\n(19.25 mm)', ZC[19.25], (0.025, 22)),
                              (pr.SPARSE, 'letters of the\n1.0 mm sets', ZC[1.0], (1.6, 72))]:
        r = sb[sb.set == s].iloc[0]
        ax.errorbar(r.fresnel_p50, 100 * r.outside_crop_p50,
                    xerr=[[r.fresnel_p50 - r.fresnel_p5], [r.fresnel_p95 - r.fresnel_p50]],
                    fmt='o', color=col, ms=4, lw=0.8, capsize=0, zorder=4)
        ax.annotate(label, xy=(r.fresnel_p50, 100 * r.outside_crop_p50),
                    xytext=xy,
                    fontsize=5.8, color=col, arrowprops=dict(arrowstyle='-', color=col, lw=0.5))
    big = pz[(pz['size'] == 'base p50') & np.isclose(pz.z_mm, 1.0)]
    if len(big):
        x, y = big.fresnel.iloc[0], 100 * (1 - big.share_mean.iloc[0])
        ax.plot(x, y, 's', color=INK, ms=4, zorder=4)
        ax.annotate('a letter of the\nCBMS geometry\nat 1.0 mm', xy=(x, y), xytext=(x * 0.25, y + 30), fontsize=5.8,
                    color=INK, arrowprops=dict(arrowstyle='-', color=INK, lw=0.5))
    ax.set_xscale('log')
    ax.set_ylim(-3, 103)
    ax.set_xlabel('Fresnel number (size$^2$ / ($\\lambda z$))')
    ax.set_ylabel('own pattern outside the crop (%)')
    ax.set_title('the relative size', fontsize=7.5)


def panel_d(ax):
    fam = pr.family()
    groups = sorted({x['law'] for x in fam})
    uni = [g for g in groups if g[0] == 'uniform']            # the standard family of Q1, when it exists
    main = uni[0] if uni else max(groups, key=lambda g: sum(x['law'] == g for x in fam)) if groups else None
    for g in groups:
        if g != main and sum(x['law'] == g for x in fam) < 2:
            continue                     # a depth law with one level only is not a curve (panel e shows it)
        pts = sorted((x for x in fam if x['law'] == g), key=lambda x: x['density'])
        ls = '-' if g == main else '--'
        for f in pr.FLOWS:
            xs = [x['density'] for x in pts]
            ys = [pr.value(x['df'], f, pr.REJ, x['mode']) for x in pts]
            ax.plot(xs, ys, ls, color=COLORS[f], lw=1.0, zorder=2)
            for x, y, p in zip(xs, ys, pts):
                ax.plot(x, y, 'o', color=COLORS[f], mfc=COLORS[f] if p['mode'] == 5 else 'white', ms=4, zorder=3)
        if g != main and pts:
            lab = f'depth uniform $\\pm${g[1]:g} $\\mu$m' if g[0] == 'uniform' else f'depth sd {g[1]:g} $\\mu$m'
            ax.annotate(lab, xy=(pts[-1]['density'], 0.5), fontsize=5.5, color=MUTED)
    cb = pr.evals(pr.CBMS)
    m = pr.reps_mode(cb)
    x = pr.cbms_equivalent_density()
    for f in pr.FLOWS:
        y = pr.value(cb, f, pr.REJ, m)
        if x is not None and y is not None:
            ax.plot(x * 1.18, y, 'D', color=COLORS[f], mfc='white' if m != 5 else COLORS[f], ms=4, zorder=3)
    if x is not None:
        y0 = pr.value(cb, 'raw', pr.REJ, m)
        ax.annotate('CBMS geometry (19.25 mm),\ndensity scaled to\nthese letters', xy=(x * 1.18, y0),
                    xytext=(6.5, 0.18), fontsize=5.8, color=ZC[19.25],
                    arrowprops=dict(arrowstyle='-', color=ZC[19.25], lw=0.5))
    ax.set_xscale('log')
    ax.set_ylim(-0.03, 1.05)
    ax.set_xlabel('objects per mm$^2$ (1.0 mm sets)')
    ax.set_ylabel('rejection of never-seen patterns')
    ax.set_title('the density', fontsize=7.5)


def panel_e(ax):
    dt = pr.csv('depth_training')
    lo, hi = dt.trained_um.min(), dt.trained_um.max()
    conds = [(lo, lo), (lo, hi), (hi, hi), (hi, lo)]
    labels = [f'{a:g}\n$\\to${b:g}' for a, b in conds]
    off = {'raw': -0.15, 'prop': 0.0, 'rec_z0': 0.15}
    for f in pr.FLOWS:
        ys = []
        for a, b in conds:
            r = dt[(dt.flow == f) & np.isclose(dt.trained_um, a) & np.isclose(dt.tested_um, b)]
            ys.append(float(r.f1.iloc[0]) if len(r) else np.nan)
        ax.plot(np.arange(4) + off[f], ys, 'o', color=COLORS[f], ms=4)
    ax.axvspan(0.5, 1.5, color=GRID, lw=0, zorder=0)
    ax.set_xticks(range(4), labels)
    ax.tick_params(axis='x', labelsize=6)
    ax.set_xlabel('depth spread (sd, $\\mu$m): training $\\to$ test')
    ax.set_ylabel('open-set F1')
    ax.set_title('the depth', fontsize=7.5)


def legend(ax):
    ax.axis('off')
    h = [Line2D([], [], color=COLORS[f], marker='o', lw=1.0, ms=4, label=NAME[f])
         for f in ['raw', 'learned', 'complex', 'wiener', 'prop', 'rec_z0']]
    h += [Line2D([], [], color=MUTED, marker='o', mfc='white', lw=0, ms=4, label='(a) trained on the idealised model'),
          Line2D([], [], color=MUTED, marker='o', mfc='white', lw=0, ms=4, label='(d) one repetition (r1)'),
          Line2D([], [], color=MUTED, marker='o', lw=0, ms=4, label='(d) mean of five repetitions'),
          Line2D([], [], color=MUTED, marker='D', mfc='white', lw=0, ms=4, label='(d) CBMS geometry, r1'),
          Line2D([], [], color=ZC[19.25], lw=1.3, label='(b) 19.25 mm (CBMS 2024)'),
          Line2D([], [], color=ZC[1.0], lw=1.3, label='(b) 1.0 mm (bench)'),
          Line2D([], [], color=ZC[19.25], marker='v', mfc='white', lw=0, ms=5,
                 label='(b) cut-off measured on the\n     holograms (19.25 mm)')]
    ax.legend(handles=h, loc='center left', fontsize=6.3, frameon=False, borderaxespad=0)


def main(out):
    setup()
    fig = plt.figure(figsize=(7.4, 5.4))
    gs = fig.add_gridspec(2, 3, hspace=0.55, wspace=0.45)
    axes = [fig.add_subplot(gs[0, i]) for i in range(3)] + [fig.add_subplot(gs[1, i]) for i in range(3)]
    for ax, fn, letter in zip(axes, [panel_a, panel_b, panel_c, panel_d, panel_e], 'abcde'):
        fn(ax)
        panel(ax, letter)
    legend(axes[5])
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / 'fig_simulation.pdf', bbox_inches='tight', pad_inches=0.02)
    fig.savefig(out / 'fig_simulation.png', bbox_inches='tight', pad_inches=0.02, dpi=200)
    print('wrote', out / 'fig_simulation.pdf')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', default=str(paths.PAPER))
    main(ap.parse_args().out)
