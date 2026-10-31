"""The pixel oracle: open-set recognition with no learning at all.

  reconstruct  Wiener inversion of the absorption part at the nominal distance (one transform pair):
               W = C / (C^2 + 0.05), C = cos(pi lambda z0 |f|^2), applied to sqrt(I / B) minus its mean
  localise     smooth -> threshold -> close -> connected components (holo_openset.detect.threshold_detect)
  compare      32 x 32 pixel crops, mean-centred and L2-normalised; the same gallery and thresholds as the networks
Two variants: on the ground-truth boxes ('gt': the pixel representation alone) and on the boxes of the threshold
localiser ('det': the complete training-free flow; missed letters left out, false detections are extra queries).
On a robustness set, the test patterns come from that set and the gallery from the base validation split, in both
modes.

    python -m holo_openset experiment oracle [--variants ...] [--workers 16]
Output: results/holo_openset/oracle.csv
"""
import os

os.environ.setdefault('OMP_NUM_THREADS', '1')

from concurrent.futures import ProcessPoolExecutor  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402

from holo_openset import paths  # noqa: E402
from holo_openset.detect import match, threshold_detect  # noqa: E402
from holo_openset.experiments.common import KEEP, fmt, l2_rows, parser, save  # noqa: E402
from holo_openset.sim.physics import PIXEL, WAVELENGTH, Z0  # noqa: E402
from holo_openset.sim.variants import VARIANTS  # noqa: E402

CROP = 32


def wiener_filter(shape, z=Z0, eps=0.05):
    fy, fx = np.fft.fftfreq(shape[0], d=PIXEL), np.fft.fftfreq(shape[1], d=PIXEL)
    c = np.cos(np.pi * WAVELENGTH * z * (fx[None, :] ** 2 + fy[:, None] ** 2))
    return c / (c * c + eps)


def to_uint8(x, lo_pct=0.5, hi_pct=99.5):
    lo, hi = np.percentile(x, [lo_pct, hi_pct])
    return (np.clip((x - lo) / max(hi - lo, 1e-9), 0, 1) * 255).round().astype(np.uint8)


def square_crop(img, box, size=CROP):
    """The box (only the box: neighbours outside it never leak in) padded to a square and resized to size x size."""
    x0, y0, x1, y1 = box
    side = int(round(max(x1 - x0, y1 - y0, 2)))
    sx0, sy0 = int(round((x0 + x1) / 2 - side / 2)), int(round((y0 + y1) / 2 - side / 2))
    canvas = np.full((side, side), int(np.median(img)), np.uint8)
    h, w = img.shape
    bx0, by0 = max(0, sx0, int(np.floor(x0))), max(0, sy0, int(np.floor(y0)))
    bx1, by1 = min(w, sx0 + side, int(np.ceil(x1))), min(h, sy0 + side, int(np.ceil(y1)))
    if bx1 > bx0 and by1 > by0:
        canvas[by0 - sy0:by1 - sy0, bx0 - sx0:bx1 - sx0] = img[by0:by1, bx0:bx1]
    return np.asarray(Image.fromarray(canvas).resize((size, size), Image.BILINEAR))


def _work(job):
    i, h, b, intensity, wf, gts, row_ids = job
    a = h.astype(np.float64)
    a = np.sqrt(np.maximum(a / np.maximum(b, 1.0), 0)) if intensity else a / a.mean()
    rec = to_uint8(np.real(np.fft.ifft2(np.fft.fft2(a - a.mean()) * wf)))
    gt_crops = [square_crop(rec, g) for g in gts]
    dets = threshold_detect(rec)
    boxes = [d[:4] for d in dets]
    det_rows, det_crops, hit = [], [], set()
    for k, j, v in match(boxes, gts, 0.5):
        if j >= 0:
            hit.add(j)
        det_rows.append(dict(image_id=i, x0=boxes[k][0], y0=boxes[k][1], x1=boxes[k][2], y1=boxes[k][3], det=1,
                             gt_idx=int(row_ids[j]) if j >= 0 else -1, iou=v))
        det_crops.append(square_crop(rec, boxes[k]))
    return row_ids, gt_crops, det_rows, det_crops


def process(pool, root, ann_sub):
    """Reconstruct, localise and crop every image of ann_sub (rows indexed as in the base annotations)."""
    import json
    holo = np.load(root / 'holograms.npy', mmap_mode='r')
    bg = np.load(root / 'backgrounds.npy', mmap_mode='r')
    meta = pd.read_csv(root / 'metadata.csv')
    row, ses = {int(i): k for k, i in enumerate(meta.image_id)}, dict(zip(meta.image_id, meta.session))
    phys = json.load(open(root / 'physics.json'))['physics']
    wf = wiener_filter(holo.shape[1:], phys.get('z0', Z0))
    jobs = [(int(i), np.array(holo[row[int(i)]]), np.array(bg[ses[int(i)]]), phys['intensity'], wf,
             g[['x0', 'y0', 'x1', 'y1']].to_numpy().tolist(), g.index.to_numpy()) for i, g in ann_sub.groupby('image_id')]
    gt, det_rows, det_crops = {}, [], []
    for rids, gc, dr, dc in pool.map(_work, jobs, chunksize=8):
        gt.update(zip(map(int, rids), gc))
        det_rows += dr
        det_crops += dc
    return gt, pd.DataFrame(det_rows), np.stack(det_crops) if det_crops else np.zeros((0, CROP, CROP), np.uint8)


def evaluate_det(ds, rep, ann, sel_val, val_det, test_det, emb_val_det, emb_test_det):
    """Strict protocol on detections: matched detections replace the boxes, missed letters are dropped, false
    detections of the test images are extra queries."""
    from holo_openset.evaluate import evaluate
    sub = ann.copy()
    emb = np.zeros((len(ann), CROP * CROP), np.float32)
    keep = np.zeros(len(ann), bool)
    for det, e in [(val_det, emb_val_det), (test_det, emb_test_det)]:
        f = det[(det.det == 1) & (det.gt_idx >= 0)].sort_values('iou', ascending=False).drop_duplicates('gt_idx')
        emb[f.gt_idx.to_numpy()] = e[f.index.to_numpy()]
        keep[f.gt_idx.to_numpy()] = True
    vt = sub.split.isin(['val', 'test']).to_numpy()
    sub.loc[vt & ~keep, 'split'] = 'missed'
    ds.ann = sub
    r = evaluate(None, ds, rep, emb=emb)
    ds.ann = ann
    seen = ds.classes(rep)[0]
    val_seen = np.where((sub.split == 'val').to_numpy() & sub.classe.isin(seen).to_numpy())[0]
    fps = test_det.gt_idx.to_numpy() < 0
    fp_rej = float(((emb_test_det[fps] @ emb[val_seen].T).max(1) < r['threshold']).mean()) if fps.any() else np.nan
    test = (ann.split == 'test').to_numpy()
    return dict(detector_recall=float(keep[test].mean()), fp_per_img=float(fps.sum() / ann[test].image_id.nunique()),
                fp_rejected=fp_rej, **{k: r[k] for k in KEEP if k in r})


def main(argv=None):
    ap = parser(__doc__)
    ap.add_argument('--variants', nargs='+', default=['base'] + list(VARIANTS))
    ap.add_argument('--workers', type=int, default=16)
    a = ap.parse_args(argv)
    from holo_openset.evaluate import evaluate
    from holo_openset.flows import dataset
    base_root = paths.dataset(paths.BASE)
    ds = dataset('raw')
    ann = ds.ann
    val, test = (ann.split == 'val').to_numpy(), (ann.split == 'test').to_numpy()
    with ProcessPoolExecutor(a.workers) as pool:
        gt, det, crops = process(pool, base_root, ann[val | test])
        val_ids = set(ann[val].image_id)
        is_val = det.image_id.isin(val_ids).to_numpy()
        val_det, emb_val_det = det[is_val].reset_index(drop=True), l2_rows(crops[is_val])
        emb_gt_base = np.zeros((len(ann), CROP * CROP), np.float32)
        idx = np.where(val | test)[0]
        emb_gt_base[idx] = l2_rows(np.stack([gt[int(k)] for k in idx]))
        for v in a.variants:
            root = base_root if v == 'base' else paths.dataset(f'variants/{v}')
            if not (root / 'holograms.npy').exists():
                print('missing', root, flush=True)
                continue
            if v == 'base':
                emb_gt, t_det, t_crops = emb_gt_base, det[~is_val].reset_index(drop=True), crops[~is_val]
            else:
                vgt, t_det, t_crops = process(pool, root, ann[test])
                emb_gt = emb_gt_base.copy()
                emb_gt[np.where(test)[0]] = l2_rows(np.stack([vgt[int(k)] for k in np.where(test)[0]]))
            emb_t_det = l2_rows(t_crops)
            effect, value, _ = VARIANTS.get(v, ('base', 'base', {}))
            rows = []
            for r in a.rep:
                res = evaluate(None, ds, r, emb=emb_gt)
                rows.append(dict(rep=r, variant=v, effect=effect, value=value, flow='oracle_pixel', boxes='gt',
                                 detector_recall=1.0, **{k: res[k] for k in KEEP if k in res}))
                rows.append(dict(rep=r, variant=v, effect=effect, value=value, flow='oracle_pixel', boxes='det',
                                 **evaluate_det(ds, r, ann, val, val_det, t_det, emb_val_det, emb_t_det)))
            print(v, fmt(rows[-2]), fmt(rows[-1]), flush=True)
            save(rows, 'oracle', keys=['rep', 'variant', 'boxes'])
