"""End to end on the 640 x 640 windows: the YOLO localiser of repetition r gives the boxes, every flow embeds them.

  1. detections: the YOLO of repetition r on every val/test hologram (conf >= 0.25, fixed a priori), matched greedily
     to the annotations at IoU >= 0.5 (missed letters listed with det = 0; detections near a dust particle flagged).
  2. recognition: gallery (val) and queries (test) are the matched detections, in the boxes found by the detector;
     letters it missed are left out of both (reported as recall); its false detections are extra queries that must
     be rejected at the same threshold. The per-object flow focuses each DETECTED box (its images are rebuilt here).

    python -m holo_openset experiment e2e --device cuda:N [--rep 1 2] [--flows ...]
Output: results/holo_openset/e2e.csv, data/holo_openset/realistic/dets_yolo_r{r}.csv
"""
import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.data import embed_annotations
from holo_openset.detect import YoloDetector, match
from holo_openset.experiments.common import KEEP, device, fmt, model, parser, save, strict
from holo_openset.flows import FLOWS, dataset
from holo_openset.reconstruct import Holograms, channels, per_object


def detections(rep, dev, root=None):
    root = root or paths.dataset(paths.BASE)
    out = root / f'dets_yolo_r{rep}.csv'
    if out.exists():
        return pd.read_csv(out)
    yolo = YoloDetector(paths.yolo_weights(rep), device=dev)
    ann = pd.read_csv(root / 'annotations.csv')
    ann['row_id'] = np.arange(len(ann))
    dust = pd.read_csv(root / 'dust.csv').groupby('image_id')
    holo = dataset('raw', root)
    rows = []
    for (i, fn), g in ann[ann.split.isin(['val', 'test'])].groupby(['image_id', 'filename']):
        boxes, confs = yolo(holo.image(i))
        gts = g[['x0', 'y0', 'x1', 'y1']].to_numpy().tolist()
        dd = dust.get_group(i)[['x0', 'y0', 'x1', 'y1']].to_numpy() if i in dust.groups else np.empty((0, 4))
        hit = set()
        for k, j, v in match([tuple(b) for b in boxes], gts, 0.5):
            b = boxes[k]
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            near = bool(len(dd) and ((dd[:, 0] <= cx) & (cx <= dd[:, 2]) & (dd[:, 1] <= cy) & (cy <= dd[:, 3])).any())
            if j >= 0:
                hit.add(j)
            rows.append(dict(image_id=i, filename=fn, split=g.split.iloc[0], x0=b[0], y0=b[1], x1=b[2], y1=b[3],
                             conf=float(confs[k]), det=1, gt_idx=int(g.row_id.iloc[j]) if j >= 0 else -1, iou=v,
                             near_dust=near))
        for j in set(range(len(gts))) - hit:
            rows.append(dict(image_id=i, filename=fn, split=g.split.iloc[0], x0=gts[j][0], y0=gts[j][1], x1=gts[j][2],
                             y1=gts[j][3], conf=0.0, det=0, gt_idx=int(g.row_id.iloc[j]), iou=0.0, near_dust=False))
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    return df


class MemImages:
    """Images held in memory, by image id."""

    def __init__(self, imgs):
        self.imgs = imgs

    def image(self, i):
        return self.imgs[int(i)]

    def images(self, ids):
        return torch.from_numpy(np.stack([self.imgs[int(i)] for i in ids]))


def edf_on_boxes(boxes_by_image, dev, root=None):
    """Per-object focus of every image on the given boxes (the autofocus distance of the base caches)."""
    src = Holograms(root or paths.dataset(paths.BASE))
    af = pd.read_csv(src.root / 'autofocus.csv').set_index('image_id').z_af
    out = {}
    for i, b in boxes_by_image.items():
        a = src.amplitude(int(i), dev)
        out[int(i)] = channels(per_object(a, float(af.loc[int(i)]), b)[0]).cpu().numpy()
    return out


def run(rep, flows, dev):
    det = detections(rep, dev)
    base = dataset('raw')
    ann = base.ann.copy()
    vt = ann.split.isin(['val', 'test']).to_numpy()
    found = det[(det.det == 1) & (det.gt_idx >= 0)].sort_values('iou', ascending=False).drop_duplicates('gt_idx')
    fps = det[det.gt_idx < 0].reset_index(drop=True)
    sub = ann.copy()
    sub.loc[found.gt_idx.to_numpy(), ['x0', 'y0', 'x1', 'y1']] = found[['x0', 'y0', 'x1', 'y1']].to_numpy()
    keep = np.zeros(len(ann), bool)
    keep[found.gt_idx.to_numpy()] = True
    sub.loc[vt & ~keep, 'split'] = 'missed'
    sel = sub.split.isin(['val', 'test']).to_numpy()
    rows = []
    for flow in flows:
        m = model(flow, rep, dev)
        if m is None:
            continue
        if flow == 'rec_edf':
            allb = pd.concat([sub[sel][['image_id', 'x0', 'y0', 'x1', 'y1']], fps[['image_id', 'x0', 'y0', 'x1', 'y1']]])
            imgs = MemImages(edf_on_boxes({i: g[['x0', 'y0', 'x1', 'y1']].to_numpy() for i, g in allb.groupby('image_id')},
                                          dev))
        else:
            imgs = dataset(flow, ann=sub)
        ds = dataset('raw', ann=sub)
        emb = np.zeros((len(sub), 128), np.float32)
        emb[sel] = embed_annotations(m, imgs, sub[sel])
        r = strict(m, ds, rep, emb)
        seen = ds.classes(rep)[0]
        val_seen = np.where((sub.split == 'val').to_numpy() & sub.classe.isin(seen).to_numpy())[0]
        fp_rej = fp_rej_dust = np.nan
        if len(fps):
            s = (embed_annotations(m, imgs, fps) @ emb[val_seen].T).max(1)
            fp_rej = float((s < r['threshold']).mean())
            if fps.near_dust.any():
                fp_rej_dust = float((s[fps.near_dust.to_numpy()] < r['threshold']).mean())
        rows.append(dict(rep=rep, flow=flow, detector_recall=float(keep[vt].mean()), n_fp=len(fps),
                         fp_per_img=len(fps) / ann[vt].image_id.nunique(), fp_near_dust=int(fps.near_dust.sum()),
                         fp_rejected=fp_rej, fp_dust_rejected=fp_rej_dust, **{k: r[k] for k in KEEP if k in r}))
        print(fmt(rows[-1]), flush=True)
    return rows


def main(argv=None):
    a = parser(__doc__, list(FLOWS)).parse_args(argv)
    dev = device(a)
    for r in a.rep:
        save(run(r, a.flows, dev), 'e2e', keys=['rep', 'flow'])
