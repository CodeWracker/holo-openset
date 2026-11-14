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
"""
import numpy as np
import pandas as pd

from holo_openset import paths
from holo_openset.data import embed_annotations
from holo_openset.evaluate import IDX, nn_scores
from holo_openset.experiments.common import KEEP, device, fmt, model, parser, save, strict
from holo_openset.flows import PAPER_FLOWS, array_name, dataset
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
    a = ap.parse_args(argv)
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
            for v in a.variants:
                root = broot if v == 'base' else paths.dataset(f'{a.variants_root}/{v}')
                if not (root / array_name(flow)).exists():
                    print('missing', root / array_name(flow), flush=True)
                    continue
                vann = pd.read_csv(root / 'annotations.csv')
                vtest = vann[vann.split == 'test'].reset_index(drop=True)
                assert (vtest[['image_id', 'x0', 'y0', 'x1', 'y1', 'classe']].values ==
                        ref[['image_id', 'x0', 'y0', 'x1', 'y1', 'classe']].values).all(), f'{v}: not the same scenes'
                emb = np.zeros((len(ann), 128), np.float32)
                emb[val] = emb_val
                emb[test] = embed_annotations(m, dataset(flow, root, ann=vann), ref)
                res = strict(m, base, r, emb)
                effect, value, _ = ALL.get(v, ('base', 'base', {}))
                rows.append(dict(rep=r, variant=v, effect=effect, value=value, flow=name,
                                 **{k: res[k] for k in KEEP if k in res}))
                print(fmt(rows[-1]), flush=True)
                if a.by_session:
                    srows += [dict(rep=r, variant=v, flow=name, threshold=res['threshold'], **x)
                              for x in sessions(emb, ann, r, res['threshold'], session_of)]
        save(rows, a.out, keys=['rep', 'variant', 'flow'])
        if srows:
            save(srows, f'{a.out}_sessions', keys=['rep', 'variant', 'flow', 'session'])
