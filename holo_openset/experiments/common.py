"""Shared pieces of the experiments."""
import argparse

import numpy as np
import pandas as pd

from holo_openset import paths
from holo_openset.evaluate import evaluate
from holo_openset.model import load_model, physical_gpu, pick_device

KEEP = ['novel_auroc', 'novel_oscr', 'novel_known_acc', 'novel_unknown_rejection', 'novel_open_macro_f1',
        'novel_closed_acc', 'world5_new_class_acc', 'world20_new_class_acc', 'worldall_new_class_acc',
        'world20_absent_rejection']


def parser(doc, flows=None):
    ap = argparse.ArgumentParser(description=doc)
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--rep', type=int, nargs='+', default=[1, 2, 3, 4, 5])
    if flows:
        ap.add_argument('--flows', nargs='+', default=flows)
    ap.add_argument('--threads', type=int, default=4)
    return ap


def device(a):
    import torch
    torch.set_num_threads(a.threads)
    dev = pick_device(a.device)
    print('device', physical_gpu() or dev, flush=True)
    return dev


def model(flow, rep, dev, train_set=paths.BASE, tag=''):
    w = paths.weights(flow, rep, train_set, tag)
    if not w.exists():
        print('missing', w, flush=True)
        return None
    return load_model(w, dev)[0]


def strict(model, ds, rep, emb):
    """The strict protocol of holo_openset.evaluate on precomputed embeddings -> dict of the KEEP metrics."""
    r = evaluate(model, ds, rep, emb=emb)
    return {k: r[k] for k in KEEP if k in r} | {'threshold': r['threshold']}


def save(rows, name, keys=None):
    """Append rows to results/holo_openset/<name>.csv, replacing older rows with the same keys."""
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    out = paths.RESULTS / f'{name}.csv'
    new = pd.DataFrame(rows)
    if out.exists() and keys:
        old = pd.read_csv(out)
        k_new = set(map(tuple, new[keys].astype(str).values))
        old = old[[tuple(v) not in k_new for v in old[keys].astype(str).values]]
        new = pd.concat([old, new], ignore_index=True)
    new.to_csv(out, index=False)
    return out


def fmt(d):
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()}


def l2_rows(x):
    x = x.reshape(len(x), -1).astype(np.float32)
    x = x - x.mean(1, keepdims=True)
    return x / (np.linalg.norm(x, axis=1, keepdims=True) + 1e-6)
