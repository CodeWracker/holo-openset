"""R4 of the pilot at 1.0 mm: the open-set numbers on the VALIDATION split, which the evaluate command does not report
(its open-set metrics are on the test split). The definition is the calibration of evaluate.calibrate (the strict
protocol): the seen classes of the repetition in 4 folds; for each fold, gallery = the even-indexed validation images
without the held-out fold, queries = the odd-indexed validation images, the held-out seen classes play the unknowns;
at the threshold t of the repetition (5 % quantile of the genuine scores, as evaluate) the metrics of
evaluate.open_set_metrics (open-set macro-F1, unknown rejection, known accuracy, closed-set accuracy, AUROC) per fold
and their mean. Nothing of the test split is read.
-> $HOLO_RESULTS/eval/<set>/val_openset_r<rep>.csv

    python scripts/exp_resolucao/val_openset.py --set bench_1mm --flows raw prop rec_z0 --rep 1 --device cuda:N
"""
import argparse

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.data import embed_annotations
from holo_openset.evaluate import IDX, calibrate, nn_scores, open_set_metrics
from holo_openset.flows import dataset, weights_of
from holo_openset.model import load_model, pick_device
from holo_openset.protocol import classes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--set', default='bench_1mm')
    ap.add_argument('--flows', nargs='+', default=['raw', 'prop', 'rec_z0'])
    ap.add_argument('--rep', type=int, default=1)
    ap.add_argument('--device', default='cpu')
    a = ap.parse_args()
    torch.set_num_threads(4)
    dev = pick_device(a.device)
    rows = []
    for flow in a.flows:
        ds = dataset(flow, paths.dataset(a.set))
        ann = ds.ann
        val = np.where((ann.split == 'val').to_numpy())[0]
        model = load_model(paths.weights(weights_of(flow), a.rep, a.set), dev)[0]
        emb = np.zeros((len(ann), 128), np.float32)
        emb[val] = embed_annotations(model, ds, ann.iloc[val])
        labels = ann.classe.map(IDX).to_numpy()
        files = ann.filename.to_numpy()
        seen_idx = [IDX[c] for c in classes(a.rep)[0]]
        val_seen = val[np.isin(labels[val], seen_idx)]
        t, cal_auroc = calibrate(emb, labels, val_seen, files, seen_idx)
        # the folds of evaluate.calibrate, again
        rng = np.random.RandomState(0)
        cl = np.array(sorted(seen_idx))
        rng.shuffle(cl)
        vfiles = np.array(sorted(set(files[val_seen])))
        is_gal = np.isin(files[val_seen], vfiles[::2])
        for k, held in enumerate(np.array_split(cl, 4)):
            gi = val_seen[is_gal & ~np.isin(labels[val_seen], held)]
            qi = val_seen[~is_gal]
            p, s = nn_scores(emb[qi], emb[gi], labels[gi])
            m = open_set_metrics(p, s, labels[qi], ~np.isin(labels[qi], held), t)
            rows.append(dict(set=a.set, flow=flow, rep=a.rep, fold=k, threshold=t, cal_auroc=cal_auroc,
                             n_queries=len(qi), **{f'val_{x}': v for x, v in m.items()}))
        print(flow, pd.DataFrame(rows[-4:]).filter(like='val_').mean().round(4).to_dict(), flush=True)
    t = pd.DataFrame(rows)
    mean = t.groupby(['set', 'flow', 'rep'], sort=False).mean(numeric_only=True).reset_index().assign(fold='mean')
    out = pd.concat([t, mean], ignore_index=True)
    d = paths.RESULTS / 'eval' / a.set
    d.mkdir(parents=True, exist_ok=True)
    out.to_csv(d / f'val_openset_r{a.rep}.csv', index=False, float_format='%.5g')
    print(mean.to_string(index=False))


if __name__ == '__main__':
    main()
