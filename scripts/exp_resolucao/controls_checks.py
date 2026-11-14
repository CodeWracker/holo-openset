"""Checks and the table of the two controls of P2 (CADERNO_PILOTO_1MM.md; run by scripts/exp_resolucao/controls_1mm.sh).

  removed   the scenes of --ids rebuilt from their seeds with the layout of --ref plus the fillers (fill_mean, or the
            layout of --set when it exists), recorded with the FILLERS REMOVED exactly as `generate` records (same
            session, camera, noise generator, device), compared with the stored holograms of --ref (equal = the
            fillers are the only difference); and, when --set exists, recorded WITH the fillers and compared with its
            stored holograms (the set is rebuilt from its seeds) -> printed and returned
  dense     control C after recording: annotations.csv of --set against --ref (bytes and every column, all splits),
            labels/, objects/, dust.csv, sessions.csv, backgrounds.npy, metadata.csv (common columns), physics.json
            (the only difference must be fill_mean); `removed` on 2 images (the first of a train and of a test
            session); letters per 640 x 640 window (annotated + fillers, from metadata) and in the band; the area they
            cover (sum of the ink boxes and of max side^2, over 100 scenes rebuilt) against the base set (realistic,
            from its annotations) -> $HOLO_RESULTS/bench_1mm_dense_checks.json
  master    control B: the cost of the master raster of the glyphs (factor 16, 8, 4) on 4 scenes of the base_newrec
            layout (scene build time, one process) and its effect on the recording at s = 2 (noise free; rms of the
            difference to factor 16 / rms of the pattern), with the scenes compared object by object
            -> $HOLO_RESULTS/base_newrec_master.csv
  table     $HOLO_RESULTS/controls.csv: raw, prop, rec_z0 of r1 (test: novel_open_macro_f1, novel_unknown_rejection,
            novel_closed_acc, novel_known_acc, threshold) for base_newrec, bench_1mm_dense, bench_1mm (copied from
            its json) and realistic --no-aux (the like-for-like reference of B, when it exists); the paired
            differences bench_1mm_dense - bench_1mm; and the reading rules of P2 applied to the crops (raw)
            -> also $HOLO_RESULTS/controls_reading.json
"""
import argparse
import hashlib
import json
import math
import time

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.model import pick_device
from holo_openset.sim.generate import CAMERA_SEED, frame_session, layout_of, make_layout
from holo_openset.sim.physics import Physics, physics_from_dict, record, sensor_intensity
from holo_openset.sim.scene import TILE, FresnelLayout, camera, make_scene, session

FLOWS = ['raw', 'prop', 'rec_z0']
METRICS = ['novel_open_macro_f1', 'novel_unknown_rejection', 'novel_closed_acc', 'novel_known_acc', 'threshold']


def scene_of(i, cfg, phys, lay):
    seed = cfg['seed'] * 1_000_000 + int(i)
    while True:   # as generate._scene
        sc = make_scene(seed, phys, lay=lay)
        if sc is not None:
            return sc
        seed += 7919 * 1000003


def record_as_generate(sc, i, cfg, phys, cam, dev):
    """What generate() stores for image i of a set (no tilt, no drift in these sets)."""
    seed, per = cfg['seed'], cfg['per_session']
    s = int(i) // per
    ses = frame_session(session(seed * 1000 + s, phys), phys, seed * 1_000_000 + int(i))
    sc = dict(sc, sensor_dust=cam['dust'])
    g = torch.Generator(device=dev).manual_seed(seed * 1_000_000 + int(i) + 700_000_000)
    return record(sensor_intensity(sc, ses, phys, dev), ses, phys, cam, g, dev)


def removed(ref, dset, ids, dev, fill_mean=154.0):
    rroot = paths.dataset(ref)
    cfg = json.load(open(rroot / 'physics.json'))
    phys = physics_from_dict(cfg['physics'])
    droot = paths.dataset(dset) if dset else None
    if droot is not None and (droot / 'physics.json').exists():
        dcfg = json.load(open(droot / 'physics.json'))
        lay = layout_of(dcfg)
        assert physics_from_dict(dcfg['physics']) == phys
        dholo = np.load(droot / 'holograms.npy', mmap_mode='r')
    else:
        lay = make_layout(cfg['layout'], dict(cfg['layout_params'], fill_mean=fill_mean))
        dholo = None
    cam = camera(cfg.get('camera_seed', CAMERA_SEED), phys, lay)
    rholo = np.load(rroot / 'holograms.npy', mmap_mode='r')
    out = []
    for i in ids:
        sc = scene_of(i, cfg, phys, lay)
        n_fill = sum(o['kind'] == 'filler' for o in sc['objects'])
        without = dict(sc, objects=[o for o in sc['objects'] if o['kind'] != 'filler'])
        a = record_as_generate(without, i, cfg, phys, cam, dev)
        r = dict(image_id=int(i), n_letters=len(sc['rows']), n_fillers=n_fill,
                 without_fillers_equal_ref=bool(np.array_equal(a, rholo[int(i)])),
                 without_fillers_max_abs_dn=int(np.abs(a.astype(int) - rholo[int(i)].astype(int)).max()))
        if dholo is not None:
            b = record_as_generate(sc, i, cfg, phys, cam, dev)
            d = b.astype(int) - dholo[int(i)].astype(int)
            r.update(with_fillers_equal_set=bool(np.array_equal(b, dholo[int(i)])),
                     with_fillers_max_abs_dn=int(np.abs(d).max()),
                     fillers_change_rms_dn=float((b.astype(float) - a.astype(float)).std()))
        print(r, flush=True)
        out.append(r)
    return out


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ink_boxes(sc, phys, kinds):
    """Ink boxes (px, window coordinates) of the objects of `kinds` that lie in the window."""
    m0, (h, w) = phys.margin, phys.window
    out = []
    for o in sc['objects']:
        if o['kind'] not in kinds:
            continue
        f = o['factor']
        x0, y0 = o['mx'] / f - m0, o['my'] / f - m0
        x1, y1 = x0 + o['master'].shape[1] / f, y0 + o['master'].shape[0] / f
        if x0 >= 0 and y0 >= 0 and x1 <= w and y1 <= h:
            out.append((x0, y0, x1, y1))
    return np.array(out).reshape(-1, 4)


def dense(a, dev):
    root, rroot = paths.dataset(a.set), paths.dataset(a.ref)
    res = dict(set=a.set, ref=a.ref)
    # the annotations and every file that must not change
    A, R = pd.read_csv(root / 'annotations.csv'), pd.read_csv(rroot / 'annotations.csv')
    res['annotations'] = dict(bytes_equal=sha(root / 'annotations.csv') == sha(rroot / 'annotations.csv'),
                              rows=len(A), columns=list(A.columns), same_columns=list(A.columns) == list(R.columns),
                              columns_equal={c: bool(A[c].equals(R[c])) for c in R.columns},
                              splits={k: int(v) for k, v in A.split.value_counts().items()})
    for name in ['dust.csv', 'sessions.csv', 'backgrounds.npy']:
        res[name] = sha(root / name) == sha(rroot / name)
    for d in ['labels', 'objects']:
        fa = sorted(p.name for p in (root / d).iterdir())
        fr = sorted(p.name for p in (rroot / d).iterdir())
        res[d] = dict(files=len(fa), same_names=fa == fr,
                      all_equal=fa == fr and all((root / d / x).read_bytes() == (rroot / d / x).read_bytes()
                                                 for x in fa))
    M, MR = pd.read_csv(root / 'metadata.csv'), pd.read_csv(rroot / 'metadata.csv')
    res['metadata_common_columns_equal'] = bool(M[MR.columns].equals(MR))
    cfg, rcfg = json.load(open(root / 'physics.json')), json.load(open(rroot / 'physics.json'))
    diff = {k: (cfg.get(k), rcfg.get(k)) for k in set(cfg) | set(rcfg) if cfg.get(k) != rcfg.get(k)}
    lp = diff.pop('layout_params', None)
    res['physics_json_differences'] = diff
    res['layout_params_differences'] = {k: (lp[0].get(k), lp[1].get(k)) for k in set(lp[0]) | set(lp[1])
                                        if lp[0].get(k) != lp[1].get(k)} if lp else {}
    # recordings without the fillers against the reference
    first = M.groupby('session').image_id.min()
    ses_split = M.groupby('session').split.first()
    ids = [int(first[ses_split[ses_split == 'train'].index[0]]), int(first[ses_split[ses_split == 'test'].index[0]])]
    res['removed'] = removed(a.ref, a.set, ids, dev)
    # letters per window
    phys = physics_from_dict(cfg['physics'])
    lay = layout_of(cfg)
    h, w = phys.window
    H, W = phys.canvas
    m0, R_ = phys.margin, phys.reach
    band_area = (min(H, m0 + h + R_) - max(0, m0 - R_)) * (min(W, m0 + w + R_) - max(0, m0 - R_)) - h * w
    win = M.n_letters + M.n_fill_window
    band = (M.n_outside + M.n_fill_band) * TILE / band_area
    q = lambda s: dict(mean=float(s.mean()), std=float(s.std()), min=float(s.min()), p5=float(s.quantile(.05)),   # noqa
                       p50=float(s.median()), p95=float(s.quantile(.95)), max=float(s.max()))
    res['letters_per_window'] = dict(target=lay.fill_mean, annotated=q(M.n_letters), fillers=q(M.n_fill_window),
                                     total=q(win), by_split={k: float(v) for k, v in win.groupby(M.split).mean().items()})
    res['letters_in_band_per_640x640'] = dict(around_the_window=q(M.n_outside * TILE / band_area),
                                              total=q(band), band_area_px=int(band_area))
    res['fillers_skipped'] = dict(images=int((M.n_fill_skipped > 0).sum()), total=int(M.n_fill_skipped.sum()))
    # covered area: rebuild 100 scenes across the set
    pick = M.image_id.to_numpy()[np.linspace(0, len(M) - 1, a.n_cover).astype(int)]
    cov = []
    for i in pick:
        sc = scene_of(i, cfg, phys, lay)
        for kinds, name in [(('letter',), 'annotated'), (('letter', 'filler'), 'total')]:
            b = ink_boxes(sc, phys, kinds)
            side = np.maximum(b[:, 2] - b[:, 0], b[:, 3] - b[:, 1])
            cov.append(dict(image_id=int(i), which=name, n=len(b),
                            box_area=float(((b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])).sum() / (h * w)),
                            side_sq=float((side ** 2).sum() / (h * w))))
    cov = pd.DataFrame(cov)
    base = pd.read_csv(paths.dataset('realistic') / 'annotations.csv')
    bm = pd.read_csv(paths.dataset('realistic') / 'metadata.csv')
    bside = np.maximum(base.x1 - base.x0, base.y1 - base.y0)
    per = lambda v: float(v.groupby(base.image_id).sum().reindex(bm.image_id, fill_value=0).mean() / 640 ** 2)  # noqa
    res['covered_fraction'] = dict(
        definition='per image, sum over the letters in the window of the ink-box area (box_area) or of the squared '
                   'max side (side_sq), over the window area; mean over images',
        scenes_rebuilt=int(a.n_cover),
        dense_annotated=cov[cov.which == 'annotated'][['n', 'box_area', 'side_sq']].mean().to_dict(),
        dense_total=cov[cov.which == 'total'][['n', 'box_area', 'side_sq']].mean().to_dict(),
        realistic=dict(n=float(len(base) / len(bm)), box_area=per((base.x1 - base.x0) * (base.y1 - base.y0)),
                       side_sq=per(bside ** 2)),
        realistic_median_side_sq_x8=float(np.median(bside) ** 2 * 8 / 640 ** 2))
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    out = paths.RESULTS / f'{a.set}_checks.json'
    json.dump(res, open(out, 'w'), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))
    print('wrote', out)


def master(a, dev):
    """Control B: the master factor of the glyphs."""
    rows = []
    base = Physics().replace(margin=1728, reach=1024, depth_std=50e-6, depth_max=150e-6, oversample=2,
                             full_well=0.0, read_noise=0.0, prnu=0.0, bits=0)
    cfg = dict(seed=17, per_session=100)
    ids = [k * 1250 for k in range(4)]
    recs = {}
    for f in a.factors:
        lay = FresnelLayout(scale=1, factor=f)
        cam = camera(CAMERA_SEED, base, lay)
        for i in ids:
            t0 = time.time()
            sc = scene_of(i, cfg, base, lay)
            dt = time.time() - t0
            ses = session(17 * 1000 + i // 100, base)
            img = record(sensor_intensity(dict(sc, sensor_dust=cam['dust']), ses, base, dev), ses, base, cam, None, dev)
            blank = record(sensor_intensity(dict(sc, sensor_dust=cam['dust']), ses, base, dev, sample=False), ses, base,
                           cam, None, dev)
            key = [(o['kind'], o.get('classe'), o['x'], o['y'], o['mask'].shape) for o in sc['objects'] + sc['dust']]
            recs[(f, i)] = (img.astype(np.float64), blank.astype(np.float64), key, sc)
            rows.append(dict(factor=f, image_id=i, scene_seconds=dt, n_objects=len(sc['objects']),
                             n_dust=len(sc['dust']), n_letters=len(sc['rows']),
                             master_mpix=sum(o['master'].size for o in sc['objects']) / 1e6))
            print(rows[-1], flush=True)
    ref = max(a.factors)
    for r in rows:
        img, blank, key, sc = recs[(r['factor'], r['image_id'])]
        rimg, rblank, rkey, rsc = recs[(ref, r['image_id'])]
        r['same_objects_as_ref'] = key == rkey
        r['same_rows_int_boxes'] = [(x['classe'], x['x0'], x['y0'], x['x1'], x['y1']) for x in sc['rows']] == \
            [(x['classe'], x['x0'], x['y0'], x['x1'], x['y1']) for x in rsc['rows']]
        r['rel_rms_vs_ref'] = float((img - rimg).std() / (rimg - rblank).std())
        r['max_abs_dn_vs_ref'] = float(np.abs(img - rimg).max())
    t = pd.DataFrame(rows)
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    t.to_csv(paths.RESULTS / 'base_newrec_master.csv', index=False, float_format='%.6g')
    print(t.to_string())


def table(a):
    ev = paths.RESULTS / 'eval'
    sets = [('base_newrec', 'B control: new code at 19.25 mm'), ('realistic', 'B reference: base set on disk, --no-aux'),
            ('bench_1mm_dense', 'C control: bench_1mm + fillers'), ('bench_1mm', 'pilot r1 (copied)')]
    rows = []
    for s, role in sets:
        for f in FLOWS:
            p = ev / s / f'{f}_r1.json'
            r = dict(set=s, role=role, flow=f, rep=1, source=str(p.relative_to(paths.PROJECT)) if p.exists() else '')
            if p.exists():
                j = json.load(open(p))
                r.update({m: j[m] for m in METRICS})
            else:
                r.update({m: math.nan for m in METRICS})
            rows.append(r)
    t = pd.DataFrame(rows)
    get = lambda s, f, m: float(t[(t.set == s) & (t.flow == f)][m].iloc[0])   # noqa: E731
    # paired differences of C
    diffs = []
    for f in FLOWS:
        diffs.append(dict(set='bench_1mm_dense - bench_1mm', role='C paired difference', flow=f, rep=1,
                          source='', **{m: get('bench_1mm_dense', f, m) - get('bench_1mm', f, m) for m in METRICS}))
    t = pd.concat([t, pd.DataFrame(diffs)], ignore_index=True)
    t.to_csv(paths.RESULTS / 'controls.csv', index=False, float_format='%.6g')
    print(t.to_string())
    # the reading rules of P2 (crops only): nearer to R_ant or to R_pil, in each metric
    pil = dict(f1=get('bench_1mm', 'raw', METRICS[0]), rej=get('bench_1mm', 'raw', METRICS[1]))
    ant = dict(f1=get('realistic', 'raw', METRICS[0]), rej=get('realistic', 'raw', METRICS[1]))
    reading = dict(R_pil=pil, R_ant=ant)
    for s, ctl in [('base_newrec', 'B'), ('bench_1mm_dense', 'C')]:
        c = dict(f1=get(s, 'raw', METRICS[0]), rej=get(s, 'raw', METRICS[1]))
        r = dict(control=c)
        if any(math.isnan(v) for v in list(c.values()) + list(ant.values())):
            r['outcome'] = 'not available (a set of results is missing)'
        else:
            near = {m: 'R_ant' if abs(c[m] - ant[m]) < abs(c[m] - pil[m]) else
                    'R_pil' if abs(c[m] - pil[m]) < abs(c[m] - ant[m]) else 'tie' for m in ('f1', 'rej')}
            r['distances'] = {m: dict(to_R_ant=abs(c[m] - ant[m]), to_R_pil=abs(c[m] - pil[m])) for m in ('f1', 'rej')}
            r['nearer'] = near
            both = set(near.values())
            if ctl == 'B':
                r['outcome'] = ('the new code reproduces the old one: the improvement at 1.0 mm is not an effect of the '
                                'code' if both == {'R_ant'} else
                                'effect of the code' if both == {'R_pil'} else
                                'inconclusive: run the arm that separates the two new pieces')
            else:
                r['outcome'] = ('the neighbours explain the improvement' if both == {'R_ant'} else
                                'the neighbours do not explain it' if both == {'R_pil'} else 'partial')
        reading[ctl] = r
    json.dump(reading, open(paths.RESULTS / 'controls_reading.json', 'w'), indent=1)
    print(json.dumps(reading, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('what', choices=['removed', 'dense', 'master', 'table'])
    ap.add_argument('--set', default='bench_1mm_dense')
    ap.add_argument('--ref', default='bench_1mm')
    ap.add_argument('--ids', type=int, nargs='*', default=[])
    ap.add_argument('--n-cover', type=int, default=100)
    ap.add_argument('--factors', type=int, nargs='+', default=[16, 8, 4])
    ap.add_argument('--device', default='cpu')
    a = ap.parse_args()
    torch.set_num_threads(4)
    if a.what == 'table':
        return table(a)
    dev = pick_device(a.device)
    if a.what == 'removed':
        removed(a.ref, a.set, a.ids, dev)
    elif a.what == 'dense':
        dense(a, dev)
    else:
        master(a, dev)


if __name__ == '__main__':
    main()
