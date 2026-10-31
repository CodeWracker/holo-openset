"""Pattern localisation.

* YoloDetector: class-agnostic YOLO12 trained on holograms of SEEN classes only (holo_openset.yolo); it looks at the
  raw hologram and is shared by every flow. Images larger than 640 x 640 (a full sensor frame) are cut into
  overlapping 640 x 640 tiles; boxes cut by an inner tile edge are dropped (the overlap is larger than any letter, so
  they are whole in a neighbouring tile) and the rest are merged by non-maximum suppression.
* threshold_detect: the training-free localiser of the pixel oracle -- on a reconstructed image every pattern is
  dark ink on a flat background: smooth -> threshold -> close -> connected components -> boxes.
* CsvBoxes / GtBoxes: boxes from a file or from the annotations.
"""
import os

import numpy as np
import pandas as pd
from scipy import ndimage

TILE, OVERLAP = 640, 160


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def match(dets, gts, thr=0.5):
    """Greedy IoU matching. -> list of (det_idx, gt_idx or -1, iou), one per detection."""
    pairs = sorted(((iou(d, g), i, j) for i, d in enumerate(dets) for j, g in enumerate(gts)), reverse=True)
    used_d, used_g, out = set(), set(), {}
    for v, i, j in pairs:
        if v < thr:
            break
        if i in used_d or j in used_g:
            continue
        used_d.add(i)
        used_g.add(j)
        out[i] = (j, v)
    return [(i, out.get(i, (-1, 0.0))[0], out.get(i, (-1, 0.0))[1]) for i in range(len(dets))]


def tiles(h, w, tile=TILE, overlap=OVERLAP):
    """Top-left corners of overlapping tiles covering an h x w image."""
    def starts(n):
        if n <= tile:
            return [0]
        s = list(range(0, n - tile, tile - overlap))
        return s + [n - tile]
    return [(y, x) for y in starts(h) for x in starts(w)]


def nms(boxes, scores, thr=0.5):
    import torch
    from torchvision.ops import nms as tv_nms
    if len(boxes) == 0:
        return np.zeros(0, int)
    return tv_nms(torch.as_tensor(boxes, dtype=torch.float32), torch.as_tensor(scores, dtype=torch.float32),
                  thr).numpy()


class YoloDetector:
    def __init__(self, weights, conf=0.25, device='cpu', batch=16):
        from ultralytics import YOLO
        if str(device) == 'cpu':
            os.environ.setdefault('CUDA_VISIBLE_DEVICES', '')
        self.model = YOLO(str(weights))
        self.conf, self.batch = conf, batch
        self.device = 'cpu' if str(device) == 'cpu' else 0   # the process sees one GPU (model.pick_device)

    def _predict(self, crops):
        out = []
        for k in range(0, len(crops), self.batch):
            res = self.model.predict([np.repeat(c[:, :, None], 3, 2) for c in crops[k:k + self.batch]], imgsz=TILE,
                                     conf=self.conf, iou=0.5, device=self.device, verbose=False)
            out += [(r.boxes.xyxy.cpu().numpy(), r.boxes.conf.cpu().numpy()) if r.boxes is not None and len(r.boxes)
                    else (np.zeros((0, 4)), np.zeros(0)) for r in res]
        return out

    def __call__(self, img):
        """img: uint8 [h, w] hologram -> boxes xyxy [N, 4], confidences [N]."""
        h, w = img.shape
        if (h, w) == (TILE, TILE):
            return self._predict([img])[0]
        corners = tiles(h, w)
        boxes, conf = [], []
        for (y, x), (b, c) in zip(corners, self._predict([img[y:y + TILE, x:x + TILE] for y, x in corners])):
            if len(b) == 0:
                continue
            e = 2.0  # px: a box this close to an inner tile edge is cut by it
            keep = ~(((b[:, 0] < e) & (x > 0)) | ((b[:, 1] < e) & (y > 0)) |
                     ((b[:, 2] > TILE - e) & (x + TILE < w)) | ((b[:, 3] > TILE - e) & (y + TILE < h)))
            boxes.append(b[keep] + [x, y, x, y])
            conf.append(c[keep])
        if not boxes:
            return np.zeros((0, 4)), np.zeros(0)
        boxes, conf = np.concatenate(boxes), np.concatenate(conf)
        k = nms(boxes, conf)
        return boxes[k], conf[k]


def threshold_detect(rec_u8, thresh=0.62, close_px=3, min_area=150, min_side=12, smooth=1.0, merge_gap=4):
    """rec_u8: reconstructed image (uint8, bright background, dark ink) -> list of (x0, y0, x1, y1, area)."""
    img = rec_u8.astype(np.float32) / 255.0
    if smooth > 0:
        img = ndimage.gaussian_filter(img, smooth)
    ink = img < thresh * np.median(img) / 0.8
    if close_px > 0:
        ink = ndimage.binary_closing(ink, structure=np.ones((2 * close_px + 1, 2 * close_px + 1), bool))
    lab, n = ndimage.label(ink)
    if n == 0:
        return []
    areas = ndimage.sum(ink, lab, index=np.arange(1, n + 1))
    boxes = []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        if areas[i] >= min_area and max(x1 - x0, y1 - y0) >= min_side:
            boxes.append([x0, y0, x1, y1, float(areas[i])])
    return [tuple(b) for b in _merge(boxes, merge_gap)]


def _merge(boxes, gap):
    """Merge boxes that overlap or touch within `gap` px (broken strokes of one letter)."""
    changed = True
    while changed and len(boxes) > 1:
        changed = False
        out, used = [], [False] * len(boxes)
        for i, a in enumerate(boxes):
            if used[i]:
                continue
            cur = list(a)
            for j in range(i + 1, len(boxes)):
                b = boxes[j]
                if used[j] or not (b[0] <= cur[2] + gap and cur[0] <= b[2] + gap and b[1] <= cur[3] + gap
                                   and cur[1] <= b[3] + gap):
                    continue
                area = lambda r: (r[2] - r[0]) * (r[3] - r[1])  # noqa: E731
                small = min(area(b), area(cur))
                iw, ih = min(cur[2], b[2]) - max(cur[0], b[0]), min(cur[3], b[3]) - max(cur[1], b[1])
                if (iw > 0 and ih > 0 and iw * ih >= 0.5 * small) or small < 0.15 * max(area(b), area(cur)):
                    cur = [min(cur[0], b[0]), min(cur[1], b[1]), max(cur[2], b[2]), max(cur[3], b[3]), cur[4] + b[4]]
                    used[j] = changed = True
            out.append(cur)
        boxes = out
    return boxes


class CsvBoxes:
    def __init__(self, path):
        self.df = pd.read_csv(path)

    def __call__(self, name):
        d = self.df[self.df.filename == os.path.basename(str(name))]
        return d[['x0', 'y0', 'x1', 'y1']].to_numpy(float), np.ones(len(d))


class GtBoxes:
    def __init__(self, ann):
        self.ann = ann

    def __call__(self, name):
        d = self.ann[self.ann.filename == os.path.basename(str(name))]
        return d[['x0', 'y0', 'x1', 'y1']].to_numpy(float), np.ones(len(d))
