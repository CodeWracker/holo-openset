"""frame_5 against session_5 (docs/exp_distancia/CADERNO.md, entry "A1 (pré-registro)"): the same nominal
distribution of the distance (5 %), drawn per image in frame_5 (800 draws) and per session in session_5 (8 draws).

Two steps, from the root of the repository after source scripts/exp_distancia/env.sh:

    python scripts/exp_distancia/frame_vs_session.py embed --device cuda:0
        Embeddings exactly as experiments/robustness.py builds them (model, gallery and threshold of the base set,
        ground-truth boxes): for every repetition, flow and set, the nearest-neighbour class and score of each test
        query (evaluate.nn_scores against the seen classes of the base validation split) and the threshold of the
        strict protocol (experiments.common.strict) -> results_exp_distancia/frame_vs_session_scores.npz
    python scripts/exp_distancia/frame_vs_session.py analyse
        Metrics of subsets of the test queries with evaluate.open_set_metrics (the metric of the paper, called on the
        subset): the whole split (checked against robustness.csv), each session, and in frame_5 each bin of the
        distance of the image from z0 -> results_exp_distancia/frame_vs_session.csv. Then the prediction of
        session_5 from the response of frame_5 (100 images per session drawn from the frame_5 images of the bin of
        that session) and the Monte Carlo of 8 sessions drawn from N(0, 5 %) -> frame_vs_session_mc.csv.
"""
import argparse
import functools
import sys

import numpy as np
import pandas as pd

from holo_openset import paths
from holo_openset.evaluate import IDX, nn_scores, open_set_metrics
from holo_openset.sim.physics import Z0

FLOWS = ['rec_z0', 'prop', 'bank_jit', 'rec_af', 'rec_afc']
SETS = ['base', 'session_5', 'frame_5']
EDGES = [0, 1, 2, 3, 4, 6, 8, 10, 12, np.inf]          # % of |z / z0 - 1|, fixed in the pre-registration
METRICS = ['known_acc', 'unknown_rejection', 'open_macro_f1', 'auroc']
SEED_PRED, SEED_MC, N_PRED, N_MC, SIGMA = 20261114, 20261115, 200, 1000, 0.05
SCORES = paths.RESULTS / 'frame_vs_session_scores.npz'


def root_of(v):
    return paths.dataset(paths.BASE if v == 'base' else f'variants/{v}')


def embed(a):
    """The loop of experiments/robustness.main, keeping the per-query nearest class and score."""
    from holo_openset.data import embed_annotations
    from holo_openset.experiments.common import device, model, strict
    from holo_openset.flows import array_name, dataset
    from holo_openset.protocol import classes
    dev = device(a)
    base = dataset('raw')
    ann = base.ann
    val, test = (ann.split == 'val').to_numpy(), (ann.split == 'test').to_numpy()
    ref = ann[test].reset_index(drop=True)
    labels = ann.classe.map(IDX).to_numpy()
    out, checks = {}, []
    for r in a.rep:
        seen = [IDX[c] for c in classes(r)[0]]
        gal = np.where(val & np.isin(labels, seen))[0]
        for flow in a.flows:
            m = model(flow, r, dev)
            emb_val = embed_annotations(m, dataset(flow), ann[val])
            for v in a.sets:
                root = root_of(v)
                assert (root / array_name(flow)).exists(), root / array_name(flow)
                vann = pd.read_csv(root / 'annotations.csv')
                vtest = vann[vann.split == 'test'].reset_index(drop=True)
                cols = ['image_id', 'x0', 'y0', 'x1', 'y1', 'classe']
                assert (vtest[cols].values == ref[cols].values).all(), f'{v}: not the same scenes'
                emb = np.zeros((len(ann), 128), np.float32)
                emb[val] = emb_val
                emb[test] = embed_annotations(m, dataset(flow, root, ann=vann), ref)
                res = strict(m, base, r, emb)
                pred, score = nn_scores(emb[test], emb[gal], labels[gal])
                key = f'r{r}/{flow}/{v}'
                out[key + '/pred'] = pred.astype(np.int16)
                out[key + '/score'] = score.astype(np.float32)
                out[key + '/threshold'] = np.float64(res['threshold'])
                checks.append(dict(rep=r, flow=flow, variant=v, threshold=res['threshold'],
                                   novel_open_macro_f1=res['novel_open_macro_f1'],
                                   novel_known_acc=res['novel_known_acc']))
                print(checks[-1], flush=True)
    out['image_id'] = ref.image_id.to_numpy()
    out['labels'] = ref.classe.map(IDX).to_numpy().astype(np.int16)
    out['seen'] = np.array([[IDX[c] for c in classes(r)[0]] for r in range(1, 6)], np.int16)  # row r - 1
    np.savez_compressed(SCORES, **out)
    print('wrote', SCORES)


def metrics(pred, score, true, known, t):
    """open_set_metrics on a subset; NaN when the subset has no unseen (or no seen) query (AUROC undefined)."""
    if known.all() or not known.any():
        return {k: np.nan for k in METRICS}
    m = open_set_metrics(pred, score, true, known, t)
    return {k: m[k] for k in METRICS}


class Scores:
    def __init__(self):
        z = np.load(SCORES)
        self.z = z
        self.image_id, self.labels, self.seen = z['image_id'], z['labels'].astype(int), z['seen']
        self.qidx = pd.Series(np.arange(len(self.image_id))).groupby(self.image_id).apply(np.asarray).to_dict()

    def get(self, r, flow, v):
        k = f'r{r}/{flow}/{v}'
        known = np.isin(self.labels, self.seen[r - 1])
        return self.z[k + '/pred'].astype(int), self.z[k + '/score'], known, float(self.z[k + '/threshold'])


@functools.lru_cache(None)
def images(v):
    m = pd.read_csv(root_of(v) / 'metadata.csv')
    m = m[m.split == 'test'].copy()
    m['dz'] = m.z / Z0 - 1
    return m.set_index('image_id')


def bin_abs(dz):
    return np.asarray(pd.cut(np.abs(np.asarray(dz)) * 100, EDGES, right=False).astype(str))


def bin_signed(dz):
    return np.char.add(np.where(dz < 0, '-', '+'), bin_abs(dz).astype(str))


def table(S, a):
    rows = []
    for v in a.sets:
        meta = images(v)
        dz_q = meta.dz.reindex(S.image_id).to_numpy()
        groups = [('all', np.full(len(dz_q), 'all'))]
        groups.append(('session', meta.session.reindex(S.image_id).astype(str).to_numpy()))
        if v == 'frame_5':
            groups += [('bin_abs', bin_abs(dz_q)), ('bin_signed', bin_signed(dz_q))]
        if v == 'base':   # the same scenes grouped by the bin they have in frame_5: how hard those images are anyway
            dz5 = images('frame_5').dz.reindex(S.image_id).to_numpy()
            groups += [('bin_abs_of_frame_5', bin_abs(dz5)), ('bin_signed_of_frame_5', bin_signed(dz5))]
        for r in a.rep:
            for flow in a.flows:
                pred, score, known, t = S.get(r, flow, v)
                for gtype, g in groups:
                    for name in pd.unique(g):
                        sub = g == name
                        img = np.unique(S.image_id[sub])
                        d = (images('frame_5') if gtype.endswith('of_frame_5') else meta).dz.loc[img]
                        rows.append(dict(rep=r, flow=flow, variant=v, group_type=gtype, group=name,
                                         n_images=len(img), n_known=int((sub & known).sum()),
                                         n_unknown=int((sub & ~known).sum()), dz_mean=d.mean(),
                                         dz_abs_mean=d.abs().mean(), threshold=t,
                                         **metrics(pred[sub], score[sub], S.labels[sub], known[sub], t)))
    return pd.DataFrame(rows)


def check(tab):
    """The whole split must give the rows of robustness.csv, each session those of robustness_sessions.csv."""
    rob = pd.read_csv(paths.RESULTS / 'robustness.csv')
    al = tab[tab.group_type == 'all'].merge(rob, on=['rep', 'variant', 'flow'])
    worst = max((al[k] - al[f'novel_{k}']).abs().max() for k in METRICS)
    ses = pd.read_csv(paths.RESULTS / 'robustness_sessions.csv')
    se = tab[tab.group_type == 'session'].assign(session=lambda d: d.group.astype(int)).merge(
        ses, on=['rep', 'variant', 'flow', 'session'], suffixes=('', '_rob'))
    worst_s = max((se[k] - se[f'{k}_rob']).abs().max() for k in ['known_acc', 'unknown_rejection', 'threshold'])
    print(f'check: {len(al)} whole-split rows against robustness.csv, largest difference {worst:.2e}; '
          f'{len(se)} session rows against robustness_sessions.csv, largest difference {worst_s:.2e}')
    assert len(al) == len(tab[tab.group_type == 'all']) and worst < 1e-9 and worst_s < 1e-9


def pooled(S, pools, sizes, rng):
    """Query indices of a synthetic test split: sizes[j] images drawn with replacement from pools[j]."""
    img = np.concatenate([rng.choice(p, n, replace=True) for p, n in zip(pools, sizes)])
    return np.concatenate([S.qidx[i] for i in img])


def predict(S, a, dev, scheme, n, rng):
    """n synthetic session_5-like splits for the session deviations dev (one per session, 100 images each),
    from the frame_5 images of the same bin -> array [n, rep, flow, metric, 2]: the metric of the frame_5 queries
    ([..., 0]) and of the same scenes in the base set ([..., 1], the difficulty of the drawn images themselves)."""
    meta = images('frame_5')
    fn = bin_abs if scheme == 'abs' else bin_signed
    lab = fn(meta.dz.to_numpy())
    out = np.zeros((n, len(a.rep), len(a.flows), len(METRICS), 2))
    got = {(r, f, v): S.get(r, f, v) for r in a.rep for f in a.flows for v in ['frame_5', 'base']}
    for b in range(n):
        d = dev[b] if dev.ndim == 2 else dev
        pools = [meta.index.to_numpy()[lab == x] for x in fn(d)]
        assert all(len(p) for p in pools), 'empty bin'
        q = pooled(S, pools, [100] * len(d), rng)
        for i, r in enumerate(a.rep):
            for j, f in enumerate(a.flows):
                for c, v in enumerate(['frame_5', 'base']):
                    pred, score, known, t = got[(r, f, v)]
                    m = metrics(pred[q], score[q], S.labels[q], known[q], t)
                    out[b, i, j, :, c] = [m[k] for k in METRICS]
    return out


def pct(x, dist):
    return 100.0 * float(np.mean(dist <= x))


def analyse(a):
    S = Scores()
    tab = table(S, a)
    check(tab)
    tab.to_csv(paths.RESULTS / 'frame_vs_session.csv', index=False)
    print('wrote', paths.RESULTS / 'frame_vs_session.csv', len(tab))
    ses = pd.read_csv(root_of('session_5') / 'sessions.csv')
    meta5 = images('session_5')
    dev = np.array([ses.set_index('session').z[s] / Z0 - 1 for s in sorted(meta5.session.unique())])
    print('session_5 test deviations (%):', np.round(dev * 100, 3))
    g = np.random.default_rng(SEED_MC).normal(0.0, SIGMA, (a.n_mc, 8))
    z_only = dict(rms=(np.sqrt((dev ** 2).mean()), np.sqrt((g ** 2).mean(1))),
                  mean_abs=(np.abs(dev).mean(), np.abs(g).mean(1)), max_abs=(np.abs(dev).max(), np.abs(g).max(1)),
                  n_beyond_2sigma=(float((np.abs(dev) > 2 * SIGMA).sum()), (np.abs(g) > 2 * SIGMA).sum(1)))
    for k, (x, dist) in z_only.items():
        print(f'z only, {k}: actual {x:.4f}, MC mean {dist.mean():.4f}, percentile {pct(x, dist):.1f}')
    whole = tab[tab.group_type == 'all'].groupby(['variant', 'flow'])[METRICS].mean()
    rows = []
    # primary: bins of |dz| with the Monte Carlo; secondary: bins with the sign, prediction only.
    # 'paired' (added after the controls rec_af / rec_afc came out low in the dry run): the damage on the drawn
    # scenes, frame_5 minus the same scenes in the base set, added to the base value of the whole split.
    for scheme, n_mc in [('abs', a.n_mc), ('signed', 0)]:
        p = predict(S, a, dev, scheme, a.n_pred, np.random.default_rng(SEED_PRED)).mean(1)    # mean over reps
        mc = predict(S, a, g, scheme, n_mc, np.random.default_rng(SEED_MC + 1)).mean(1) if n_mc else None
        for j, f in enumerate(a.flows):
            for k, met in enumerate(METRICS):
                meas, base = whole.loc[('session_5', f), met], whole.loc[('base', f), met]
                pd_, pp = p[:, j, k, 0], base + p[:, j, k, 0] - p[:, j, k, 1]
                row = dict(scheme=scheme, flow=f, metric=met, base=base, frame_5=whole.loc[('frame_5', f), met],
                           session_5=meas, pred_actual=pd_.mean(), pred_actual_lo=np.quantile(pd_, 0.025),
                           pred_actual_hi=np.quantile(pd_, 0.975), pred_actual_paired=pp.mean(),
                           pred_actual_paired_lo=np.quantile(pp, 0.025), pred_actual_paired_hi=np.quantile(pp, 0.975))
                if mc is not None:
                    d, dp = mc[:, j, k, 0], base + mc[:, j, k, 0] - mc[:, j, k, 1]
                    row |= dict(mc_mean=d.mean(), mc_sd=d.std(ddof=1), mc_p05=np.quantile(d, 0.05),
                                mc_p50=np.quantile(d, 0.5), mc_p95=np.quantile(d, 0.95),
                                pct_pred_actual=pct(row['pred_actual'], d), pct_session_5=pct(meas, d),
                                mc_paired_mean=dp.mean(), mc_paired_sd=dp.std(ddof=1),
                                mc_paired_p05=np.quantile(dp, 0.05), mc_paired_p50=np.quantile(dp, 0.5),
                                mc_paired_p95=np.quantile(dp, 0.95),
                                pct_pred_actual_paired=pct(row['pred_actual_paired'], dp),
                                pct_session_5_paired=pct(meas, dp))
                rows.append(row)
    for k, (x, dist) in z_only.items():
        rows.append(dict(scheme='z only', flow='', metric=k, session_5=x, mc_mean=dist.mean(), mc_sd=dist.std(ddof=1),
                         mc_p05=np.quantile(dist, 0.05), mc_p50=np.quantile(dist, 0.5), mc_p95=np.quantile(dist, 0.95),
                         pct_session_5=pct(x, dist)))
    out = pd.DataFrame(rows)
    out.to_csv(paths.RESULTS / 'frame_vs_session_mc.csv', index=False)
    with pd.option_context('display.width', 300, 'display.max_columns', 40, 'display.max_rows', 200):
        print(out.round(4).to_string(index=False))
    print('wrote', paths.RESULTS / 'frame_vs_session_mc.csv')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('step', choices=['embed', 'analyse'])
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--rep', type=int, nargs='+', default=[1, 2, 3, 4, 5])
    ap.add_argument('--flows', nargs='+', default=FLOWS)
    ap.add_argument('--sets', nargs='+', default=SETS)
    ap.add_argument('--n-pred', type=int, default=N_PRED)
    ap.add_argument('--n-mc', type=int, default=N_MC)
    a = ap.parse_args(argv)
    embed(a) if a.step == 'embed' else analyse(a)


if __name__ == '__main__':
    sys.exit(main())
