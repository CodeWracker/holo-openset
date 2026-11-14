"""Paired enrollment test (docs/exp_resolucao/PROTOCOLO.md, framing section): per repetition, the enrollment metrics
of `prop` and of `bank_jit` minus those of each reconstruction flow, from the strict evaluations of the paper
(results/eval/realistic/<flow>_r<rep>.json; read only). Writes $HOLO_RESULTS/enroll_paired.csv.

    python scripts/exp_resolucao/enroll_paired.py
"""
import json

import numpy as np
import pandas as pd

from holo_openset import paths

SRC = paths.PROJECT / 'results' / 'eval' / 'realistic'
METRICS = ['world5_new_class_acc', 'world20_new_class_acc', 'worldall_new_class_acc', 'world20_new_class_rank1',
           'world20_absent_rejection', 'world20_seen_acc', 'world5_new_class_rank1', 'world5_absent_rejection',
           'world5_seen_acc']
LAYERS = ['prop', 'bank_jit']
RECS = ['rec_z0', 'rec_af', 'rec_afc', 'rec_edf', 'rec_twin']
REPS = [1, 2, 3, 4, 5]


def load(flow, rep):
    d = json.load(open(SRC / f'{flow}_r{rep}.json'))
    assert d['rep'] == rep and d.get('tag', '') == '' and d.get('train_set', 'realistic') == 'realistic', (flow, rep)
    return d


def main():
    rows = []
    for a in LAYERS:
        for b in RECS:
            for m in METRICS:
                va = np.array([load(a, r)[m] for r in REPS])
                vb = np.array([load(b, r)[m] for r in REPS])
                d = va - vb
                s = np.sign(d.mean())
                rows.append(dict(layer=a, reconstruction=b, metric=m, layer_mean=va.mean(), rec_mean=vb.mean(),
                                 diff_mean=d.mean(), diff_min=d.min(), diff_max=d.max(),
                                 same_sign_as_mean=int((np.sign(d) == s).sum()) if s != 0 else 0,
                                 **{f'diff_r{r}': v for r, v in zip(REPS, d)}))
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    out = paths.RESULTS / 'enroll_paired.csv'
    pd.DataFrame(rows).to_csv(out, index=False, float_format='%.6f')
    print(out)
    t = pd.DataFrame(rows)
    pd.set_option('display.width', 250)
    print(t[['layer', 'reconstruction', 'metric', 'layer_mean', 'rec_mean', 'diff_mean', 'diff_min', 'diff_max',
             'same_sign_as_mean']].round(3).to_string(index=False))


if __name__ == '__main__':
    main()
