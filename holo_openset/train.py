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
from holo_openset.sim.physics import PIXEL, WAVELENGTH, Z0
from holo_openset.model import IMAGE_SIZE, HoloEmbedder, physical_gpu, physics_weights, square_boxes


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


@torch.no_grad()
def calibrate_alpha(imgs_u8, device, lo=0.002, hi=0.08, n_coarse=79, n_fine=41):
    """The propagation phase alpha (units of the training grid) at which the holograms are sharpest, from the
    holograms alone: no label and no optical parameter. The sharpness is the Tamura coefficient of the gradient of the
    back-propagated field (the criterion of the blind autofocus), averaged over the images; coarse scan, then fine."""
    from holo_openset.reconstruct import tog
    x = imgs_u8.to(device).float() / 255.0
    x = x - x.mean(dim=(-2, -1), keepdim=True)
    h, w = x.shape[-2:]
    A = torch.fft.fft2(x.to(torch.complex64))
    fy = torch.fft.fftfreq(h, device=device, dtype=torch.float64) * IMAGE_SIZE
    fx = torch.fft.fftfreq(w, device=device, dtype=torch.float64) * IMAGE_SIZE
    q = fx[None, :] ** 2 + fy[:, None] ** 2

    def sharpness(alphas):
        return [tog(torch.fft.ifft2(A * torch.exp(1j * float(a) * q).to(torch.complex64))).mean().item()
                for a in alphas]
    coarse = np.linspace(lo, hi, n_coarse)
    c = coarse[int(np.argmax(sharpness(coarse)))]
    step = coarse[1] - coarse[0]
    fine = np.linspace(c - step, c + step, n_fine)
    return float(fine[int(np.argmax(sharpness(fine)))])


def train(dataset, classes, steps=3000, imgs_per_step=16, buffer=0.25, jitter=0.05, lr=3e-4, lr_fourier=3e-1,
          aux_weight=0.5, mode='radial', aux_scenes=None, threads=12, seed=0, fourier='learned', device='cpu', distance_error=0.0,
          n_dist=1, alpha_init='calib', lr_alpha=1e-5, log=print):
    """classes: list of letters to train on (the seen classes). aux_scenes: optional (images_npy, boxes_csv).
    fourier: 'learned' (default) or a deterministic-reconstruction baseline, 'fresnel' / 'wiener': the layer is
    set to the physical transfer function and frozen, so the embedding is trained on reconstructed images.
    Modes 'prop' and 'bank': alpha_init 'calib' calibrates the propagation phase on 32 training holograms
    (calibrate_alpha), a number sets it directly (0 = start from the identity); the bank spreads n_dist distances
    over +-5 % of it; lr_alpha is the learning rate of alpha."""
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

    model = HoloEmbedder(len(classes), mode=mode, n_dist=n_dist)
    if mode in ('prop', 'bank'):
        if alpha_init == 'calib':
            ids = rng.choice(np.unique(tr[tr.src == 'set'].image_id), 32, replace=False)
            a0 = calibrate_alpha(dataset.images(ids), device)
        else:
            a0 = float(alpha_init)
        k = model.fourier.alpha.numel()
        spread = torch.linspace(-0.05, 0.05, k, dtype=torch.float64) if k > 1 else torch.zeros(1, dtype=torch.float64)
        model.fourier.alpha.data = a0 * (1 + spread)
        log(f'alpha {a0:.6f} ({"calibrated on 32 training holograms" if alpha_init == "calib" else "given"}); '
            f'the bench would be {np.pi * WAVELENGTH * Z0 / (IMAGE_SIZE * PIXEL) ** 2:.6f}')
    if fourier != 'learned':
        model.fourier.weight.requires_grad_(False)
        model.fourier.weight.copy_(physics_weights(model.fourier.q_values, fourier, distance_error=distance_error,
                                                   z=getattr(dataset, 'z0', None)))
    model.to(device)
    print(f'device {physical_gpu() or device}', flush=True)
    fparams = [p for n, p in model.named_parameters() if n.startswith('fourier.') and p.requires_grad
               and not n.endswith('alpha')]
    aparams = [p for n, p in model.named_parameters() if n.endswith('fourier.alpha')]
    oparams = [p for n, p in model.named_parameters() if not n.startswith('fourier.')]
    groups_opt = [{'params': oparams, 'lr': lr}]
    if fparams:
        groups_opt.append({'params': fparams, 'lr': lr_fourier, 'weight_decay': 0.0})
    if aparams:
        groups_opt.append({'params': aparams, 'lr': lr_alpha, 'weight_decay': 0.0})
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
    if mode in ('prop', 'bank'):
        log('alpha after training ' + ' '.join(f'{v:.6f}' for v in model.fourier.alpha.detach().cpu().tolist()))
    model.cpu().eval()
    return model


def save_checkpoint(model, path, **meta):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    torch.save({'state_dict': model.state_dict(), 'meta': meta}, path)


__all__ = ['train', 'save_checkpoint', 'SupConLoss', 'CLASSES']
