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
                              (pr.PILOT, 'letters of the\n1.0 mm sets', ZC[1.0], (1.6, 72))]:
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


def diameter_mm(set_name=None):
    """D of the axis of Q1 (hologram_diameter*_summary.json): the 1.0 mm sets by default, or the summary whose laws come
    from set_name (the sets of the paper, measured by the same script), None if not measured."""
    import json
    for f in sorted(pr.RES.glob('hologram_diameter*summary.json')):
        j = json.loads(f.read_text())
        if (set_name is None and f.name == 'hologram_diameter_summary.json') or \
                (set_name is not None and j.get('laws_from') == set_name):
            d = j.get('D_ef_um', {}).get(j.get('axis'))
            return d * 1e-3 if d else None
    return None


def curve_axes(ax, t, metric, ylabel, top=True, top_label='objects per mm$^2$'):
    """One panel of the density curve on the axis of Q1: x = pi D^2 sigma on a log scale (the mean number of
    overlapping neighbours), ticks labelled with the share of overlapping holograms, the density on the top axis;
    r1 at every level (open), the mean of five with its min-max where five exist (filled)."""
    d_mm = diameter_mm()
    for f in pr.FLOWS:
        g = t[t.flow == f].sort_values('pi_D2_sigma')
        if not len(g):
            continue
        five = g.n_reps == 5
        y = np.where(five, g[f'{metric}_mean'], g[f'{metric}_r1'])
        ax.plot(g.pi_D2_sigma, y, '-', color=COLORS[f], lw=1.0, zorder=2)
        ax.plot(g.pi_D2_sigma, g[f'{metric}_r1'], 'o', mfc='white', mec=COLORS[f], ms=3.5, zorder=3)
        if five.any():
            h = g[five]
            ax.errorbar(h.pi_D2_sigma, h[f'{metric}_mean'],
                        yerr=[h[f'{metric}_mean'] - h[f'{metric}_min'], h[f'{metric}_max'] - h[f'{metric}_mean']],
                        fmt='o', color=COLORS[f], ms=4, lw=0.8, capsize=1.5, zorder=4)
    lv = t.drop_duplicates('level').sort_values('pi_D2_sigma')
    ax.set_xscale('log')
    ax.set_xticks(lv.pi_D2_sigma, [f'{100 * o:.0f}' if o < 0.995 else '>99' for o in lv.overlap])
    ax.minorticks_off()
    ax.set_xlabel('overlapping holograms (%)')
    ax.set_ylabel(ylabel)
    if top and d_mm:
        k = np.pi * d_mm ** 2
        sec = ax.secondary_xaxis('top', functions=(lambda x: x / k, lambda s_: s_ * k))
        sec.set_xticks(lv.per_mm2, [f'{v:.0f}' for v in lv.per_mm2])
        sec.minorticks_off()
        sec.tick_params(labelsize=6)
        sec.set_xlabel(top_label, fontsize=6.5)


def old_sets(metric):
    """The sets that existed before the curve, on its axis with their own diameter: the geometry of CBMS 2024 (same
    recipe as the curve, r1) and the small letters at 2 mm (mean of five, sets_by_fresnel.csv).
    -> [(label, x, {flow: y}, marker, filled)]"""
    out = []
    cb, d_c, dens = pr.evals(pr.CBMS), diameter_mm(pr.CBMS), pr.density(pr.CBMS)[0]
    if d_c and dens:
        col = pr.F1 if metric == 'f1' else pr.REJ
        out.append(('CBMS 2024 geometry (19.25 mm), r1', np.pi * d_c ** 2 * dens,
                    {f: pr.value(cb, f, col, pr.reps_mode(cb)) for f in pr.FLOWS}, 'D', False))
    d_s, sb = diameter_mm('small_near'), pr.csv('sets_by_fresnel')
    r = sb[(sb.set == 'small_near') & (sb.repetitions == 'mean5')]
    dens_s = pr.density('small_near')[0]
    if d_s and len(r) and dens_s:
        r = r.iloc[0]
        k = 'f1' if metric == 'f1' else 'rejection'
        out.append(('small letters at 2 mm, mean of five', np.pi * d_s ** 2 * dens_s,
                    {f: r[f'{k}_{f}'] for f in pr.FLOWS}, 's', True))
    return out


def draw_old(ax, items):
    for label, x, ys, mk, filled in items:
        for f, y in ys.items():
            if y is not None and np.isfinite(y):
                ax.plot(x, y, mk, color=COLORS[f], mfc=COLORS[f] if filled else 'white', ms=4.5, zorder=5)


def panel_d(ax):
    t = pr.csv('density_curve')
    if len(t):                                   # the axis of Q1, from the table of the curve
        curve_axes(ax, t, 'rejection', 'rejection of never-seen patterns',
                   top_label='the density: objects per mm$^2$')
        draw_old(ax, [o for o in old_sets('rejection') if o[3] == 'D'])
        ax.set_ylim(-0.03, 1.05)
        return
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
            lab = (f'depth uniform $\\pm${g[1]:g} $\\mu$m' if g[0] == 'uniform' else
                   'nearly flat sample' if g[1] < 10 else f'depth sd {g[1]:g} $\\mu$m')
            ax.annotate(lab, xy=(pts[0]['density'] * 1.6, 0.42), fontsize=5.5, color=MUTED, rotation=-28)
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
    """Open-set F1 against the depth law of the test, for the models trained on a nearly flat sample (open) and on the
    standard law (filled), five repetitions each (depth_tests.csv)."""
    dt = pr.csv('depth_tests')
    dt = dt[dt.kind != 'diff']
    tests = [('flat', 'nearly\nflat'), ('u50', 'standard\n(channel)'), ('wide', 'stress\ntest')]
    off = {'raw': -0.2, 'prop': 0.0, 'rec_z0': 0.2}
    for tr, mfc_filled, ls in [('flat', False, ':'), ('u50', True, '-')]:
        for f in pr.FLOWS:
            ys = []
            for te, _ in tests:
                r = dt[(dt.trained == tr) & (dt.tested == te) & (dt.flow == f)]
                ys.append(float(r.f1_mean.iloc[0]) if len(r) else np.nan)
            xs = np.arange(len(tests)) + off[f]
            ax.plot(xs, ys, ls, color=COLORS[f], lw=0.8)
            ax.plot(xs, ys, 'o', color=COLORS[f], mfc=COLORS[f] if mfc_filled else 'white', ms=4)
    ax.axvspan(1.5, 2.5, color=GRID, lw=0, zorder=0)
    ax.set_xticks(range(len(tests)), [t[1] for t in tests])
    ax.tick_params(axis='x', labelsize=6)
    ax.set_xlabel('depth law of the test sample')
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
          Line2D([], [], color=MUTED, marker='o', mfc='white', ls=':', lw=0.8, ms=4,
                 label='(e) trained on a nearly flat sample'),
          Line2D([], [], color=MUTED, marker='o', ls='-', lw=0.8, ms=4, label='(e) trained on the standard law'),
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
