"""Item a of Q0 (CADERNO_CURVA.md): the five repetitions on the dense set of the pilot (bench_1mm_dense).

Rows of $HOLO_RESULTS/dense_five_reps.csv:
  kind=flow   one per repetition and flow (raw, prop, rec_z0): F1 (novel_open_macro_f1), rejection of the unseen
              (novel_unknown_rejection), closed accuracy (novel_closed_acc), and auroc, known accuracy, threshold
  kind=diff   one per repetition: prop - raw and rec_z0 - prop in the same three metrics
  kind=stat   mean / min / max over the repetitions of every row above
  kind=count  how many repetitions meet each threshold of the criterion of P0 for prop - raw (F1 >= 0.10,
              rejection >= 0.30, both), applied descriptively
    python scripts/exp_resolucao/dense_five_reps.py [--set bench_1mm_dense]
"""
import argparse
import json

import pandas as pd

from holo_openset import paths

FLOWS = ['raw', 'prop', 'rec_z0']
M = {'novel_open_macro_f1': 'f1', 'novel_unknown_rejection': 'rejection', 'novel_closed_acc': 'closed_acc',
     'novel_auroc': 'auroc', 'novel_known_acc': 'known_acc', 'threshold': 'threshold'}
MAIN = ['f1', 'rejection', 'closed_acc']


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--set', default='bench_1mm_dense')
    ap.add_argument('--out', default='dense_five_reps.csv')
    a = ap.parse_args()
    rows = []
    for r in range(1, 6):
        for f in FLOWS:
            p = paths.RESULTS / 'eval' / a.set / f'{f}_r{r}.json'
            if not p.exists():
                raise SystemExit(f'missing {p}')
            j = json.load(open(p))
            rows.append(dict(kind='flow', rep=r, flow=f, **{v: j[k] for k, v in M.items()}))
    t = pd.DataFrame(rows)
    diffs = []
    for r in range(1, 6):
        g = t[t.rep == r].set_index('flow')
        for name, x, y in [('prop - raw', 'prop', 'raw'), ('rec_z0 - prop', 'rec_z0', 'prop')]:
            diffs.append(dict(kind='diff', rep=r, flow=name, **{m: g.loc[x, m] - g.loc[y, m] for m in MAIN}))
    t = pd.concat([t, pd.DataFrame(diffs)], ignore_index=True)
    stats = []
    for f, g in t.groupby('flow', sort=False):
        for s in ['mean', 'min', 'max']:
            stats.append(dict(kind='stat', rep=s, flow=f, **{m: getattr(g[m], s)() for m in MAIN}))
    t = pd.concat([t, pd.DataFrame(stats)], ignore_index=True)
    d = t[(t.kind == 'diff') & (t.flow == 'prop - raw')]
    c1, c2 = d.f1 >= 0.10, d.rejection >= 0.30
    counts = [dict(kind='count', rep='of 5', flow='prop - raw', f1=int(c1.sum()), rejection=int(c2.sum()),
                   closed_acc=None, note='repetitions with F1 >= 0.10 / rejection >= 0.30; both: '
                                         f'{int((c1 & c2).sum())}')]
    t = pd.concat([t, pd.DataFrame(counts)], ignore_index=True)
    t.to_csv(paths.RESULTS / a.out, index=False, float_format='%.6g')
    with pd.option_context('display.width', 200, 'display.max_columns', 20):
        print(t.to_string())


if __name__ == '__main__':
    main()
