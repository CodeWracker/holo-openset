"""Strict open-set evaluation (the protocol of the paper).

For repetition r (21 seen classes, 5 unseen):
  * threshold: calibrated on the VALIDATION split with SEEN classes only (4 folds of held-out seen classes; gallery =
    even-indexed val images, queries = odd-indexed); t = 5 % quantile of the genuine scores (FRR 5 %).
  * novel : gallery = val crops of seen classes, queries = all test crops. Unseen queries must be rejected.
  * world : 3 unseen classes enrolled from their val crops (no retraining, k = 5, 20 or all examples per class);
            the remaining 2 unseen classes must still be rejected. Decisions use per-class thresholds
            t_c = min(t, own genuine-score quantile) -- see gallery.py.
Metrics: AUROC known/unknown, OSCR, known accuracy and unknown rejection at the threshold, open-set macro-F1
(classes + 'unknown'), accuracy on the newly enrolled unseen classes.
"""
import numpy as np
from sklearn.metrics import roc_auc_score

from holo_openset.data import CLASSES, embed_annotations

IDX = {c: i for i, c in enumerate(CLASSES)}


def nn_scores(q, g, gl):
    s = q @ g.T
    return gl[s.argmax(1)], s.max(1)


def calibrate(emb, labels, val_idx, files, seen_idx, n_folds=4, frr=0.05, seed=0):
    rng = np.random.RandomState(seed)
    classes = np.array(sorted(seen_idx))
    rng.shuffle(classes)
    folds = np.array_split(classes, n_folds)
    vfiles = np.array(sorted(set(files[val_idx])))
    is_gal = np.isin(files[val_idx], vfiles[::2])
    gen, imp = [], []
    for held in folds:
        gi = val_idx[is_gal & ~np.isin(labels[val_idx], held)]
        qi = val_idx[~is_gal]
        _, s = nn_scores(emb[qi], emb[gi], labels[gi])
        unk = np.isin(labels[qi], held)
        gen.append(s[~unk])
        imp.append(s[unk])
    gen, imp = np.concatenate(gen), np.concatenate(imp)
    auroc = roc_auc_score(np.r_[np.ones(len(gen)), np.zeros(len(imp))], np.r_[gen, imp])
    return float(np.quantile(gen, frr)), float(auroc)


def oscr(pred, score, true, known):
    sk, su, correct = score[known], score[~known], (pred == true)[known]
    thr = np.sort(np.unique(np.r_[sk, su]))[::-1]
    thr = thr[::max(1, len(thr) // 2000)]
    ccr = np.r_[0, [((sk >= t) & correct).mean() for t in thr], correct.mean()]
    fpr = np.r_[0, [(su >= t).mean() for t in thr], 1]
    return float(np.trapz(ccr, fpr))


def open_set_metrics(pred, score, true, known, t):
    yp = np.where(score >= t, pred, -1)
    yt = np.where(known, true, -1)
    f1 = [2 * ((yp == c) & (yt == c)).sum() / max(2 * ((yp == c) & (yt == c)).sum() + ((yp == c) & (yt != c)).sum()
                                                  + ((yp != c) & (yt == c)).sum(), 1) for c in np.unique(np.r_[yp, yt])]
    return dict(auroc=float(roc_auc_score(known.astype(int), score)), oscr=oscr(pred, score, true, known),
                known_acc=float(((pred == true) & (score >= t))[known].mean()),
                unknown_rejection=float((score < t)[~known].mean()), open_macro_f1=float(np.mean(f1)),
                closed_acc=float((pred == true)[known].mean()))


def evaluate(model, dataset, rep, buffer=0.25, frr=0.05, emb=None):
    """emb: optional precomputed embeddings [len(dataset.ann), 128] (val and test rows are used); model is then unused."""
    ann = dataset.ann
    seen, unseen = dataset.classes(rep)
    labels = ann.classe.map(IDX).to_numpy()
    split, files = ann.split.to_numpy(), ann.filename.to_numpy()
    vt = np.where(np.isin(split, ['val', 'test']))[0]
    if emb is None:
        emb = np.zeros((len(ann), 128), np.float32)
        emb[vt] = embed_annotations(model, dataset, ann.iloc[vt], buffer)
    seen_idx = [IDX[c] for c in seen]
    is_seen = np.isin(labels, seen_idx)
    val_seen = np.where((split == 'val') & is_seen)[0]
    t, cal_auroc = calibrate(emb, labels, val_seen, files, seen_idx, frr=frr)
    q = np.where(split == 'test')[0]
    p, s = nn_scores(emb[q], emb[val_seen], labels[val_seen])
    out = {'rep': rep, 'threshold': t, 'cal_auroc': cal_auroc}
    out.update({f'novel_{k}': v for k, v in open_set_metrics(p, s, labels[q], is_seen[q], t).items()})
    imgs = ann.image_id.to_numpy()
    enr, absent = [IDX[c] for c in unseen[:3]], [IDX[c] for c in unseen[3:]]
    rng = np.random.RandomState(0)
    for shots in (5, 20, 0):
        new = []
        for c in enr:
            ci = np.where((split == 'val') & (labels == c))[0]
            new.append(ci if shots == 0 else rng.choice(ci, min(shots, len(ci)), replace=False))
        gal = np.r_[val_seen, np.concatenate(new)]
        tc = {}
        for c in np.unique(labels[gal]):
            ci = gal[labels[gal] == c]
            sc = emb[ci] @ emb[ci].T
            sc[imgs[ci][:, None] == imgs[ci][None, :]] = -2
            g = sc.max(1)
            g = g[g > -2]
            tc[c] = min(t, float(np.quantile(g, frr))) if len(g) else t
        p, s = nn_scores(emb[q], emb[gal], labels[gal])
        acc = s >= np.array([tc[x] for x in p])
        lq = labels[q]
        k = 'all' if shots == 0 else shots
        out[f'world{k}_seen_acc'] = float(((p == lq) & acc)[np.isin(lq, seen_idx)].mean())
        out[f'world{k}_new_class_acc'] = float(((p == lq) & acc)[np.isin(lq, enr)].mean())
        out[f'world{k}_new_class_rank1'] = float((p == lq)[np.isin(lq, enr)].mean())
        out[f'world{k}_absent_rejection'] = float((~acc)[np.isin(lq, absent)].mean())
    return out
