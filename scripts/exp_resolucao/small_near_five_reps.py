"""Q3-C (docs/exp_resolucao/CADERNO_CURVA.md): the column of the small letters at 2 mm with the re-recorded set
(small_near_newrec), the ten flows of the size table (SMALL_FLOWS of pipeline.py) in r1-r5, next to the column of the
paper (small_near recorded at the sampling of the sensor; results/eval/small_near, READ only).

-> $HOLO_RESULTS/small_near_newrec_five_reps.csv
   kind=rep    per flow and repetition: F1 (novel_open_macro_f1), rejection of the unseen, closed accuracy, known
               accuracy, for the new set and for the paper's set
   kind=stat   per flow: mean / min / max over the five repetitions of both, and new - paper of the means
   and $HOLO_RESULTS/small_near_newrec_five_reps_reading.json: the registered prediction (no mean F1 moves more than
   0.02; the order of the routes the same: crops far below, the routes with propagation together), checked
    python scripts/exp_resolucao/small_near_five_reps.py
"""
import json

import pandas as pd

from holo_openset import paths

FLOWS = ['raw', 'learned', 'complex', 'wiener', 'prop', 'bank_jit', 'bank_w3', 'rec_z0', 'rec_af', 'rec_twin']
M = {'novel_open_macro_f1': 'f1', 'novel_unknown_rejection': 'rejection', 'novel_closed_acc': 'closed_acc',
     'novel_known_acc': 'known_acc'}
PROPAGATION = ['wiener', 'prop', 'bank_jit', 'bank_w3', 'rec_z0', 'rec_af', 'rec_twin']   # every route with a propagation


def load(root, name):
    rows = []
    for f in FLOWS:
        for r in range(1, 6):
            j = json.load(open(root / 'eval' / name / f'{f}_r{r}.json'))
            rows.append(dict(flow=f, rep=r, **{v: j[k] for k, v in M.items()}))
    return pd.DataFrame(rows)


def main():
    new = load(paths.RESULTS, 'small_near_newrec')
    old = load(paths.PROJECT / 'results', 'small_near')
    t = new.merge(old, on=['flow', 'rep'], suffixes=('', '_paper'))
    t.insert(0, 'kind', 'rep')
    stats = []
    for f in FLOWS:
        g = t[t.flow == f]
        for st in ['mean', 'min', 'max']:
            stats.append(dict(kind='stat', flow=f, rep=st, **{c: getattr(g[c], st)() for c in t.columns
                                                              if c not in ('kind', 'flow', 'rep')}))
    s = pd.DataFrame(stats)
    means = s[s.rep == 'mean'].set_index('flow')
    for m in M.values():
        s.loc[s.rep == 'mean', f'{m}_new_minus_paper'] = (means[m] - means[f'{m}_paper']).to_numpy()
    out = pd.concat([t, s], ignore_index=True)
    out.to_csv(paths.RESULTS / 'small_near_newrec_five_reps.csv', index=False, float_format='%.6g')
    d = (means.f1 - means.f1_paper)
    order_new = list(means.f1.sort_values(ascending=False).index)
    order_old = list(means.f1_paper.sort_values(ascending=False).index)
    gap = lambda col: float(means.loc[PROPAGATION, col].min() - means.loc['raw', col])   # noqa: E731
    reading = dict(
        max_abs_mean_f1_change=float(d.abs().max()), flow_of_max=str(d.abs().idxmax()),
        f1_change_by_flow={k: float(v) for k, v in d.items()},
        within_0_02=bool(d.abs().max() <= 0.02),
        order_by_mean_f1_new=order_new, order_by_mean_f1_paper=order_old, same_order=order_new == order_old,
        crops_lowest_new=order_new[-1] == 'raw', crops_lowest_paper=order_old[-1] == 'raw',
        propagation_routes_f1_range_new=[float(means.loc[PROPAGATION, 'f1'].min()),
                                         float(means.loc[PROPAGATION, 'f1'].max())],
        propagation_routes_f1_range_paper=[float(means.loc[PROPAGATION, 'f1_paper'].min()),
                                           float(means.loc[PROPAGATION, 'f1_paper'].max())],
        lowest_propagation_minus_crops_f1=dict(new=gap('f1'), paper=gap('f1_paper')),
        note='routes with propagation: ' + ', '.join(PROPAGATION) + '; learned and complex are layers without a '
             'propagation phase')
    json.dump(reading, open(paths.RESULTS / 'small_near_newrec_five_reps_reading.json', 'w'), indent=1)
    with pd.option_context('display.width', 250, 'display.max_columns', 30):
        print(s[s.rep == 'mean'][['flow', 'f1', 'f1_paper', 'f1_new_minus_paper', 'rejection', 'rejection_paper',
                                   'rejection_new_minus_paper']].round(4).to_string(index=False))
    print(json.dumps(reading, indent=1))


if __name__ == '__main__':
    main()
