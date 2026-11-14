"""P2 / A of the pilot at 1.0 mm: the five repetitions of bench_1mm side by side, and the criterion of P0 applied
mechanically: a repetition counts in favour if F1(prop) - F1(raw) >= 0.10 AND rejection(prop) - rejection(raw) >= 0.30
(test split, novel_open_macro_f1 and novel_unknown_rejection, threshold from validation); the thesis holds with 4 or 5.

  pilot_five_reps.csv             per repetition and flow: F1, rejection, closed-set accuracy, known accuracy,
                                  threshold (kind = 'flow'); per repetition the gaps prop - raw and rec_z0 - prop and
                                  the three conditions (kind = 'gap'); mean, min, max of every number and the count of
                                  repetitions meeting each condition (kind = 'summary')
  pilot_five_reps_robustness.csv  the robustness rows (robustness_bench_1mm.csv) per repetition, and their mean, min, max
  pilot_five_reps_alpha.csv       the alpha of prop per repetition: calibrated at the start of training (train.calibrate
                                  _alpha on the same 32 training holograms that train() drew, recomputed here on the CPU)
                                  and after training (the checkpoint), in mm

    python scripts/exp_resolucao/pilot_five_reps.py [--set bench_1mm]
"""
import argparse
import json
import math

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.flows import dataset
from holo_openset.protocol import classes
from holo_openset.sim.physics import PIXEL, WAVELENGTH
from holo_openset.train import calibrate_alpha

FLOWS = ['raw', 'prop', 'rec_z0']
KEYS = {'f1': 'novel_open_macro_f1', 'rejection': 'novel_unknown_rejection', 'closed_acc': 'novel_closed_acc',
        'known_acc': 'novel_known_acc', 'threshold': 'threshold'}
REPS = [1, 2, 3, 4, 5]


def mm(alpha):
    return alpha * (640 * PIXEL) ** 2 / (math.pi * WAVELENGTH) * 1e3


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--set', default='bench_1mm')
    ap.add_argument('--extend', type=int, default=12, help='the --alpha-extend of the trainings of prop')
    a = ap.parse_args()
    torch.set_num_threads(4)
    R = paths.RESULTS
    rows = []
    for r in REPS:
        for f in FLOWS:
            d = json.load(open(R / 'eval' / a.set / f'{f}_r{r}.json'))
            rows.append(dict(kind='flow', rep=r, flow=f, **{k: d[v] for k, v in KEYS.items()}))
    t = pd.DataFrame(rows)
    gaps = []
    for r in REPS:
        x = t[t.rep == r].set_index('flow')
        g = dict(kind='gap', rep=r, flow='prop - raw',
                 f1=x.f1['prop'] - x.f1['raw'], rejection=x.rejection['prop'] - x.rejection['raw'])
        g.update(meets_f1=g['f1'] >= 0.10, meets_rejection=g['rejection'] >= 0.30)
        g['meets_both'] = g['meets_f1'] and g['meets_rejection']
        gaps.append(g)
        gaps.append(dict(kind='gap', rep=r, flow='rec_z0 - prop', f1=x.f1['rec_z0'] - x.f1['prop'],
                         rejection=x.rejection['rec_z0'] - x.rejection['prop']))
    g = pd.DataFrame(gaps)
    summ = []
    for df in (t, g):
        for flow, x in df.groupby('flow', sort=False):
            for stat in ('mean', 'min', 'max'):
                row = dict(kind='summary', rep=stat, flow=flow)
                for k in ('f1', 'rejection', 'closed_acc', 'known_acc', 'threshold'):
                    if k in x and x[k].notna().any():
                        row[k] = getattr(x[k], stat)()
                summ.append(row)
    p = g[g.flow == 'prop - raw']
    summ.append(dict(kind='summary', rep='count of 5', flow='prop - raw', meets_f1=int(p.meets_f1.sum()),
                     meets_rejection=int(p.meets_rejection.sum()), meets_both=int(p.meets_both.sum())))
    out = pd.concat([t, g, pd.DataFrame(summ)], ignore_index=True)
    out.to_csv(R / 'pilot_five_reps.csv', index=False, float_format='%.4f')
    pd.set_option('display.width', 250)
    print(out.to_string(index=False))
    n = int(p.meets_both.sum())
    print(f'criterion of P0: {n} of 5 repetitions meet both conditions (F1 gap >= 0.10 and rejection gap >= 0.30); '
          f'the rule asks 4 or 5')

    rb = pd.read_csv(R / 'robustness_bench_1mm.csv')
    rb = rb[rb.rep.isin(REPS)][['rep', 'variant', 'flow', 'novel_open_macro_f1', 'novel_unknown_rejection',
                                'novel_closed_acc', 'novel_known_acc']]
    s = rb.groupby(['variant', 'flow'], sort=False).agg(['mean', 'min', 'max', 'count'])
    s.columns = [f'{m}_{st}' for m, st in s.columns]
    rb.to_csv(R / 'pilot_five_reps_robustness_rows.csv', index=False, float_format='%.4f')
    s.reset_index().to_csv(R / 'pilot_five_reps_robustness.csv', index=False, float_format='%.4f')
    print(s[[c for c in s.columns if c.startswith(('novel_open', 'novel_unknown'))]].round(4).to_string())

    ds = dataset('prop', paths.dataset(a.set))
    ann = ds.ann
    al = []
    for r in REPS:
        seen = classes(r)[0]
        tr = ann[(ann.split == 'train') & ann.classe.isin(seen)]
        ids = np.random.RandomState(0).choice(np.unique(tr.image_id), 32, replace=False)   # as train() draws them
        a0 = calibrate_alpha(ds.images(ids), 'cpu', extend=a.extend)
        ck = torch.load(paths.weights('prop', r, a.set), map_location='cpu', weights_only=False)
        a1 = float(ck['state_dict']['fourier.alpha'].mean())
        al.append(dict(rep=r, alpha_calibrated=a0, z_calibrated_mm=mm(a0), alpha_trained=a1, z_trained_mm=mm(a1),
                       change=a1 / a0 - 1))
    al = pd.DataFrame(al)
    al.to_csv(R / 'pilot_five_reps_alpha.csv', index=False, float_format='%.7g')
    print(al.to_string(index=False))


if __name__ == '__main__':
    main()
