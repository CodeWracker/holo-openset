"""Training on SEEN classes only (SupCon + CosFace auxiliary), CPU-friendly.

Each step takes `imgs_per_step` whole holograms, filters them with the learnable Fourier layer and embeds two
jittered views of every seen-class pattern. The Fourier layer gets its own (high) learning rate: with a low one
its 33,704 radial weights barely leave the identity (see the paper, ablation on lr).
Optional auxiliary scenes (seen letters in extra fonts, recorded with the same acquisition) can be added.
"""
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

from holo_openset.data import CLASSES
from holo_openset.model import HoloEmbedder, physical_gpu, physics_weights, square_boxes


class SupConLoss(nn.Module):
    """Supervised contrastive loss (Khosla et al., 2020)."""

    def __init__(self, temperature=0.1):
        super().__init__()
        self.t = temperature

    def forward(self, f, y):
        sim = f @ f.T / self.t
        pos = (y[:, None] == y[None, :]).float()
        pos.fill_diagonal_(0)
        e = torch.exp(sim - sim.max(1, keepdim=True).values.detach())
        denom = e.sum(1) - e.diag() + 1e-10
        valid = pos.sum(1) > 0
        return (-torch.log((e * pos).sum(1) / denom + 1e-10))[valid].mean()


def train(dataset, classes, steps=3000, imgs_per_step=16, buffer=0.25, jitter=0.05, lr=3e-4, lr_fourier=3e-1,
          aux_weight=0.5, mode='radial', aux_scenes=None, threads=12, seed=0, fourier='learned', device='cpu', distance_error=0.0,
          log=print):
    """classes: list of letters to train on (the seen classes). aux_scenes: optional (images_npy, boxes_csv).
    fourier: 'learned' (default) or a deterministic-reconstruction baseline, 'fresnel' / 'wiener': the layer is
    set to the physical transfer function and frozen, so the embedding is trained on reconstructed images."""
    torch.manual_seed(seed)
    rng = np.random.RandomState(seed)
    torch.set_num_threads(threads)
    remap = {c: i for i, c in enumerate(sorted(classes))}
    ann = dataset.ann
    tr = ann[(ann.split == 'train') & ann.classe.isin(classes)][['image_id', 'classe', 'x0', 'y0', 'x1', 'y1']]
    tr = tr.assign(src='set')
    aux_imgs = None
    if aux_scenes is not None:
        aux_imgs = np.load(aux_scenes[0], mmap_mode='r')
        bx = pd.read_csv(aux_scenes[1])
        bx = bx[bx.classe.isin(classes)]
        tr = pd.concat([tr, bx[['image_id', 'classe', 'x0', 'y0', 'x1', 'y1']].assign(src='aux')], ignore_index=True)
    groups = {k: g for k, g in tr.groupby(['src', 'image_id'])}
    keys = list(groups)

    def load(k):
        src, i = k
        return np.asarray(aux_imgs[int(i)]) if src == 'aux' else dataset.image(int(i))

    model = HoloEmbedder(len(classes), mode=mode)
    if fourier != 'learned':
        model.fourier.weight.requires_grad_(False)
        model.fourier.weight.copy_(physics_weights(model.fourier.q_values, fourier, distance_error=distance_error,
                                                   z=getattr(dataset, 'z0', None)))
    model.to(device)
    print(f'device {physical_gpu() or device}', flush=True)
    fparams = [p for n, p in model.named_parameters() if n.startswith('fourier.') and p.requires_grad]
    oparams = [p for n, p in model.named_parameters() if not n.startswith('fourier.')]
    groups_opt = [{'params': oparams, 'lr': lr}]
    if fparams:
        groups_opt.append({'params': fparams, 'lr': lr_fourier, 'weight_decay': 0.0})
    opt = torch.optim.AdamW(groups_opt, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=[g['lr'] for g in groups_opt], total_steps=steps,
                                                pct_start=0.1)
    supcon = SupConLoss(0.1)
    t0 = time.time()
    model.train()
    for step in range(steps):
        pick = [keys[i] for i in rng.choice(len(keys), imgs_per_step, replace=False)]
        rows = pd.concat([groups[k] for k in pick])
        bidx = np.concatenate([np.full(len(groups[k]), j) for j, k in enumerate(pick)])
        xyxy = rows[['x0', 'y0', 'x1', 'y1']].to_numpy()
        boxes = [torch.from_numpy(np.c_[bidx, square_boxes(xyxy, buffer, jitter, rng)]).float() for _ in range(2)]
        filt = model.filtered(torch.from_numpy(np.stack([load(k) for k in pick])))
        f = model.embed_boxes(filt, torch.cat(boxes))
        y = torch.from_numpy(np.array([remap[c] for c in rows.classe])).to(device)
        yy = torch.cat([y, y])
        loss = supcon(f, yy)
        if aux_weight > 0:
            logits = 30.0 * (f @ F.normalize(model.cls, dim=1).T) - 30.0 * 0.2 * F.one_hot(yy, len(classes))
            loss = loss + aux_weight * F.cross_entropy(logits, yy)
        opt.zero_grad()
        loss.backward()
        opt.step()
        sched.step()
        if step % 100 == 0 or step == steps - 1:
            log(f'step {step}/{steps} loss {loss.item():.4f} ({time.time() - t0:.0f}s)')
    model.cpu().eval()
    return model


def save_checkpoint(model, path, **meta):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    torch.save({'state_dict': model.state_dict(), 'meta': meta}, path)


__all__ = ['train', 'save_checkpoint', 'SupConLoss', 'CLASSES']
