"""The search of the distance on its own (docs/exp_distancia): how far each way of focusing lands from the true distance
of each hologram. No class label is used, and the candidates only ever meet the VALIDATION split.

  sweep    every candidate search of GRID (range and candidates x binning x sharpness) on every validation hologram of
           the given sets -> logs/focus_sweep/<set>.npz (the distance each candidate found on each image) and
           results/focus_sweep.csv (per candidate and set: median, 90th percentile and gross failures of the error,
           reconstructions, cost in whole-image reconstructions, measured time)
  select   the rules written down before the sweep, applied to focus_sweep.csv -> results/focus_selection.json
  policy   when to focus, on validation: once per session on its first k images (k = 1 or 3), from the distances the
           blind search found in the sweep; and every M images of a drifting session, by the accuracy on the SEEN
           classes of the validation split with the models and the threshold of the base set
           -> results/focus_policy.csv
  error    after the choices are frozen: the logs autofocus*.csv of sets already reconstructed, per set and method and
           per session -> results/focus_error.csv, focus_error_sessions.csv

    python -m holo_openset experiment focus sweep --device cuda:N [--sets ...] [--stride 1]
    python -m holo_openset experiment focus select
    python -m holo_openset experiment focus policy --device cuda:N
    python -m holo_openset experiment focus error --sets variants/session_5 ... --methods af afs ...
"""
import argparse
import itertools
import json
import time

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.experiments.common import device, model, save
from holo_openset.reconstruct import BLIND, FOCUS, Focus, Holograms, autofocus, backprop, channels
from holo_openset.sim.physics import Z0

# ------------------------------------------------------------------------------------------------ the candidates
SEARCH = {   # name -> lo, hi (units of z0), coarse candidates, fine candidates
    'blind': (None, None, 73, 41),      # the paper: 0.2-2.1 z0
    'r30': (0.70, 1.30, 31, 21),
    'r20': (0.80, 1.20, 21, 21),
    'r15a': (0.85, 1.15, 15, 11),       # the example of the protocol
    'r15b': (0.85, 1.15, 15, 21),
    'r15c': (0.85, 1.15, 9, 15),
    'r10a': (0.90, 1.10, 11, 11),
    'r10b': (0.90, 1.10, 7, 11),
}
BINS = (1, 2, 4, 8)
CRITERIA = {  # name -> mask (fraction of the maximum of the blank frame), fill, sigma (sensor pixels)
    'tog': (0.0, False, 0.0),           # the paper
    's1': (0.0, False, 1.0),
    's2': (0.0, False, 2.0),
    'm': (0.2, False, 0.0),
    'mf': (0.2, True, 0.0),
    'ms': (0.2, False, 1.5),
    'mfs': (0.2, True, 1.5),
    'mfs2': (0.2, True, 2.0),
}
GRID = {f'{s}-b{b}-{c}': Focus(lo=lo, hi=hi, n_coarse=nc, n_fine=nf, bin=b, mask=mk, fill=fl, sigma=sg)
        for (s, (lo, hi, nc, nf)), b, (c, (mk, fl, sg)) in itertools.product(SEARCH.items(), BINS, CRITERIA.items())}
REFERENCE = 'blind-b1-tog'
assert GRID[REFERENCE] == BLIND

VAL_SETS = ['realistic', 'variants_val/frame_5', 'variants_val/fullwell_500', 'variants_val/beam_narrow']
CLEAN = ['realistic', 'variants_val/frame_5']                      # the bench, and a distance that moves per image
NOISY = ['variants_val/fullwell_500', 'variants_val/beam_narrow']  # where the sharpness of the paper is misled
GROSS = 0.01      # an error above 1 % of z0 (about 190 um, six depths of field) counts as a gross failure
MEDIAN_UM = 50.0  # the median error of the blind search of the paper


def val_ids(root):
    meta = pd.read_csv(paths.dataset(root) / 'metadata.csv')
    return meta[meta.split == 'val'].image_id.to_numpy()


def summary(z, true_z, z0=Z0):
    e = np.abs(np.asarray(z) - np.asarray(true_z))
    return dict(n=int(len(e)), median_um=float(np.median(e) * 1e6), p90_um=float(np.quantile(e, 0.9) * 1e6),
                max_um=float(e.max() * 1e6), gross=float((e > GROSS * z0).mean()))


# ------------------------------------------------------------------------------------------------ sweep
def sweep(a):
    dev = device(a)
    out_dir = paths.LOGS / 'focus_sweep'
    out_dir.mkdir(parents=True, exist_ok=True)
    names = a.candidates or list(GRID)
    for root in a.sets:
        src = Holograms(paths.dataset(root))
        ids = val_ids(root)[::a.stride]
        if not len(ids):
            raise SystemExit(f'{root} has no validation images: the sweep only runs on the validation split')
        f = out_dir / f"{root.replace('/', '__')}.npz"
        z = np.full((len(names), len(ids)), np.nan)
        sec = np.zeros(len(names))
        if f.exists():   # resume
            old = np.load(f, allow_pickle=True)
            if list(old['names']) == names and np.array_equal(old['ids'], ids):
                z, sec = old['z'], old['seconds']
        todo = np.where(~np.isfinite(z).all(0))[0]
        print(root, len(ids), 'images,', len(todo), 'to do,', len(names), 'candidates', flush=True)
        for n, k in enumerate(todo):
            i = int(ids[k])
            amp, bg = src.amplitude(i, dev), src.blank(i, dev)
            for c, name in enumerate(names):
                if dev.type == 'cuda':
                    torch.cuda.synchronize(dev)
                t0 = time.perf_counter()
                z[c, k] = autofocus(amp, src.z0, GRID[name], bg)[0]
                if dev.type == 'cuda':
                    torch.cuda.synchronize(dev)
                sec[c] += time.perf_counter() - t0
            if n % 25 == 24 or n == len(todo) - 1:
                np.savez(f, names=np.array(names), ids=ids, z=z, seconds=sec,
                         true_z=np.array([src.true_z[int(j)] for j in ids]))
                print(f'{root} {n + 1}/{len(todo)}', flush=True)
        true_z = np.array([src.true_z[int(j)] for j in ids])
        rows = [dict(set=root, candidate=name, search=name.split('-')[0], bin=GRID[name].bin,
                     criterion=name.split('-')[2], reconstructions=GRID[name].n, cost=GRID[name].cost,
                     ms=1e3 * sec[c] / len(ids), **summary(z[c], true_z, src.z0))
                for c, name in enumerate(names)]
        save(rows, 'focus_sweep', keys=['set', 'candidate'])


# ------------------------------------------------------------------------------------------------ select
def select(a):
    """The three searches that go to the test split, by the rules written in the notebook before the sweep:
    cheap     the cheapest candidate (whole-image reconstructions per search; ties: the smaller worst 90th percentile)
              whose median error is at most 50 um and whose gross failures are at most those of the blind search plus
              one point, on the bench and on the distance that moves per image;
    robust    among the candidates that satisfy the same condition and cost no more than the blind search, the one
              with the fewest gross failures on the worse of the two noisy sets (ties within half a point: the smaller
              worst 90th percentile, then the cheaper);
    both      the cheapest candidate that satisfies the condition and whose gross failures on each noisy set are at
              most those of `robust` plus one point."""
    d = pd.read_csv(paths.RESULTS / 'focus_sweep.csv')
    missing = [s for s in CLEAN + NOISY if s not in set(d.set)]
    if missing:
        raise SystemExit(f'the sweep has not run on {missing}')
    g = d.pivot(index='candidate', columns='set', values='gross')
    med = d.pivot(index='candidate', columns='set', values='median_um')
    p90 = d.pivot(index='candidate', columns='set', values='p90_um')
    cost = d.groupby('candidate').cost.first()
    ok = pd.Series(True, index=g.index)
    for s in CLEAN:
        ok &= (med[s] <= MEDIAN_UM) & (g[s] <= g.loc[REFERENCE, s] + 0.01)
    t = pd.DataFrame(dict(cost=cost, ok=ok, clean_p90=p90[CLEAN].max(1), noisy_gross=g[NOISY].max(1),
                          noisy_p90=p90[NOISY].max(1)))
    cand = t[t.ok]
    if not len(cand):
        raise SystemExit('no candidate finds the distance on the clean sets')
    cheap = cand.sort_values(['cost', 'clean_p90']).index[0]
    r = cand[cand.cost <= cost[REFERENCE]]
    r = r[r.noisy_gross <= r.noisy_gross.min() + 0.005].sort_values(['noisy_p90', 'cost'])
    robust = r.index[0]
    b = cand[(g.loc[cand.index, NOISY] <= g.loc[robust, NOISY] + 0.01).all(1)].sort_values(['cost', 'clean_p90'])
    both = b.index[0] if len(b) else None
    out = dict(reference=REFERENCE, cheap=cheap, robust=robust, both=both, candidates_ok=int(ok.sum()),
               candidates=len(t))
    for k in ['reference', 'cheap', 'robust', 'both']:
        name = out[k]
        if name:
            out[f'{k}_focus'] = {f: getattr(GRID[name], f) for f in ['lo', 'hi', 'n_coarse', 'n_fine', 'bin', 'mask',
                                                                      'fill', 'sigma']}
            out[f'{k}_cost'] = float(cost[name])
            out[f'{k}_stats'] = d[d.candidate == name].set_index('set')[['median_um', 'p90_um', 'gross']].to_dict('index')
    json.dump(out, open(paths.RESULTS / 'focus_selection.json', 'w'), indent=1)
    print(json.dumps(out, indent=1))


# ------------------------------------------------------------------------------------------------ policy
class MemImages:
    def __init__(self, imgs):
        self.imgs = imgs

    def image(self, i):
        return self.imgs[int(i)]

    def images(self, ids):
        return torch.from_numpy(np.stack([self.imgs[int(i)] for i in ids]))


class SeenValidation:
    """Accuracy on the seen classes of the validation split, as the calibration of the strict protocol splits it: the
    gallery is the patterns of every other validation image of the BASE set (reconstructed at the distance of the
    blind search, the cache rec_af), the queries are the patterns of the remaining images, here taken from another
    recording of the same scenes and reconstructed at given distances. Model and threshold are those of the base set.
    No unseen class and no test image is touched."""

    def __init__(self, rep, dev, flow='rec_af'):
        from holo_openset.data import embed_annotations
        from holo_openset.evaluate import IDX, calibrate
        from holo_openset.flows import dataset
        from holo_openset.protocol import classes
        self.dev, self.m, self.embed = dev, model(flow, rep, dev), embed_annotations
        base = dataset(flow)
        ann = self.ann = base.ann
        seen = [IDX[c] for c in classes(rep)[0]]
        self.labels = ann.classe.map(IDX).to_numpy()
        files = ann.filename.to_numpy()
        val = np.where((ann.split == 'val').to_numpy() & np.isin(self.labels, seen))[0]
        emb = np.zeros((len(ann), 128), np.float32)
        emb[val] = embed_annotations(self.m, base, ann.iloc[val])
        self.t, _ = calibrate(emb, self.labels, val, files, seen)
        even = np.isin(files[val], np.array(sorted(set(files[val])))[::2])
        self.gal, self.qry = val[even], val[~even]
        self.emb_gal = emb[self.gal]
        self.reference = self.score(emb[self.qry])

    def score(self, emb_q):
        s = emb_q @ self.emb_gal.T
        pred, score = self.labels[self.gal][s.argmax(1)], s.max(1)
        return float(((pred == self.labels[self.qry]) & (score >= self.t)).mean())

    def __call__(self, src, z_of):
        """src: Holograms of a validation recording of the same scenes; z_of: image id -> distance."""
        rows = self.ann.iloc[self.qry]
        imgs = {int(i): channels(backprop(src.amplitude(int(i), self.dev), [z_of[int(i)]])[0]).cpu().numpy()
                for i in rows.image_id.unique()}
        return self.score(self.embed(self.m, MemImages(imgs), rows))


def reuse(ids, session, z, every, first=1):
    """The distance each image is reconstructed at when the search (whose result on every image is z) is run only on
    the first `first` images of each block (every = 0: the session; M: M images) and its median reused."""
    from holo_openset.reconstruct import focus_blocks
    found = dict(zip([int(i) for i in ids], z))
    out = {}
    for members, focused in focus_blocks(ids, session, Focus(every=every, first=first)):
        zb = float(np.median([found[i] for i in focused]))
        out.update({i: zb for i in members})
    return out


def policy(a):
    dev = device(a)
    rows = []

    def load(root, candidate=REFERENCE):
        f = paths.LOGS / 'focus_sweep' / f"{root.replace('/', '__')}.npz"
        if not f.exists():
            raise SystemExit(f'run the sweep on {root} first')
        d = np.load(f, allow_pickle=True)
        if not np.array_equal(d['ids'], val_ids(root)):
            raise SystemExit(f'the sweep of {root} did not cover every validation image')
        return d['ids'], d['z'][list(d['names']).index(candidate)], d['true_z']

    # once per session: k = 1 or 3, by the distance error (the true distance is one per session in these sets)
    for root in a.session_sets:
        src = Holograms(paths.dataset(root))
        ids, z, true_z = load(root)
        for k in (1, 3):
            zr = reuse(ids, src.session, z, 0, k)
            e = np.array([abs(zr[int(i)] - t) for i, t in zip(ids, true_z)])
            ses = np.array([src.session[int(i)] for i in ids])
            per = pd.Series(e).groupby(ses).first()
            rows.append(dict(policy=f'session, first {k}', set=root, sessions=int(per.size),
                             sessions_gross=int((per > GROSS * src.z0).sum()), **summary(list(zr.values()), true_z,
                                                                                         src.z0)))
        rows.append(dict(policy='every image', set=root, **summary(z, true_z, src.z0)))
    # every M images of a drifting session: by the accuracy on the seen classes of validation
    src = Holograms(paths.dataset(a.walk_set))
    ids, z, true_z = load(a.walk_set)
    exact = dict(zip([int(i) for i in ids], true_z))
    acc = {}
    for r in a.rep:
        ev = SeenValidation(r, dev)
        acc[('base set', r)] = ev.reference
        acc[('true distance', r)] = ev(src, exact)
        for M in [1] + a.every:
            acc[(M, r)] = ev(src, reuse(ids, src.session, z, M))
        acc[(0, r)] = ev(src, reuse(ids, src.session, z, 0))
        print(r, {k[0]: round(v, 4) for k, v in acc.items() if k[1] == r}, flush=True)
    for key in ['base set', 'true distance', 1] + a.every + [0]:
        v = [acc[(key, r)] for r in a.rep]
        label = {1: 'every image', 0: 'session, first 1'}.get(key, f'every {key}' if isinstance(key, int) else key)
        zr = None if isinstance(key, str) else reuse(ids, src.session, z, key)
        rows.append(dict(policy=label, set=a.walk_set, val_known_acc=float(np.mean(v)), val_known_acc_std=float(np.std(v, ddof=1))
                         if len(v) > 1 else np.nan, reps=len(v),
                         **(summary([zr[int(i)] for i in ids], true_z, src.z0) if zr else {})))
    save(rows, 'focus_policy', keys=['policy', 'set'])
    print(pd.DataFrame(rows).to_string())


# ------------------------------------------------------------------------------------------------ error
def error(a):
    rows, srows = [], []
    for root in a.sets:
        d = paths.dataset(root)
        meta = pd.read_csv(d / 'metadata.csv').set_index('image_id')
        z0 = json.load(open(d / 'physics.json'))['physics'].get('z0', Z0)
        for m in a.methods:
            f = d / ('autofocus.csv' if m == 'af' else f'autofocus_{m}.csv')
            if not f.exists():
                print('missing', f, flush=True)
                continue
            t = pd.read_csv(f)
            if a.split:
                t = t[t.image_id.map(meta.split) == a.split]
            ses = t.image_id.map(meta.session)
            rows.append(dict(set=root, method=m, reconstructions_per_image=float(t.n_reconstructions.mean()),
                             **summary(t.z_af, t.true_z, z0)))
            for s, g in t.groupby(ses):
                srows.append(dict(set=root, method=m, session=int(s), true_z_mean=float(g.true_z.mean()),
                                  **summary(g.z_af, g.true_z, z0)))
    save(rows, 'focus_error', keys=['set', 'method'])
    save(srows, 'focus_error_sessions', keys=['set', 'method', 'session'])
    print(pd.DataFrame(rows).to_string())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('what', choices=['sweep', 'select', 'policy', 'error'])
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--rep', type=int, nargs='+', default=[1, 2, 3, 4, 5])
    ap.add_argument('--sets', nargs='+', default=VAL_SETS)
    ap.add_argument('--stride', type=int, default=1, help='sweep: every n-th validation image')
    ap.add_argument('--candidates', nargs='+', default=None, help='sweep: only these candidates of GRID (default: all)')
    ap.add_argument('--session-sets', nargs='+', default=['realistic', 'variants_val/session_5',
                                                          'variants_val/fullwell_500', 'variants_val/beam_narrow'])
    ap.add_argument('--walk-set', default='variants_val/walk_05')
    ap.add_argument('--every', type=int, nargs='+', default=[2, 5, 10, 20, 50], help='policy: candidates of M')
    ap.add_argument('--methods', nargs='+', default=['af'] + list(FOCUS))
    ap.add_argument('--split', default=None, help='error: only the images of this split of the set')
    a = ap.parse_args(argv)
    {'sweep': sweep, 'select': select, 'policy': policy, 'error': error}[a.what](a)
