"""Dataset access and batched embedding of patterns.

A set (data/holo_openset/<name>, built by `python -m holo_openset simulate`) holds the holograms as one uint8 array
[N, h, w] (holograms.npy), its reconstructions as uint8 [N, 3, h, w] (rec_<method>.npy), annotations.csv with one
box per letter and metadata.csv with the split and session of each image. Images are addressed by image id.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image

from holo_openset import paths
from holo_openset.model import square_boxes
from holo_openset.protocol import classes as split_classes
from holo_openset.sim.letters import CLASSES
from holo_openset.sim.physics import Z0


def load_hologram(path):
    """Read a hologram file as uint8 [h, w] (any size: the Fourier layer is applied at the physical frequencies)."""
    return np.asarray(Image.open(path).convert('L'))


class Dataset:
    """Annotations of a set and one of its image arrays (holograms or a reconstruction)."""

    def __init__(self, root=None, array='holograms.npy', ann=None):
        self.root = Path(root) if root else paths.dataset(paths.BASE)
        self.ann = ann if ann is not None else pd.read_csv(self.root / 'annotations.csv')
        meta = pd.read_csv(self.root / 'metadata.csv')
        self.row = {int(i): k for k, i in enumerate(meta.image_id)}
        self.arr = np.load(array if Path(str(array)).is_absolute() else self.root / array, mmap_mode='r')
        cfg = self.root / 'physics.json'
        self.z0 = json.load(open(cfg))['physics'].get('z0', Z0) if cfg.exists() else Z0

    @staticmethod
    def classes(rep):
        return split_classes(rep)

    def image(self, image_id):
        return np.asarray(self.arr[self.row[int(image_id)]])

    def images(self, ids):
        return torch.from_numpy(np.stack([self.image(int(i)) for i in ids]))


class Array:
    """A bare image array (e.g. auxiliary scenes), addressed by row."""

    def __init__(self, path):
        self.arr = np.load(path, mmap_mode='r')

    def image(self, i):
        return np.asarray(self.arr[int(i)])

    def images(self, ids):
        return torch.from_numpy(np.stack([self.image(int(i)) for i in ids]))


@torch.no_grad()
def embed_annotations(model, dataset, rows, buffer=0.25, batch_images=16):
    """Embeddings for annotation rows (DataFrame with image_id, x0, y0, x1, y1), in row order."""
    model.eval()
    rows = rows.reset_index(drop=True)
    out = np.zeros((len(rows), 128), np.float32)
    by_img = rows.groupby('image_id').indices
    ids = np.array(sorted(by_img))
    for s in range(0, len(ids), batch_images):
        chunk = ids[s:s + batch_images]
        idx = np.concatenate([by_img[i] for i in chunk])
        bidx = np.concatenate([np.full(len(by_img[i]), k) for k, i in enumerate(chunk)])
        b = square_boxes(rows.loc[idx, ['x0', 'y0', 'x1', 'y1']].to_numpy(), buffer)
        filt = model.filtered(dataset.images(chunk))
        out[idx] = model.embed_boxes(filt, torch.from_numpy(np.c_[bidx, b]).float()).cpu().numpy()
    return out


@torch.no_grad()
def embed_image(model, img_u8, boxes_xyxy, buffer=0.25, max_boxes=512):
    """Embeddings of the patterns at boxes_xyxy (N x 4) in one image (uint8 [h, w] or [3, h, w], any size)."""
    model.eval()
    if len(boxes_xyxy) == 0:
        return np.zeros((0, 128), np.float32)
    filt = model.filtered(torch.from_numpy(np.asarray(img_u8))[None])
    b = square_boxes(boxes_xyxy, buffer)
    out = [model.embed_boxes(filt, torch.from_numpy(np.c_[np.zeros(len(c)), c]).float()).cpu().numpy()
           for c in np.array_split(b, max(1, -(-len(b) // max_boxes)))]
    return np.concatenate(out)


@torch.no_grad()
def fourier_view(model, holo_u8):
    """What the network 'sees': the hologram after the learned Fourier layer (float [h, w]; the modulus for the
    complex layer)."""
    f = model.filtered(torch.from_numpy(np.asarray(holo_u8))[None])[0]
    return f[-1].cpu().numpy()


__all__ = ['CLASSES', 'Dataset', 'Array', 'embed_annotations', 'embed_image', 'fourier_view', 'load_hologram']
