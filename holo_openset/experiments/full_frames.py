"""Full sensor frames: what each flow costs and what it buys on a whole acquisition of the bench.

The question: is the conventional reconstruction as fast as the learned layer only because the
dataset images are small? Here every flow runs end to end on full frames of the sensor of the bench (3840 x 2748 px,
29.4 mm^2; python -m holo_openset simulate full), acquired in the test sessions with the physics of the base set:

  detect      the YOLO of the repetition, in overlapping 640 x 640 tiles (shared by every flow)
  front end   none (raw) | the learned layer, real or complex, or the fixed Wiener filter, on the WHOLE frame (one
              transform pair at the physical frequencies of the training grid) | the conventional reconstruction of
              the whole frame: flat field, back-propagation at z0, blind autofocus (114 reconstructions), per-object
              focus (25 more, scored in each detected box), twin-image removal (50 passes)
  embed       ResNet18 on the crops of the detected boxes
  decide      nearest neighbour in the gallery of the repetition (val patterns of the seen classes, 640 x 640 windows
              of the base set, threshold calibrated there) -> class or unknown
Each stage is timed with the GPU synchronised before and after (wall clock, one GPU). Accuracy: the strict open-set
metrics of the paper with that gallery and threshold, on (gt) the annotated boxes and (det) the detected boxes (missed
letters left out and reported as recall; false detections are extra queries that must be rejected).

    python -m holo_openset experiment full_frames --device cuda:N [--rep 1 2 3] [--frames 40]
Output: results/holo_openset/full_frames.csv (accuracy per rep x flow x boxes),
        results/holo_openset/full_frames_time.csv (time per frame x rep x flow x stage)

--frames-set NAME reads another set of full frames (data/NAME, from `simulate full --name ...`) and writes NAME.csv,
NAME_time.csv and NAME_focus.csv (the distance each flow reconstructed each frame at, against the true one). A flow
that reuses a distance (reconstruct.FOCUS with every != 1) searches it on the first frame(s) of each session of the
set and the 'autofocus' stage is recorded on those frames only: the cost per frame is that time divided by the frames
that share it.
"""
import time

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.data import embed_annotations
from holo_openset.detect import YoloDetector, match
from holo_openset.evaluate import IDX, calibrate, open_set_metrics
from holo_openset.experiments.common import device, fmt, model, parser, save
from holo_openset.flows import FLOWS, PAPER_FLOWS, dataset
from holo_openset.model import square_boxes
from holo_openset.reconstruct import EDF, FOCUS, Holograms, autofocus, backprop, channels, focus_blocks, \
    per_object, remove_twin


class Clock:
    def __init__(self, dev):
        self.dev, self.t = dev, {}

    def __call__(self, name, fn, *args):
        if self.dev.type == 'cuda':
            torch.cuda.synchronize(self.dev)
        t0 = time.perf_counter()
        out = fn(*args)
        if self.dev.type == 'cuda':
            torch.cuda.synchronize(self.dev)
        self.t[name] = self.t.get(name, 0.0) + time.perf_counter() - t0
        return out


class Distances:
    """The distance of each frame under a way of focusing of reconstruct.FOCUS. A distance shared by several frames
    (once per session, every M frames) is searched when its first frame arrives; the time of each search is kept for
    the frame it was run on."""

    def __init__(self, src, focus, ids, dev):
        self.src, self.focus, self.dev = src, focus, dev
        self.block = {i: (tuple(members), focused) for members, focused in focus_blocks(ids, src.session, focus)
                      for i in members}
        self.z, self.seconds = {}, {}

    def __call__(self, i, a, clock):
        members, focused = self.block[i]
        if members not in self.z:
            found = []
            for j in focused:
                aj = a if j == i else self.src.amplitude(j, self.dev)
                bg = self.src.blank(j, self.dev) if self.focus.mask > 0 else None
                c = Clock(self.dev)
                found.append(c('autofocus', autofocus, aj, self.src.z0, self.focus, bg)[0])
                self.seconds[j] = c.t['autofocus']
            self.z[members] = float(np.median(found))
        if i in self.seconds:
            clock.t['autofocus'] = clock.t.get('autofocus', 0.0) + self.seconds.pop(i)
        return self.z[members]


def front_end(flow, src, i, boxes, dev, clock, z0, dist=None, used=None):
    """The image the network of `flow` receives for full frame i (tensor on dev). dist: the Distances of a flow of
    the distance study; used: dict that receives the distance the frame was reconstructed at."""
    rec = FLOWS[flow]['rec']
    if rec is None:
        return clock('load', lambda: torch.from_numpy(np.array(src.holo[src.row[i]])).to(dev))
    a = clock('normalise', src.amplitude, i, dev)
    if rec == 'z0':
        z = z0
        u = clock('reconstruct', lambda: backprop(a, [z0])[0])
    else:
        z = dist(i, a, clock) if dist is not None else clock('autofocus', autofocus, a, z0)[0]
        if rec in EDF:
            u = clock('per_object', lambda: per_object(a, z, boxes, *EDF[rec])[0])
        elif rec == 'twin':
            u = clock('twin', remove_twin, a, z)
        else:
            u = clock('reconstruct', lambda: backprop(a, [z])[0])
    if used is not None:
        used[i] = z
    return clock('channels', channels, u)


def embed_boxes(m, filt, xyxy, chunk=512):
    """Embeddings of the boxes xyxy in an image already through the layer (filt [1, C, h, w])."""
    if len(xyxy) == 0:
        return np.zeros((0, 128), np.float32)
    b = square_boxes(np.asarray(xyxy), 0.25)
    return np.concatenate([m.embed_boxes(filt, torch.from_numpy(np.c_[np.zeros(len(c)), c]).float()).cpu().numpy()
                           for c in np.array_split(b, max(1, -(-len(b) // chunk)))])


def gallery(m, flow, rep, ds):
    """Embeddings of the val patterns of the seen classes (base set) and the calibrated global threshold."""
    ann = ds.ann
    seen = ds.classes(rep)[0]
    labels = ann.classe.map(IDX).to_numpy()
    val_seen = np.where((ann.split == 'val').to_numpy() & ann.classe.isin(seen).to_numpy())[0]
    emb = np.zeros((len(ann), 128), np.float32)
    emb[val_seen] = embed_annotations(m, dataset(flow), ann.iloc[val_seen])
    t, _ = calibrate(emb, labels, val_seen, ann.filename.to_numpy(), [IDX[c] for c in seen])
    return emb[val_seen], labels[val_seen], t, [IDX[c] for c in seen]


def metrics(q, gal, gal_lab, t, true, seen_idx):
    s = q @ gal.T
    pred, score = gal_lab[s.argmax(1)], s.max(1)
    known = np.isin(true, seen_idx)
    r = open_set_metrics(pred, score, true, known, t)
    return {f'novel_{k}': v for k, v in r.items()}


def run(rep, flows, dev, frames=None, frames_set='full_frames'):
    root = paths.dataset(frames_set)
    src = Holograms(root)
    ann = pd.read_csv(root / 'annotations.csv')
    ids = [int(i) for i in src.ids][:frames]
    yolo = YoloDetector(paths.yolo_weights(rep), device=dev)
    base = dataset('raw')
    dets, times, rows, focus = {}, [], [], []
    for i in ids:  # detection is shared by every flow: timed once per frame
        clock = Clock(dev)
        img = np.array(src.holo[src.row[i]])
        dets[i] = clock('detect', yolo, img)
        times.append(dict(rep=rep, frame=i, flow='all', stage='detect', seconds=clock.t['detect'],
                          n_boxes=len(dets[i][0])))
    for flow in flows:
        m = model(flow, rep, dev)
        if m is None:
            continue
        gal, gal_lab, t, seen_idx = gallery(m, flow, rep, base)
        q_gt, true_gt, q_det, true_det, fp_scores = [], [], [], [], []
        n_gt = n_found = 0
        rec = FLOWS[flow]['rec']
        dist = Distances(src, FOCUS[rec], ids, dev) if rec in FOCUS else None
        used = {}
        for i in ids:
            clock = Clock(dev)
            g = ann[ann.image_id == i]
            gt = g[['x0', 'y0', 'x1', 'y1']].to_numpy(float)
            boxes = dets[i][0]
            x = front_end(flow, src, i, boxes, dev, clock, src.z0, dist, used)
            with torch.no_grad():
                filt = clock('layer', m.filtered, x[None])   # the Fourier layer (identity for raw and rec_*)
                e_det = clock('embed', embed_boxes, m, filt, boxes)
                clock('decide', lambda: (e_det @ gal.T).max(1))
                e_gt = embed_boxes(m, filt, gt)
            q_gt.append(e_gt)
            true_gt.append(g.classe.map(IDX).to_numpy())
            hit = {j: k for k, j, _ in match([tuple(b) for b in boxes], gt.tolist(), 0.5) if j >= 0}
            n_gt += len(gt)
            n_found += len(hit)
            if hit:
                q_det.append(e_det[list(hit.values())])
                true_det.append(g.classe.map(IDX).to_numpy()[list(hit.keys())])
            fp = np.setdiff1d(np.arange(len(boxes)), list(hit.values()))
            fp_scores.append((e_det[fp] @ gal.T).max(1) if len(fp) else np.zeros(0))
            for st, sec in clock.t.items():
                times.append(dict(rep=rep, frame=i, flow=flow, stage=st, seconds=sec, n_boxes=len(boxes)))
            if i in used:
                focus.append(dict(rep=rep, flow=flow, frame=i, session=src.session.get(i), z=used[i],
                                  true_z=src.true_z.get(i)))
            print(rep, flow, i, {k: round(v, 4) for k, v in clock.t.items()}, flush=True)
        r_gt = metrics(np.concatenate(q_gt), gal, gal_lab, t, np.concatenate(true_gt), seen_idx)
        r_det = metrics(np.concatenate(q_det), gal, gal_lab, t, np.concatenate(true_det), seen_idx)
        fps = np.concatenate(fp_scores)
        common = dict(rep=rep, flow=flow, frames=len(ids), letters=n_gt, threshold=t)
        rows.append(dict(common, boxes='gt', detector_recall=1.0, **r_gt))
        rows.append(dict(common, boxes='det', detector_recall=n_found / max(n_gt, 1), fp_per_frame=len(fps) / len(ids),
                         fp_rejected=float((fps < t).mean()) if len(fps) else np.nan, **r_det))
        print(fmt(rows[-2]), '\n', fmt(rows[-1]), flush=True)
    return rows, times, focus


def main(argv=None):
    ap = parser(__doc__, list(PAPER_FLOWS))
    ap.add_argument('--frames', type=int, default=None)
    ap.add_argument('--frames-set', default='full_frames', help='set of full frames under data/ (simulate full --name)')
    a = ap.parse_args(argv)
    dev = device(a)
    for r in a.rep:
        rows, times, focus = run(r, a.flows, dev, a.frames, a.frames_set)
        save(rows, a.frames_set, keys=['rep', 'flow', 'boxes'])
        save(times, f'{a.frames_set}_time', keys=['rep', 'flow', 'frame', 'stage'])
        if a.frames_set != 'full_frames' or any(f not in PAPER_FLOWS for f in a.flows):
            save(focus, f'{a.frames_set}_focus', keys=['rep', 'flow', 'frame'])
