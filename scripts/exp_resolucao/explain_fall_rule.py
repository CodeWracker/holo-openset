"""An explanatory figure (not for the paper; labels in Portuguese) of what the pre-registered rule "fell" of the density
curve measures, and of what the sample looks like at each level (CADERNO_CURVA.md, Q0 b).

Rows 1-3, one column per level of the u50 curve (data/curve_u50_L008 ... _L343), the same region of the same training
scene in the five sets (the annotated letters are the same in the five; only the un-annotated fillers change):
  1  the sample in the plane of the objects: the scene rebuilt from its seed (holo_openset.sim.scene.make_scene with
     the layout of each set's physics.json), annotated letters in colour, fillers in grey (dust not drawn);
  2  the recorded hologram (holograms.npy), with the boxes of the annotated letters;
  3  the modulus of the field back-propagated to the set's z0 (1.0 mm) by holo_openset.reconstruct, after the flat
     field of the session (the input of the rec_z0 flow; no model involved).
Row 4, from results_exp_resolucao/density_curve_reps.csv only: (a) rejection of the never-seen letters, mean of five
repetitions with min-max; (b) and (c) the change of rejection and of F1 against the sparse level, same flow, same
repetition, one point per repetition, with the line of the rule and the count of repetitions past it.

    python scripts/exp_resolucao/explain_fall_rule.py --out docs/exp_resolucao/img
    -> <out>/explica_regra_caiu.png, .pdf
Deterministic: no training, no evaluation, no test data read by a model.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from holo_openset.paper.style import COLORS  # noqa: E402
from holo_openset.reconstruct import Holograms, reconstruct  # noqa: E402
from holo_openset.sim.generate import layout_of  # noqa: E402
from holo_openset.sim.physics import PIXEL, physics_from_dict  # noqa: E402
from holo_openset.sim.scene import make_scene  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
LEVELS = [8, 15, 69, 154, 343]
FLOWS = ['raw', 'prop', 'rec_z0']
NAME = {'raw': 'crops', 'prop': 'camada de propagação', 'rec_z0': 'reconstrução'}
ANNOT = '#d9480f'   # the annotated letters
FILLER = '#9a9a9a'  # the fillers
# Training image 465 (session of the train split): the 320 x 320 region at (x0, y0) = (256, 160) of the 640 x 640
# window holds three annotated letters (S, V, K) well inside it and no other annotated letter (chosen by a scan of
# the first 600 training images for regions with 2-3 annotated letters, largest spacing).
IMAGE, X0, Y0, SIDE = 465, 256, 160, 320
RULE = {'rejection': -0.30, 'f1': -0.10}


def fmt(v, nd=2):
    return f'{v:.{nd}f}'.replace('.', ',')


def scene_of(i, cfg, phys, lay):
    seed = cfg['seed'] * 1_000_000 + int(i)
    while True:   # as holo_openset.sim.generate._scene
        sc = make_scene(seed, phys, lay=lay)
        if sc is not None:
            return sc
        seed += 7919 * 1000003


def object_plane(root, i, ann):
    """RGB of the window in the plane of the objects: white, letters by their area coverage of each pixel."""
    cfg = json.load(open(root / 'physics.json'))
    phys = physics_from_dict(cfg['physics'])
    sc = scene_of(i, cfg, phys, layout_of(cfg))
    rows = pd.DataFrame(sc['rows'])
    assert (rows[['classe', 'x0', 'y0', 'x1', 'y1']].to_numpy() == ann[['classe', 'x0', 'y0', 'x1', 'y1']].to_numpy()
            ).all(), f'{root.name}: the rebuilt scene is not the recorded one'
    h, w = phys.window
    m0 = sc['margin']
    cov = {k: np.zeros((h, w), np.float32) for k in ('letter', 'filler')}
    for o in sc['objects']:
        if o['kind'] not in cov:
            continue
        m = o['mask']
        mh, mw = m.shape
        y, x = o['y'] - m0, o['x'] - m0
        ys, xs = max(0, y), max(0, x)
        ye, xe = min(h, y + mh), min(w, x + mw)
        if ye <= ys or xe <= xs:
            continue
        sub = cov[o['kind']][ys:ye, xs:xe]
        np.maximum(sub, m[ys - y:ye - y, xs - x:xe - x], out=sub)
    rgb = np.ones((h, w, 3), np.float32)
    for k, col in (('filler', FILLER), ('letter', ANNOT)):
        c = np.array(matplotlib.colors.to_rgb(col), np.float32)
        a = cov[k][..., None]
        rgb = rgb * (1 - a) + c * a
    n_fill = sum(o['kind'] == 'filler' and o['x'] - m0 < X0 + SIDE and o['x'] - m0 + o['mask'].shape[1] > X0
                 and o['y'] - m0 < Y0 + SIDE and o['y'] - m0 + o['mask'].shape[0] > Y0 for o in sc['objects'])
    return rgb, n_fill


def images(level):
    root = ROOT / 'data' / f'curve_u50_L{level:03d}'
    src = Holograms(root)
    ann = pd.read_csv(root / 'annotations.csv')
    ann = ann[ann.image_id == IMAGE].reset_index(drop=True)
    assert (ann.split == 'train').all()
    obj, n_fill = object_plane(root, IMAGE, ann)
    holo = np.array(src.holo[src.row[IMAGE]], np.float32)
    a = src.amplitude(IMAGE, 'cpu')
    rec = reconstruct(a, 'z0', z0=src.z0, pixel=src.pixel).abs().numpy()
    sl = (slice(Y0, Y0 + SIDE), slice(X0, X0 + SIDE))
    return dict(obj=obj[sl], holo=holo[sl], rec=rec[sl], ann=ann, n_fill=n_fill, z0=src.z0)


def reps():
    d = pd.read_csv(ROOT / 'results_exp_resolucao' / 'density_curve_reps.csv')
    d = d[d.flow.isin(FLOWS)].copy()
    sp = d[d.level == LEVELS[0]].set_index(['flow', 'rep'])
    key = list(zip(d.flow, d.rep))
    d['dr'] = d.rejection.to_numpy() - sp.loc[key, 'rejection'].to_numpy()
    d['df'] = d.f1.to_numpy() - sp.loc[key, 'f1'].to_numpy()
    assert np.allclose(d.dr, d.d_rej, atol=1e-5) and np.allclose(d.df, d.d_f1, atol=1e-5)
    return d


def drop_panel(ax, d, col, rule, ylabel, title, ylim, h_in):
    off = {'raw': -0.27, 'prop': 0.0, 'rec_z0': 0.27}
    jit = np.array([-0.06, -0.03, 0.0, 0.03, 0.06])
    lv = LEVELS[1:]
    ax.axhspan(ylim[0], rule, color='#d62728', alpha=0.07, lw=0)
    ax.axhline(rule, color='#b22222', ls='--', lw=1.2)
    ax.axhline(0, color='#555555', lw=0.8)
    ax.text(-0.42, ylim[0] + 0.03 * (ylim[1] - ylim[0]), f'regra: caiu se ≥ {fmt(-rule)} abaixo em 4 de 5\n'
            '(linha tracejada; região sombreada = além da linha)', ha='left', va='bottom', fontsize=9,
            color='#b22222')
    score = {}
    for gx, L in enumerate(lv):
        for f in FLOWS:
            g = d[(d.level == L) & (d.flow == f)].sort_values('rep')
            v = g[col].to_numpy()
            x = gx + off[f]
            ax.scatter(x + jit[:len(v)], v, s=22, color=COLORS[f], edgecolor='white', lw=0.4, zorder=3)
            ax.plot([x - 0.11, x + 0.11], [v.mean()] * 2, color=COLORS[f], lw=2.2, zorder=4)
            score[L, f] = int((v <= rule + 1e-12).sum())
    ax.set_xlim(-0.5, len(lv) - 0.5)
    ax.set_ylim(*ylim)
    ax.set_xticks(range(len(lv)))
    ax.set_xticklabels([f'{lab} por mm²' for lab in ('13', '60', '135', '300')], fontsize=9)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=11, loc='left')
    ax.tick_params(labelsize=9)
    ax.grid(axis='y', color='#e4e3df', lw=0.6)
    tr = matplotlib.transforms.blended_transform_factory(ax.transData, ax.transAxes)
    dy = 1 / h_in   # one inch in axes units
    ax.text(-0.5, -0.33 * dy, 'repetições além\nda linha (negrito\n= caiu, ≥ 4 de 5):', transform=tr, ha='right', va='top', fontsize=9,
            color='#333333')
    for gx, L in enumerate(lv):
        for k, f in enumerate(FLOWS):
            s = score[L, f]
            ax.text(gx, -(0.33 + 0.19 * k) * dy, f'{s} de 5', transform=tr, ha='center',
                    va='top', fontsize=9, color=COLORS[f], fontweight='bold' if s >= 4 else 'normal')
    return score


def main(out):
    torch.set_num_threads(4)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    d = reps()
    lvl = d.groupby('level')[['per_mm2', 'overlap', 'covered']].mean()
    ims = {L: images(L) for L in LEVELS}

    W, H = 15, 13.0
    fig = plt.figure(figsize=(W, H), facecolor='white')

    def axes_in(x, y, w, h):   # inches from the bottom left
        return fig.add_axes([x / W, y / H, w / W, h / H])

    fig.text(0.5, 12.72 / H, "O que a regra 'caiu' mede, e como é a amostra em cada nível", ha='center', va='center',
             fontsize=15, fontweight='bold')
    side, gap = 2.2, 0.55
    left = (W - 5 * side - 4 * gap) / 2
    tops = [11.5, 9.0, 6.5]
    heads = ['1 · a amostra (plano dos objetos): letras anotadas em laranja, letras de enchimento (não anotadas) em '
             'cinza; poeira não desenhada',
             '2 · o holograma gravado (o que os crops recebem), com as caixas das letras anotadas',
             f'3 · depois de uma retropropagação a {fmt(ims[8]["z0"] * 1e3, 1)} mm (o que a reconstrução recebe): '
             'amplitude do campo, após o flat-field da sessão']
    # common grey scales across the five levels
    hl = np.percentile(np.stack([ims[L]['holo'] for L in LEVELS]), [0.5, 99.5])
    rl = np.percentile(np.stack([ims[L]['rec'] for L in LEVELS]), [0.5, 99.5])
    for c, L in enumerate(LEVELS):
        x = left + c * (side + gap)
        r = lvl.loc[L]
        fig.text((x + side / 2) / W, 12.36 / H, f'{fmt(r.per_mm2, 0)} por mm²', ha='center', va='center',
                 fontsize=12, fontweight='bold')
        fig.text((x + side / 2) / W, 12.1 / H, f'sobreposição {fmt(r.overlap)} ·\n{fmt(100 * r.covered, 1)} % da '
                 'área coberta', ha='center', va='center', fontsize=10, linespacing=1.3)
        im = ims[L]
        for k, (top, key) in enumerate(zip(tops, ['obj', 'holo', 'rec'])):
            ax = axes_in(x, top - side, side, side)
            if key == 'obj':
                ax.imshow(im['obj'], interpolation='antialiased')
            else:
                lim = hl if key == 'holo' else rl
                ax.imshow(im[key], cmap='gray', vmin=lim[0], vmax=lim[1], interpolation='antialiased')
            if key == 'holo':
                for _, a in im['ann'].iterrows():
                    if a.x1 > X0 and a.x0 < X0 + SIDE and a.y1 > Y0 and a.y0 < Y0 + SIDE:
                        ax.add_patch(Rectangle((a.x0 - X0 - 0.5, a.y0 - Y0 - 0.5), a.x1 - a.x0, a.y1 - a.y0,
                                               fill=False, ec=ANNOT, lw=0.9))
            if key == 'obj' and c == 0:   # scale bar: 100 um
                n = 100e-6 / PIXEL
                ax.plot([SIDE - 15 - n, SIDE - 15], [SIDE - 18] * 2, color='black', lw=2.5)
                ax.text(SIDE - 15 - n / 2, SIDE - 26, '100 µm', ha='center', va='bottom', fontsize=9)
            if key == 'obj' and L != LEVELS[0]:
                ax.text(6, 6, f'+{im["n_fill"]} letras de enchimento nesta região', ha='left', va='top', fontsize=8.5,
                        color='#444444', bbox=dict(fc='white', ec='none', alpha=0.9, pad=1.5))
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_color('#888888')
                s.set_linewidth(0.6)
    for top, txt in zip(tops, heads):
        fig.text(left / W, (top + 0.14) / H, txt, ha='left', va='center', fontsize=11)
    fig.text(left / W, (tops[2] - side - 0.18) / H,
             f'Mesma região (320 × 320 px = {fmt(SIDE * PIXEL * 1e3, 2)} mm de lado) da imagem de treino {IMAGE} nos '
             'cinco conjuntos: as letras anotadas (S, V, K) são as mesmas; só as de enchimento mudam. Escalas de cinza '
             'iguais nas cinco colunas.', ha='left', va='center', fontsize=9, color='#444444')

    # row 4
    y4, h4 = 1.3, 1.7
    fig.text(left / W, 3.88 / H,
             "4 · a regra pré-registrada: um fluxo 'caiu' num nível se, em pelo menos 4 das 5 repetições, o F1 ficou "
             "≥ 0,10 abaixo OU a rejeição ficou ≥ 0,30 abaixo",
             ha='left', va='center', fontsize=11)
    fig.text(left / W, 3.64 / H, '      do valor do MESMO fluxo no nível esparso (7 por mm²), na MESMA repetição.',
             ha='left', va='center', fontsize=11)
    pw, pg, x4 = 3.75, 1.1, 1.2
    xs = [x4, x4 + pw + pg, x4 + 2 * (pw + pg)]
    ax = axes_in(xs[0], y4, pw, h4)
    xi = np.arange(len(LEVELS))
    for f in FLOWS:
        g = d[d.flow == f].groupby('level').rejection
        m, lo, hi = g.mean().loc[LEVELS], g.min().loc[LEVELS], g.max().loc[LEVELS]
        ax.fill_between(xi, lo, hi, color=COLORS[f], alpha=0.18, lw=0)
        ax.plot(xi, m, color=COLORS[f], lw=1.6, marker='o', ms=4.5)
    ax.set_xticks(xi)
    ax.set_xticklabels(['7', '13', '60', '135', '300'], fontsize=9)
    ax.set_xlabel('objetos por mm²', fontsize=10)
    ax.set_ylim(-0.02, 1.05)
    ax.set_ylabel('rejeição', fontsize=10)
    ax.set_title('(a) Rejeição das não vistas (média; faixa mín.–máx.)', fontsize=11, loc='left')
    ax.tick_params(labelsize=9)
    ax.grid(color='#e4e3df', lw=0.6)
    sr = drop_panel(axes_in(xs[1], y4, pw, h4), d, 'dr', RULE['rejection'], 'Δ rejeição (nível − esparso)',
                    '(b) Queda da rejeição contra o esparso, mesma repetição', (-0.95, 0.12), h4)
    sf = drop_panel(axes_in(xs[2], y4, pw, h4), d, 'df', RULE['f1'], 'Δ F1 (nível − esparso)',
                    '(c) Queda do F1 contra o esparso, mesma repetição', (-0.34, 0.04), h4)
    hnd = [Line2D([], [], color=COLORS[f], lw=2, marker='o', ms=5, label=NAME[f]) for f in FLOWS]
    hnd += [Line2D([], [], color='#555555', lw=0, marker='o', ms=5, label='um ponto = uma repetição'),
            Line2D([], [], color='#555555', lw=2.2, label='traço = média das 5')]
    fig.legend(handles=hnd, loc='center', bbox_to_anchor=(0.5, 3.36 / H), ncol=5, fontsize=10, frameon=False)
    for ext in ('png', 'pdf'):
        fig.savefig(out / f'explica_regra_caiu.{ext}', dpi=150, facecolor='white')
    print('wrote', out / 'explica_regra_caiu.png')
    print('fillers in the scene:', {L: ims[L]['n_fill'] for L in LEVELS})
    print('covered %:', (100 * lvl.covered).round(2).to_dict())
    for name, s in (('rejection', sr), ('f1', sf)):
        print(name, 'k of 5:', {f: [s[L, f] for L in LEVELS[1:]] for f in FLOWS})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--out', default=str(ROOT / 'docs' / 'exp_resolucao' / 'img'))
    main(p.parse_args().out)
