"""Open-world discovery: group the patterns rejected as 'unknown' into candidate new classes.

Clustering parameters chosen on seen classes are biased: the network was trained on them and makes them unusually
compact. They are therefore chosen with a calibration TWIN, the same network trained without 5 of the seen classes
(holo_openset.protocol.held_out_seen; python -m holo_openset train --cal), on VALIDATION data only:
  * gallery = val patterns (even images) of the twin's 16 classes, queries = val patterns (odd images) of all 21
    seen classes, rejected at a genuine-only threshold of FRR f -> calibration pool (5 pseudo-novel classes + leaks);
  * each (f, cut) of average-linkage clustering on cosine distance is scored by B-cubed F1 on that pool times the
    share of held-out patterns that reach it; the configuration with the best MEAN score over the repetitions is
    frozen.
On TEST data the final model of the repetition then rejects at FRR f against the gallery of the 21 seen classes (val
patterns) and its rejected pool is clustered with that cut; B-cubed F1 against the true classes (each pattern left
'pending' -- in a cluster smaller than 3 -- counts as its own singleton). No test or unseen data is used for a choice.

    python -m holo_openset experiment discovery --device cuda:N [--flows learned rec_z0]
Output: results/holo_openset/discovery.csv, discovery_clusters_r{r}_{flow}.csv (test pool with cluster ids)
"""
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist

from holo_openset import paths
from holo_openset.data import embed_annotations
from holo_openset.experiments.common import device, fmt, model, parser, save
from holo_openset.flows import dataset
from holo_openset.protocol import held_out_seen

FRR_GRID = [0.005, 0.01, 0.02, 0.05]
CUTS = np.round(np.arange(0.1, 1.31, 0.05), 3)
MIN_SIZE = 3


def bcubed(pred, true):
    pred, true = np.asarray(pred), np.asarray(true)
    sp, st = pred[:, None] == pred[None, :], true[:, None] == true[None, :]
    inter = (sp & st).sum(1)
    p, r = (inter / sp.sum(1)).mean(), (inter / st.sum(1)).mean()
    return float(p), float(r), float(2 * p * r / (p + r))


def cluster(emb, cut, min_size=MIN_SIZE):
    """Average linkage on cosine distance cut at `cut`; clusters smaller than min_size -> -1 (pending)."""
    if len(emb) < 2:
        return -np.ones(len(emb), int)
    lab = fcluster(linkage(pdist(emb, 'cosine'), 'average'), t=cut, criterion='distance')
    ids, cnt = np.unique(lab, return_counts=True)
    big = ids[cnt >= min_size][np.argsort(-cnt[cnt >= min_size])]
    keep = {i: n for n, i in enumerate(big)}
    return np.array([keep.get(l, -1) for l in lab])


def score(lab, true):
    return bcubed(np.where(lab < 0, -np.arange(1, len(lab) + 1), lab), true)


def threshold(emb, labels, images, frr):
    """Genuine-only threshold: even-image half as gallery, odd-image half as queries."""
    u = np.unique(images)
    even = np.isin(images, u[::2])
    q = np.where(~even)[0]
    q = q[np.isin(labels[q], labels[even])]
    s = emb[q] @ emb[even].T
    genuine = np.where(labels[q][:, None] == labels[even][None, :], s, -2).max(1)
    return float(np.quantile(genuine, frr))


def calibration_grid(twin, flow, rep):
    """Score of every (frr, cut) on the validation pool of the calibration twin of repetition rep:
    B-cubed F1 of the pool times the share of held-out patterns that reach it."""
    ds = dataset(flow)
    ann = ds.ann
    seen = ds.classes(rep)[0]
    val = ann[(ann.split == 'val') & ann.classe.isin(seen)].reset_index(drop=True)
    emb = embed_annotations(twin, ds, val)
    held = held_out_seen(rep)
    lab, img = val.classe.to_numpy(), val.image_id.to_numpy()
    u = np.unique(img)
    kept = ~np.isin(lab, held)
    gal = np.isin(img, u[::2]) & kept
    qry = ~np.isin(img, u[::2])
    rows = []
    for frr in FRR_GRID:
        t = threshold(emb[kept], lab[kept], img[kept], frr)
        s = (emb[qry] @ emb[gal].T).max(1)
        pool = np.where(qry)[0][s < t]
        reach = np.isin(lab[pool], held).sum() / max(1, (np.isin(lab, held) & qry).sum())
        for c in CUTS:
            f1 = score(cluster(emb[pool], c), lab[pool])[2] if len(pool) >= 3 else 0.0
            rows.append(dict(rep=rep, frr=frr, cut=float(c), f1=f1, reach=float(reach), score=f1 * reach))
    return rows


def run(flow, rep, dev, frr, cut, cal_score):
    final = model(flow, rep, dev)
    ds = dataset(flow)
    ann = ds.ann
    seen, unseen = ds.classes(rep)
    val = ann[(ann.split == 'val') & ann.classe.isin(seen)].reset_index(drop=True)
    test = ann[ann.split == 'test'].reset_index(drop=True)
    ev, et = embed_annotations(final, ds, val), embed_annotations(final, ds, test)
    t = threshold(ev, val.classe.to_numpy(), val.image_id.to_numpy(), frr)
    pool = np.where((et @ ev.T).max(1) < t)[0]
    lab = cluster(et[pool], cut)
    true = test.classe.to_numpy()[pool]
    p, r, f1 = score(lab, true)
    is_unseen = np.isin(true, unseen)
    out = test.iloc[pool][['image_id', 'classe', 'x0', 'y0', 'x1', 'y1']].assign(cluster=lab, unseen=is_unseen)
    out.to_csv(paths.RESULTS / f'discovery_clusters_r{rep}_{flow}.csv', index=False)
    ids = np.unique(lab[lab >= 0])
    return dict(rep=rep, flow=flow, frr=frr, cut=cut, cal_score=cal_score, pool=len(pool),
                unseen_in_pool=float(is_unseen.sum() / np.isin(test.classe, unseen).sum()),
                seen_leak=float((~is_unseen).mean()) if len(pool) else np.nan, n_clusters=len(ids),
                pending=int((lab < 0).sum()), bcubed_p=p, bcubed_r=r, bcubed_f1=f1)


def main(argv=None):
    a = parser(__doc__, ['learned', 'rec_z0']).parse_args(argv)
    dev = device(a)
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    for flow in a.flows:
        grid = []
        for r in a.rep:
            twin = model(flow, r, dev, tag='_cal')
            if twin is not None:
                grid += calibration_grid(twin, flow, r)
        grid = pd.DataFrame(grid)
        grid.assign(flow=flow).to_csv(paths.RESULTS / f'discovery_calibration_{flow}.csv', index=False)
        best = grid.groupby(['frr', 'cut']).score.mean().idxmax()   # one configuration for every repetition
        cal = float(grid.groupby(['frr', 'cut']).score.mean().max())
        print(flow, 'chosen frr, cut =', best, 'mean calibration score', round(cal, 3), flush=True)
        rows = [run(flow, r, dev, best[0], best[1], cal) for r in a.rep]
        for row in rows:
            print(fmt(row), flush=True)
        save(rows, 'discovery', keys=['rep', 'flow'])


def discover_files(a, dev):
    """CLI `discover`: predict on hologram files and cluster the patterns rejected as unknown."""
    import json
    from holo_openset.gallery import UNKNOWN, Gallery
    from holo_openset.predict import load_model_for, predict
    from holo_openset.cli import _detector, _images
    model = load_model_for(a, dev)
    gallery = Gallery.load(a.gallery)
    ds = _images(a)
    det = _detector(a, ds, dev)
    pool = []
    for p in a.images:
        _, _, dets = predict(model, a.flow, gallery, p, det, dev, with_embeddings=True)
        pool += [(p, d['box'], d['embedding']) for d in dets if d['decision'] == UNKNOWN]
    cut = a.cut if a.cut is not None else 0.6
    lab = cluster(np.array([e for _, _, e in pool]), cut, a.min_size) if pool else np.zeros(0, int)
    ids, cnt = np.unique(lab[lab >= 0], return_counts=True)
    print(f'{len(pool)} unknown patterns -> {len(ids)} candidate new classes, {(lab < 0).sum()} pending')
    report = dict(n_unknown=len(pool), cut=cut, clusters={int(i): int(c) for i, c in zip(ids, cnt)},
                  patterns=[dict(image=str(p), box=b, cluster=int(l)) for (p, b, _), l in zip(pool, lab)])
    if a.out:
        json.dump(report, open(a.out, 'w'), indent=1)
