"""Z6.1: what the three sets the paper already has say about the distance (existing results only, read from
results/eval/{realistic,small_z0,small_near}/<flow>_r<rep>.json). Per set and flow: mean of the five repetitions,
standard deviation, min and max of the open-set and enrollment metrics; per set, every flow minus the hologram crops
(`raw`) per repetition, and how that gap moves from one set to another (per repetition).
Writes $HOLO_RESULTS/small_preview.csv and small_preview_gaps.csv.

    python scripts/exp_resolucao/small_preview.py
"""
import json

import numpy as np
import pandas as pd

from holo_openset import paths

SRC = paths.PROJECT / 'results' / 'eval'
SETS = ['realistic', 'small_z0', 'small_near']
METRICS = ['novel_open_macro_f1', 'novel_unknown_rejection', 'novel_known_acc', 'novel_auroc', 'world5_new_class_acc',
           'world20_new_class_acc', 'worldall_new_class_acc', 'world20_absent_rejection']
REPS = [1, 2, 3, 4, 5]


def load(s, flow):
    out = []
    for r in REPS:
        f = SRC / s / f'{flow}_r{r}.json'
        if not f.exists():
            return None
        d = json.load(open(f))
        assert d['rep'] == r and d.get('tag', '') == '' and d.get('train_set', s) == s, (s, flow, r)
        out.append(d)
    return out


def main():
    flows = sorted(set.intersection(*[{p.stem.rsplit('_r', 1)[0] for p in (SRC / s).glob('*_r1.json')} for s in SETS]))
    vals, rows, gaps = {}, [], []
    for s in SETS:
        for f in flows:
            d = load(s, f)
            if d is None:
                continue
            for m in METRICS:
                v = np.array([x[m] for x in d])
                vals[(s, f, m)] = v
                rows.append(dict(set=s, flow=f, metric=m, mean=v.mean(), std=v.std(ddof=1), min=v.min(), max=v.max(),
                                 **{f'r{r}': x for r, x in zip(REPS, v)}))
    for s in SETS:
        for f in flows:
            if f == 'raw':
                continue
            for m in METRICS:
                d = vals[(s, f, m)] - vals[(s, 'raw', m)]
                gaps.append(dict(comparison=f'{s}: {f} - raw', set=s, flow=f, metric=m, diff_mean=d.mean(),
                                 diff_min=d.min(), diff_max=d.max(),
                                 same_sign=int((np.sign(d) == np.sign(d.mean())).sum()),
                                 **{f'r{r}': x for r, x in zip(REPS, d)}))
    for a, b in [('small_near', 'small_z0'), ('small_z0', 'realistic'), ('small_near', 'realistic')]:
        for f in flows:
            if f == 'raw':
                continue
            for m in METRICS:
                d = (vals[(a, f, m)] - vals[(a, 'raw', m)]) - (vals[(b, f, m)] - vals[(b, 'raw', m)])
                gaps.append(dict(comparison=f'({f} - raw) at {a} minus at {b}', set=f'{a}-{b}', flow=f, metric=m,
                                 diff_mean=d.mean(), diff_min=d.min(), diff_max=d.max(),
                                 same_sign=int((np.sign(d) == np.sign(d.mean())).sum()),
                                 **{f'r{r}': x for r, x in zip(REPS, d)}))
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(paths.RESULTS / 'small_preview.csv', index=False, float_format='%.6f')
    pd.DataFrame(gaps).to_csv(paths.RESULTS / 'small_preview_gaps.csv', index=False, float_format='%.6f')
    pd.set_option('display.width', 250)
    t = pd.DataFrame(rows)
    print(t[t.metric == 'novel_open_macro_f1'].pivot(index='flow', columns='set', values='mean').round(3))
    g = pd.DataFrame(gaps)
    print(g[g.metric == 'novel_open_macro_f1'][['comparison', 'diff_mean', 'diff_min', 'diff_max', 'same_sign']]
          .round(3).to_string(index=False))


if __name__ == '__main__':
    main()
