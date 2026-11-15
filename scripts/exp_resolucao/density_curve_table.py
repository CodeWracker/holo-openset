"""The table of the density curve and the rules of Q0 b (CADERNO_CURVA.md), applied mechanically.

For each level of the family (8 = the sparse set, 15, 69, 154, 343 -> data/curve_<law>_L<level>) and each repetition
with an evaluation json:
  density      letters per 640 x 640 window obtained (annotated + fillers, metadata.csv) and per mm^2 (window 1.142
               mm^2); covered area (sum of the ink boxes, <set>_checks.json, when it exists)
  overlap      1 - exp(-pi D_ef^2 sigma), D_ef the axis measure of hologram_diameter_summary.json, sigma the obtained
               density
  per flow     F1, rejection of the unseen, closed accuracy; minus the same flow on the sparse level in the same
               repetition; fell_f1 (<= -0.10), fell_rej (<= -0.30)
  per level    prop - raw (F1, rejection), rec_z0 - prop
Reading: with r1 only, provisional. "fell" with five repetitions = in at least 4 of 5. "The curves separate" at a
level (r1): prop - raw >= 0.10 in F1, or >= 0.30 in rejection, or some flow fell; the sparse level always. "Where the
layer falls": the first level (by increasing density) where prop fell in F1, and in rejection, reported separately.
-> $HOLO_RESULTS/density_curve_<law>.csv, density_curve_<law>_reading.json
"""
import argparse
import json
import math

import pandas as pd

from holo_openset import paths
from holo_openset.sim.physics import PIXEL

LEVELS = [8, 15, 69, 154, 343]
FLOWS = ['raw', 'prop', 'rec_z0']
WINDOW_MM2 = (640 * PIXEL * 1e3) ** 2


def set_name(law, level, sparse):
    return sparse if level == 8 else f'curve_{law}_L{level:03d}'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--law', required=True)
    ap.add_argument('--sparse', required=True)
    a = ap.parse_args()
    summ = json.load(open(paths.RESULTS / 'hologram_diameter_summary.json'))
    d_mm = summ['D_ef_px'][summ['axis']] * PIXEL * 1e3
    rows = []
    for lv in LEVELS:
        s = set_name(a.law, lv, a.sparse)
        root = paths.dataset(s)
        if not (root / 'metadata.csv').exists():
            continue
        m = pd.read_csv(root / 'metadata.csv')
        per_win = float((m.n_letters + (m.n_fill_window if 'n_fill_window' in m else 0)).mean())
        sigma = per_win / WINDOW_MM2
        ck = paths.RESULTS / f'{s}_checks.json'
        cov = json.load(open(ck))['covered_fraction']['dense_total']['box_area'] if ck.exists() else math.nan
        skipped = int(m.n_fill_skipped.sum()) if 'n_fill_skipped' in m else 0
        fills = int((m.n_fill_window + m.n_fill_band).sum()) if 'n_fill_window' in m else 0
        for r in range(1, 6):
            for f in FLOWS:
                p = paths.RESULTS / 'eval' / s / f'{f}_r{r}.json'
                if not p.exists():
                    continue
                j = json.load(open(p))
                rows.append(dict(level=lv, set=s, rep=r, flow=f, letters_per_window=per_win, per_mm2=sigma,
                                 covered=cov, overlap=1 - math.exp(-math.pi * d_mm ** 2 * sigma),
                                 fillers_skipped_share=skipped / fills if fills else 0.0,
                                 f1=j['novel_open_macro_f1'], rejection=j['novel_unknown_rejection'],
                                 closed_acc=j['novel_closed_acc']))
    t = pd.DataFrame(rows)
    if t.empty:
        raise SystemExit('no evaluation yet')
    sp = t[t.level == 8].set_index(['rep', 'flow'])
    for m_, k in [('f1', 'd_f1'), ('rejection', 'd_rej')]:
        t[k] = [getattr(r, m_) - sp.loc[(r.rep, r.flow), m_] if (r.rep, r.flow) in sp.index else math.nan
                for r in t.itertuples()]
    t['fell_f1'] = t.d_f1 <= -0.10
    t['fell_rej'] = t.d_rej <= -0.30
    t.to_csv(paths.RESULTS / f'density_curve_{a.law}.csv', index=False, float_format='%.6g')
    reading = dict(axis=summ['axis'], D_ef_um=d_mm * 1e3, levels={})
    first = dict(f1=None, rej=None)
    for lv in sorted(t.level.unique()):
        g = t[t.level == lv]
        reps = sorted(g.rep.unique())
        lvr = dict(set=g.set.iloc[0], reps=[int(x) for x in reps], letters_per_window=float(g.letters_per_window.iloc[0]),
                   per_mm2=float(g.per_mm2.iloc[0]), overlap=float(g.overlap.iloc[0]))
        r1 = g[g.rep == 1].set_index('flow')
        if set(FLOWS) <= set(r1.index):
            dpf, dpr = r1.loc['prop', 'f1'] - r1.loc['raw', 'f1'], r1.loc['prop', 'rejection'] - r1.loc['raw', 'rejection']
            fell = {f: dict(f1=bool(r1.loc[f, 'fell_f1']), rej=bool(r1.loc[f, 'fell_rej'])) for f in FLOWS}
            lvr['r1'] = dict(prop_minus_raw=dict(f1=dpf, rej=dpr),
                             rec_minus_prop=dict(f1=r1.loc['rec_z0', 'f1'] - r1.loc['prop', 'f1'],
                                                 rej=r1.loc['rec_z0', 'rejection'] - r1.loc['prop', 'rejection']),
                             fell=fell)
            lvr['separate_r1'] = bool(lv == 8 or dpf >= 0.10 or dpr >= 0.30 or
                                      any(v['f1'] or v['rej'] for v in fell.values()))
        if len(reps) == 5:
            lvr['fell_5reps'] = {f: dict(f1=int(g[g.flow == f].fell_f1.sum()) >= 4,
                                         rej=int(g[g.flow == f].fell_rej.sum()) >= 4) for f in FLOWS}
            d = g.pivot(index='rep', columns='flow', values=['f1', 'rejection'])
            c1 = (d['f1']['prop'] - d['f1']['raw']) >= 0.10
            c2 = (d['rejection']['prop'] - d['rejection']['raw']) >= 0.30
            lvr['p0_thresholds_of_5'] = dict(f1=int(c1.sum()), rej=int(c2.sum()), both=int((c1 & c2).sum()))
        src = lvr.get('fell_5reps') or (lvr.get('r1') or {}).get('fell')
        if src and lv != 8:
            for k in ('f1', 'rej'):
                if first[k] is None and src['prop'][k]:
                    first[k] = int(lv)
        reading['levels'][int(lv)] = lvr
    reading['layer_falls_first'] = {k: (v if v is not None else 'did not fall up to the obtained density')
                                    for k, v in first.items()}
    reading['provisional'] = any(len(v['reps']) < 5 for v in reading['levels'].values())
    json.dump(reading, open(paths.RESULTS / f'density_curve_{a.law}_reading.json', 'w'), indent=1, default=float)
    with pd.option_context('display.width', 220, 'display.max_columns', 30):
        print(t.to_string())
    print(json.dumps(reading, indent=1, default=float))


if __name__ == '__main__':
    main()
