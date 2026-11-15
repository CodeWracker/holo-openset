"""Q3-D, the stratified reading (descriptive, no new model): with the crops model of r1 of small_near_newrec and its
threshold, the acceptance of the known letters and the rejection of the unseen ones on the test split, by third of the
letter size and by whether the centre of another hologram lies within D of the letter's centre. A second pass on the
same test with the same model and threshold (CADERNO_CURVA_DENSIDADE.md, D8); it chooses nothing.

- Scores: the steps of holo_openset.evaluate.evaluate (embeddings of the val and test crops, the threshold calibrated on
  the validation split with the seen classes, nearest neighbour against the val crops of the seen classes); the
  threshold is checked against eval/<set>/raw_r1.json before anything is counted.
- Size: the larger side of the integer box (what the pipeline crops); thirds by the 1/3 and 2/3 quantiles of the test
  queries.
- Neighbour: every letter of the scene (annotated and around the window), rebuilt from its seed; the centre of a
  letter is the centre of its ink box; "near" = another letter's centre at less than D (the effective hologram
  diameter of the set, D_rms(192 k) of hologram_diameter_<set>_summary.json, px): two holograms of diameter D overlap.
  Dust is not counted.
-> $HOLO_RESULTS/<set>_strata.csv (one row per stratum: n known / unseen, acceptance of the known, known accuracy
   (correct and accepted), rejection of the unseen)
    python scripts/exp_resolucao/small_near_strata.py --set small_near_newrec --device cuda:N
"""
import argparse
import json

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.data import embed_annotations
from holo_openset.evaluate import IDX, calibrate, nn_scores
from holo_openset.flows import dataset
from holo_openset.model import load_model, pick_device
from holo_openset.sim.generate import layout_of
from holo_openset.sim.physics import physics_from_dict
from holo_openset.sim.scene import make_scene


def scene_of(i, cfg, phys, lay):
    seed = cfg['seed'] * 1_000_000 + int(i)
    while True:   # as generate._scene
        sc = make_scene(seed, phys, lay=lay)
        if sc is not None:
            return sc
        seed += 7919 * 1000003


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--set', default='small_near_newrec')
    ap.add_argument('--rep', type=int, default=1)
    ap.add_argument('--device', default='cpu')
    a = ap.parse_args()
    torch.set_num_threads(4)
    dev = pick_device(a.device)
    root = paths.dataset(a.set)
    ds = dataset('raw', root)
    ann = ds.ann
    seen, unseen = ds.classes(a.rep)
    labels = ann.classe.map(IDX).to_numpy()
    split, files = ann.split.to_numpy(), ann.filename.to_numpy()
    vt = np.where(np.isin(split, ['val', 'test']))[0]
    model = load_model(paths.weights('raw', a.rep, a.set), dev)[0]
    emb = np.zeros((len(ann), 128), np.float32)
    emb[vt] = embed_annotations(model, ds, ann.iloc[vt], 0.25)
    seen_idx = [IDX[c] for c in seen]
    is_seen = np.isin(labels, seen_idx)
    val_seen = np.where((split == 'val') & is_seen)[0]
    t, _ = calibrate(emb, labels, val_seen, files, seen_idx)
    ref = json.load(open(paths.RESULTS / 'eval' / a.set / f'raw_r{a.rep}.json'))
    assert abs(t - ref['threshold']) < 1e-5, f'threshold {t} differs from the evaluation json {ref["threshold"]}'
    q = np.where(split == 'test')[0]
    pred, score = nn_scores(emb[q], emb[val_seen], labels[val_seen])
    known = is_seen[q]
    acc_known = float(((pred == labels[q]) & (score >= t))[known].mean())
    rej = float((score < t)[~known].mean())
    assert abs(acc_known - ref['novel_known_acc']) < 1e-9 and abs(rej - ref['novel_unknown_rejection']) < 1e-9, \
        'the pass does not reproduce the evaluation json'
    # the neighbours, from the scenes rebuilt from their seeds
    cfg = json.load(open(root / 'physics.json'))
    phys = physics_from_dict(cfg['physics'])
    lay = layout_of(cfg)
    summ = json.load(open(paths.RESULTS / f'hologram_diameter_{a.set}_summary.json'))
    D = summ['D_ef_px'][summ['axis']]
    m0 = phys.margin
    qa = ann.iloc[q].reset_index(drop=True)
    near = np.zeros(len(qa), bool)
    nearest = np.full(len(qa), np.inf)
    for i, g in qa.groupby('image_id'):
        sc = scene_of(i, cfg, phys, lay)
        cen = []
        for o in sc['objects']:
            if o['kind'] in ('letter', 'outside', 'filler'):
                f = o['factor']
                cen.append(((o['mx'] + o['master'].shape[1] / 2) / f - m0, (o['my'] + o['master'].shape[0] / 2) / f
                            - m0))
        cen = np.array(cen)
        for k, r in g.iterrows():
            c = np.array([(r.bx0 + r.bx1) / 2, (r.by0 + r.by1) / 2])
            d = np.hypot(*(cen - c).T)
            assert d.min() < 1e-6, f'image {i}: the annotated letter is not in the rebuilt scene'
            other = np.sort(d)[1] if len(d) > 1 else np.inf
            nearest[k], near[k] = other, other < D
    side = np.maximum(qa.x1 - qa.x0, qa.y1 - qa.y0).to_numpy(float)
    e1, e2 = np.quantile(side, [1 / 3, 2 / 3])
    third = np.where(side <= e1, 'small', np.where(side <= e2, 'middle', 'large'))
    correct = pred == labels[q]
    accepted = score >= t
    rows = []
    strata = [('all', np.ones(len(qa), bool))] + \
        [(f'size {s} ({lo:.0f}-{hi:.0f} px)', third == s) for s, lo, hi in
         [('small', side.min(), e1), ('middle', e1, e2), ('large', e2, side.max())]] + \
        [(f'neighbour within D ({D:.1f} px)', near), (f'no neighbour within D ({D:.1f} px)', ~near)] + \
        [(f'size {s}, {"neighbour" if n else "no neighbour"} within D', (third == s) & (near == n))
         for s in ('small', 'middle', 'large') for n in (True, False)]
    for name, m in strata:
        k, u = m & known, m & ~known
        rows.append(dict(stratum=name, n_known=int(k.sum()), n_unseen=int(u.sum()),
                         known_acceptance=float(accepted[k].mean()) if k.any() else np.nan,
                         known_accuracy=float((accepted & correct)[k].mean()) if k.any() else np.nan,
                         unseen_rejection=float((~accepted)[u].mean()) if u.any() else np.nan,
                         closed_accuracy=float(correct[k].mean()) if k.any() else np.nan))
    out = pd.DataFrame(rows)
    out.attrs = {}
    out.to_csv(paths.RESULTS / f'{a.set}_strata.csv', index=False, float_format='%.6g')
    info = dict(set=a.set, rep=a.rep, threshold=t, D_px=D, size_thirds_px=[float(e1), float(e2)],
                share_near=float(near.mean()), nearest_neighbour_px_median=float(np.median(nearest)),
                reproduces_json=dict(known_acc=acc_known, unknown_rejection=rej))
    json.dump(info, open(paths.RESULTS / f'{a.set}_strata.json', 'w'), indent=1)
    with pd.option_context('display.width', 200, 'display.max_columns', 20):
        print(out.round(4).to_string(index=False))
    print(json.dumps(info, indent=1))


if __name__ == '__main__':
    main()
