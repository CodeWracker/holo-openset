"""Robustness: every flow, trained and calibrated on the base acquisition, meets test holograms recorded with ONE effect
changed (holo_openset.sim.variants; the same scenes as the base test split, with their own blank frames and their own
reconstructions: python -m holo_openset reconstruct --set variants/<name>).

Gallery, thresholds and models stay those of the base set: the embeddings of the validation patterns come from the
base set and those of the test patterns from the variant (ground-truth boxes: this isolates the front end; the
detector on the variants is measured by the oracle experiment and by e2e on the base set). 'base' is the base test
split itself.

    python -m holo_openset experiment robustness --device cuda:N [--rep ...] [--variants ...] [--flows ...]
Output: results/holo_openset/robustness.csv

--by-session also writes robustness_sessions.csv: the accuracy on the seen classes and the rejection of the unseen
ones in each test session, at the same threshold (a distance found once per session is right or wrong for a whole
session). --own evaluates a flow of the distance study with a model trained on its own images instead of the model
it borrows (rows saved as <flow>+own).

--set, --variants-root and --out run the same experiment on another base set and its own recordings of the
variants, e.g. a set reduced b x b (holo_openset.resolution): --set realistic_b4 --variants-root variants_b4
--out robustness_b4 (models of models/<set>, test scenes of data/variants_b4/<name>).

The front end recalibrated without labels (the pilot at 1.0 mm, docs/exp_resolucao/CADERNO_PILOTO_1MM.md, P0 (b)):
--alpha-json FILE sets the alpha of the propagation layer ('prop', 'bank': the value 'alpha' of the file, written by
scripts/exp_resolucao/recalibrate_distance.py; a bank keeps its spread around it) for the TEST embeddings of the
variants (--alpha-mode literal), or scales the trained alpha by the ratio of the two calibrations of the file,
alpha / alpha_ref (--alpha-mode ratio); --rec-tag T makes the flows of a reconstruction read rec_<method>T.npy of the
variants (a cache back-propagated at the recalibrated distance: reconstruct --z0 Z --tag T). The rows of the variants
so read are named <flow><suffix> (--suffix, default +recal). The weights, the gallery (the validation split of --set,
embedded as the model was trained) and the threshold do not change.
"""
import json

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.data import Dataset, embed_annotations
from holo_openset.evaluate import IDX, nn_scores
from holo_openset.experiments.common import KEEP, device, fmt, model, parser, save, strict
from holo_openset.flows import FLOWS, PAPER_FLOWS, array_name, dataset
from holo_openset.protocol import classes
from holo_openset.sim.variants import ALL, VARIANTS


def sessions(emb, ann, rep, threshold, session_of):
    """Per test session: accepted-and-correct share of the seen-class patterns, rejected share of the unseen ones
    (gallery: the seen classes of the validation split, as in the strict protocol)."""
    seen = [IDX[c] for c in classes(rep)[0]]
    labels = ann.classe.map(IDX).to_numpy()
    split = ann.split.to_numpy()
    gal = np.where((split == 'val') & np.isin(labels, seen))[0]
    q = np.where(split == 'test')[0]
    pred, score = nn_scores(emb[q], emb[gal], labels[gal])
    known = np.isin(labels[q], seen)
    ses = ann.image_id.map(session_of).to_numpy()[q]
    out = []
    for s in np.unique(ses):
        k, u = (ses == s) & known, (ses == s) & ~known
        out.append(dict(session=int(s), n_known=int(k.sum()), n_unknown=int(u.sum()),
                        known_acc=float(((pred == labels[q]) & (score >= threshold))[k].mean()),
                        unknown_rejection=float((score < threshold)[u].mean()) if u.any() else np.nan))
    return out


def main(argv=None):
    ap = parser(__doc__, list(PAPER_FLOWS))
    ap.add_argument('--variants', nargs='+', default=['base'] + list(VARIANTS))
    ap.add_argument('--by-session', action='store_true', help='also robustness_sessions.csv')
    ap.add_argument('--own', action='store_true', help="the flow's own checkpoint instead of the one it borrows")
    ap.add_argument('--set', default=paths.BASE, help='the base set: its models, gallery and thresholds')
    ap.add_argument('--variants-root', default='variants', help='where the variants of that set are (data/<root>/<v>)')
    ap.add_argument('--out', default='robustness', help='name of the csv (and of <out>_sessions.csv)')
    ap.add_argument('--alpha-json', help="the variants' test patterns embedded with the alpha of this file (prop, bank)")
    ap.add_argument('--rec-tag', default='', help="the variants' reconstructions read from rec_<method><tag>.npy")
    ap.add_argument('--alpha-mode', default='literal', choices=['literal', 'ratio'],
                    help="literal: the file's alpha replaces the trained one; ratio: the trained one times "
                         "alpha / alpha_ref of the file")
    ap.add_argument('--suffix', default='+recal', help='name of the rows read with --alpha-json / --rec-tag')
    a = ap.parse_args(argv)
    cal = json.load(open(a.alpha_json)) if a.alpha_json else None
    alpha_new = float(cal['alpha']) if cal else None
    dev = device(a)
    broot = paths.dataset(a.set)
    base = dataset('raw', broot)
    ann = base.ann
    val, test = (ann.split == 'val').to_numpy(), (ann.split == 'test').to_numpy()
    ref = ann[test].reset_index(drop=True)
    meta = pd.read_csv(base.root / 'metadata.csv')
    session_of = dict(zip(meta.image_id, meta.session))
    for r in a.rep:
        rows, srows = [], []
        for flow in a.flows:
            m = model(flow, r, dev, train_set=a.set, own=a.own)
            if m is None:
                continue
            name = f'{flow}+own' if a.own else flow
            emb_val = embed_annotations(m, dataset(flow, broot), ann[val])
            recal = alpha_new is not None and hasattr(m.fourier, 'alpha')
            alpha_trained = m.fourier.alpha.detach().clone() if recal else None
            for v in a.variants:
                root = broot if v == 'base' else paths.dataset(f'{a.variants_root}/{v}')
                arr = array_name(flow)
                if v != 'base' and a.rec_tag and FLOWS[flow]['rec']:
                    arr = arr.replace('.npy', f'{a.rec_tag}.npy')
                if not (root / arr).exists():
                    print('missing', root / arr, flush=True)
                    continue
                vann = pd.read_csv(root / 'annotations.csv')
                vtest = vann[vann.split == 'test'].reset_index(drop=True)
                assert (vtest[['image_id', 'x0', 'y0', 'x1', 'y1', 'classe']].values ==
                        ref[['image_id', 'x0', 'y0', 'x1', 'y1', 'classe']].values).all(), f'{v}: not the same scenes'
                emb = np.zeros((len(ann), 128), np.float32)
                emb[val] = emb_val
                if recal and v != 'base':   # the propagation of the layer moved to the recalibrated distance
                    k = alpha_new / float(alpha_trained.mean()) if a.alpha_mode == 'literal' else \
                        float(cal['alpha']) / float(cal['alpha_ref'])
                    with torch.no_grad():
                        m.fourier.alpha.copy_(alpha_trained * k)
                    print(f'{flow}: alpha {float(alpha_trained.mean()):.7f} -> {float(m.fourier.alpha.mean()):.7f} '
                          f'({a.alpha_mode})', flush=True)
                emb[test] = embed_annotations(m, Dataset(root, arr, ann=vann), ref)
                if recal:
                    with torch.no_grad():
                        m.fourier.alpha.copy_(alpha_trained)
                res = strict(m, base, r, emb)
                effect, value, _ = ALL.get(v, ('base', 'base', {}) if v == 'base' else (v, v, {}))   # a set's own
                moved = v != 'base' and (recal or bool(a.rec_tag and FLOWS[flow]['rec']))
                rows.append(dict(rep=r, variant=v, effect=effect, value=value, flow=f'{name}{a.suffix}' if moved else name,
                                 **{k: res[k] for k in KEEP if k in res}))
                print(fmt(rows[-1]), flush=True)
                if a.by_session:
                    srows += [dict(rep=r, variant=v, flow=rows[-1]['flow'], threshold=res['threshold'], **x)
                              for x in sessions(emb, ann, r, res['threshold'], session_of)]
        save(rows, a.out, keys=['rep', 'variant', 'flow'])
        if srows:
            save(srows, f'{a.out}_sessions', keys=['rep', 'variant', 'flow', 'session'])
