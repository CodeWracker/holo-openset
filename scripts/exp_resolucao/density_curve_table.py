"""The table of the density curve and the rules of Q0 b (CADERNO_CURVA.md), applied mechanically.

For each level of the family (8 = the sparse set, 15, 69, 154, 343, 514 -> data/curve_<law>_L<level>) and each repetition
with an evaluation json:
  density      letters per 640 x 640 window obtained (annotated + fillers, metadata.csv) and per mm^2 (window 1.142
               mm^2); covered area (sum of the ink boxes, <set>_checks.json; for the sparse level, from its
               annotations: the same measure, the ink boxes bx0..by1); skipped fillers
  overlap      1 - exp(-pi D^2 sigma) and pi D^2 sigma (the axis of Q1), D the axis measure of
               hologram_diameter_summary.json (D_rms(192) = 111.8 um), sigma the obtained density
  per flow     F1, rejection of the unseen, closed accuracy; minus the same flow on the sparse level in the same
               repetition; fell_f1 (<= -0.10), fell_rej (<= -0.30)
  differences  prop - raw and rec_z0 - prop, as rows with flow 'prop - raw', 'rec_z0 - prop'
Reading: with r1 only, provisional. "fell" with five repetitions = in at least 4 of 5. "The curves separate" at a
level (r1): prop - raw >= 0.10 in F1, or >= 0.30 in rejection, or some flow fell; the sparse level always. "Where the
layer falls": the first level (by increasing density) where prop fell in F1, and in rejection, reported separately
(from the five repetitions where they exist, from r1 elsewhere). Thresholds of P0 (prop - raw >= 0.10 and >= 0.30)
counted over the five repetitions, descriptively.
-> $HOLO_RESULTS/<prefix>_reps.csv (one row per level, repetition and flow), <prefix>.csv (one row per level and
   flow: r1 and mean / min / max over the repetitions, the flags), <prefix>_reading.json
"""
import argparse
import json
import math

import pandas as pd

from holo_openset import paths
from holo_openset.sim.physics import PIXEL

LEVELS = [8, 15, 69, 154, 343, 514]
FLOWS = ['raw', 'prop', 'rec_z0']
DIFFS = [('prop - raw', 'prop', 'raw'), ('rec_z0 - prop', 'rec_z0', 'prop')]
METRICS = {'novel_open_macro_f1': 'f1', 'novel_unknown_rejection': 'rejection', 'novel_closed_acc': 'closed_acc'}
WINDOW_MM2 = (640 * PIXEL * 1e3) ** 2


def set_name(law, level, sparse):
    return sparse if level == 8 else f'curve_{law}_L{level:03d}'


def level_info(s, d_mm):
    root = paths.dataset(s)
    m = pd.read_csv(root / 'metadata.csv')
    fill = m.n_fill_window if 'n_fill_window' in m else 0
    per_win = float((m.n_letters + fill).mean())
    sigma = per_win / WINDOW_MM2
    ck = paths.RESULTS / f'{s}_checks.json'
    if ck.exists() and 'covered_fraction' in json.load(open(ck)):
        cov = json.load(open(ck))['covered_fraction']['dense_total']['box_area']
    else:   # no fillers: the ink boxes of the annotations (the letters in the window are all annotated)
        a = pd.read_csv(root / 'annotations.csv')
        area = ((a.bx1 - a.bx0) * (a.by1 - a.by0)).groupby(a.image_id).sum().reindex(m.image_id, fill_value=0)
        cov = float(area.mean() / 640 ** 2)
    fills = int((m.n_fill_window + m.n_fill_band).sum()) if 'n_fill_window' in m else 0
    skipped = int(m.n_fill_skipped.sum()) if 'n_fill_skipped' in m else 0
    return dict(set=s, letters_per_window=per_win, per_mm2=sigma, covered=cov,
                fillers_skipped_share=skipped / fills if fills else 0.0,
                pi_D2_sigma=math.pi * d_mm ** 2 * sigma, overlap=1 - math.exp(-math.pi * d_mm ** 2 * sigma))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--law', required=True)
    ap.add_argument('--sparse', required=True)
    ap.add_argument('--prefix', default='density_curve')
    a = ap.parse_args()
    summ = json.load(open(paths.RESULTS / 'hologram_diameter_summary.json'))
    d_mm = summ['D_ef_px'][summ['axis']] * PIXEL * 1e3
    rows, info = [], {}
    for lv in LEVELS:
        s = set_name(a.law, lv, a.sparse)
        if not (paths.dataset(s) / 'metadata.csv').exists():
            continue
        info[lv] = level_info(s, d_mm)
        for r in range(1, 6):
            got = {}
            for f in FLOWS:
                p = paths.RESULTS / 'eval' / s / f'{f}_r{r}.json'
                if p.exists():
                    j = json.load(open(p))
                    got[f] = {v: j[k] for k, v in METRICS.items()}
            for f, v in got.items():
                rows.append(dict(level=lv, rep=r, flow=f, **info[lv], **v))
            for name, x, y in DIFFS:
                if x in got and y in got:
                    rows.append(dict(level=lv, rep=r, flow=name, **info[lv],
                                     **{m: got[x][m] - got[y][m] for m in METRICS.values()}))
    t = pd.DataFrame(rows)
    if t.empty:
        raise SystemExit('no evaluation yet')
    sp = t[t.level == 8].set_index(['rep', 'flow'])
    for m_, k in [('f1', 'd_f1'), ('rejection', 'd_rej')]:
        t[k] = [getattr(r, m_) - sp.loc[(r.rep, r.flow), m_] if r.flow in FLOWS and (r.rep, r.flow) in sp.index
                else math.nan for r in t.itertuples()]
    t['fell_f1'] = t.d_f1 <= -0.10
    t['fell_rej'] = t.d_rej <= -0.30
    t.to_csv(paths.RESULTS / f'{a.prefix}_reps.csv', index=False, float_format='%.6g')
    # one row per level and flow
    summary, reading = [], dict(law=a.law, axis=summ['axis'], D_um=d_mm * 1e3, levels={})
    first = dict(f1=None, rej=None)
    for lv in sorted(t.level.unique()):
        g = t[t.level == lv]
        reps = sorted(g[g.flow == 'raw'].rep.unique())
        five = len(reps) == 5
        lvr = dict(**info[lv], reps=[int(x) for x in reps])
        for f in FLOWS + [d[0] for d in DIFFS]:
            h = g[g.flow == f].set_index('rep')
            if h.empty:
                continue
            row = dict(level=lv, flow=f, **info[lv], n_reps=len(h))
            for m in METRICS.values():
                row[f'{m}_r1'] = h.loc[1, m] if 1 in h.index else math.nan
                row[f'{m}_mean'], row[f'{m}_min'], row[f'{m}_max'] = h[m].mean(), h[m].min(), h[m].max()
            if f in FLOWS:
                row['d_f1_r1'] = h.loc[1, 'd_f1'] if 1 in h.index else math.nan
                row['d_rej_r1'] = h.loc[1, 'd_rej'] if 1 in h.index else math.nan
                row['d_f1_mean'], row['d_rej_mean'] = h.d_f1.mean(), h.d_rej.mean()
                row['fell_f1_r1'] = bool(h.loc[1, 'fell_f1']) if 1 in h.index else None
                row['fell_rej_r1'] = bool(h.loc[1, 'fell_rej']) if 1 in h.index else None
                row['fell_f1_count'] = int(h.fell_f1.sum())
                row['fell_rej_count'] = int(h.fell_rej.sum())
                row['fell_f1_4of5'] = (int(h.fell_f1.sum()) >= 4) if five else None
                row['fell_rej_4of5'] = (int(h.fell_rej.sum()) >= 4) if five else None
            if f == 'prop - raw':
                row['p0_f1_count'] = int((h.f1 >= 0.10).sum())
                row['p0_rej_count'] = int((h.rejection >= 0.30).sum())
                row['p0_both_count'] = int(((h.f1 >= 0.10) & (h.rejection >= 0.30)).sum())
            summary.append(row)
        sl = pd.DataFrame([r for r in summary if r['level'] == lv]).set_index('flow')
        if 1 in reps:
            fell = {f: dict(f1=bool(sl.loc[f, 'fell_f1_r1']), rej=bool(sl.loc[f, 'fell_rej_r1'])) for f in FLOWS}
            pr = sl.loc['prop - raw']
            lvr['r1'] = dict(prop_minus_raw=dict(f1=pr.f1_r1, rej=pr.rejection_r1),
                             rec_minus_prop=dict(f1=sl.loc['rec_z0 - prop', 'f1_r1'],
                                                 rej=sl.loc['rec_z0 - prop', 'rejection_r1']), fell=fell)
            lvr['separate_r1'] = bool(lv == 8 or pr.f1_r1 >= 0.10 or pr.rejection_r1 >= 0.30 or
                                      any(v['f1'] or v['rej'] for v in fell.values()))
        if five:
            lvr['fell_4of5'] = {f: dict(f1=bool(sl.loc[f, 'fell_f1_4of5']), rej=bool(sl.loc[f, 'fell_rej_4of5']))
                                for f in FLOWS}
            pr = sl.loc['prop - raw']
            lvr['p0_thresholds_of_5'] = dict(f1=int(pr.p0_f1_count), rej=int(pr.p0_rej_count),
                                             both=int(pr.p0_both_count))
        src = lvr.get('fell_4of5') or (lvr.get('r1') or {}).get('fell')
        if src and lv != 8:
            for k in ('f1', 'rej'):
                if first[k] is None and src['prop'][k]:
                    first[k] = int(lv)
        reading['levels'][int(lv)] = lvr
    pd.DataFrame(summary).to_csv(paths.RESULTS / f'{a.prefix}.csv', index=False, float_format='%.6g')
    reading['layer_falls_first'] = {k: (v if v is not None else 'did not fall up to the obtained density')
                                    for k, v in first.items()}
    reading['provisional'] = any(len(v['reps']) < 5 for v in reading['levels'].values())
    json.dump(reading, open(paths.RESULTS / f'{a.prefix}_reading.json', 'w'), indent=1, default=float)
    with pd.option_context('display.width', 250, 'display.max_columns', 40):
        print(pd.DataFrame(summary)[['level', 'flow', 'n_reps', 'letters_per_window', 'overlap', 'f1_r1',
                                     'rejection_r1', 'f1_mean', 'rejection_mean']].to_string())
    print(json.dumps(reading, indent=1, default=float))


if __name__ == '__main__':
    main()
