"""Model: learnable Fourier layer on the full hologram + ResNet18 embedding of each pattern crop.

The Fourier layer computes   y = IFFT( FFT(x) * W[q(kx, ky)] )   with q = kx^2 + ky^2 the squared radial frequency
index on the 640 x 640 training grid, i.e. ONE learnable real weight per discrete radius (isotropic filter). It is
initialised to W = 1 (identity), so the network starts by looking at the raw hologram. On an image of another size
(a full sensor frame) the same filter is applied at the same PHYSICAL frequencies: W is interpolated at
q' = (640 f_x)^2 + (640 f_y)^2, f in cycles per pixel -- still one transform pair on the whole image.
"""
import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
from torchvision.ops import roi_align

IMAGE_SIZE = 640

from holo_openset.spectrum import fast_pad
from holo_openset.sim.physics import PIXEL, WAVELENGTH, Z0


def physics_weights(q_values, kind, size=IMAGE_SIZE, eps=0.02, distance_error=0.0, z=None):
    """Fixed radial transfer function of a deterministic reconstruction, on the bins q = kx^2 + ky^2 of the layer.
    These use the optical parameters (wavelength, distance, pixel pitch); the learned layer never sees them.

    The linear part of an in-line hologram is the object filtered by C = cos(pi lambda z (u^2 + v^2)), with
    u^2 + v^2 = q / (size * pixel)^2.
      'fresnel'   W = C               real part of the back-propagation: refocused object plus its defocused twin
      'wiener'    W = C / (C^2 + eps) regularised inverse of the absorption part
    distance_error: relative error of the propagation distance given to the reconstruction (0.05 = 5 % too long).
    """
    c = torch.cos(np.pi * WAVELENGTH * (z or Z0) * (1 + distance_error) * q_values.double() / (size * PIXEL) ** 2)
    if kind == 'fresnel':
        return c.float()
    if kind == 'wiener':
        return (c / (c * c + eps)).float()
    raise ValueError(kind)


class FourierLayer(nn.Module):
    """mode 'radial': one real weight per radius, one output channel. 'complex': one COMPLEX weight per radius
    (W_re + i W_im, initialised to 1 + 0i); the output is the complex filtered hologram as three channels, real part,
    imaginary part and modulus -- the form of a numerical back-propagation, exp(+i pi lambda z |f|^2) = cos + i sin,
    which an intensity hologram of objects that absorb AND delay the light needs (one real filter can only invert
    one of the two). 'none': identity; a multi-channel input (e.g. a reconstruction cache) passes through.

    'prop': the gain per radius of 'radial' times the PHASE of a free-space propagation, exp(+i alpha q), with
    alpha ONE learnable scalar in units of the training grid (alpha = pi lambda z / (N pixel)^2 for a distance z: the
    optical parameters are never given, alpha is found from the holograms). 'bank': the same at n_dist distances
    around alpha, a focal stack of 3 x n_dist channels for objects at different depths and sessions at different
    distances, without an autofocus per hologram."""

    def __init__(self, size=IMAGE_SIZE, mode='radial', n_dist=1):
        super().__init__()
        self.mode = mode
        if mode in ('radial', 'complex', 'prop', 'bank'):
            k = np.fft.fftfreq(size, d=1.0 / size).astype(np.int64)
            q = k[None, :] ** 2 + k[:, None] ** 2
            uniq, inv = np.unique(q, return_inverse=True)
            self.register_buffer('inv', torch.from_numpy(inv.reshape(size, size)))
            self.register_buffer('q_values', torch.from_numpy(uniq))
            self.weight = nn.Parameter(torch.ones(len(uniq)))
            if mode == 'complex':
                self.weight_im = nn.Parameter(torch.zeros(len(uniq)))
            if mode in ('prop', 'bank'):
                self.alpha = nn.Parameter(torch.zeros(n_dist if mode == 'bank' else 1, dtype=torch.float64))
                self.alpha_scale = 1.0   # training-time jitter of the distance (not a parameter, not saved)
        elif mode == 'none':
            self.register_buffer('weight', torch.ones(1))
        else:
            raise ValueError(mode)

    @property
    def out_channels(self):
        if self.mode in ('prop', 'bank'):
            return 3 * self.alpha.numel()
        return {'none': None, 'radial': 1, 'complex': 3}[self.mode]

    def grid_q(self, shape):
        """q = kx^2 + ky^2 of an image of `shape`, in units of the training grid (float64 [H, W])."""
        size = self.inv.shape[-1]
        if tuple(shape) == (size, size):
            return self.q_values.double()[self.inv]
        fy = torch.fft.fftfreq(shape[0], device=self.inv.device, dtype=torch.float64) * size
        fx = torch.fft.fftfreq(shape[1], device=self.inv.device, dtype=torch.float64) * size
        return fx[None, :] ** 2 + fy[:, None] ** 2

    def _resampled(self, w, shape):
        """Weights w (one per bin of q_values) evaluated at the physical frequencies of an image of `shape`."""
        q = self.grid_q(shape).flatten()
        qv = self.q_values.double()
        j = torch.searchsorted(qv, q).clamp(1, len(qv) - 1)
        t = ((q - qv[j - 1]) / (qv[j] - qv[j - 1])).clamp(0, 1).to(w.dtype)
        return (w[j - 1] * (1 - t) + w[j] * t).reshape(shape)

    def transfer(self, shape=None):
        """The 2-D transfer function W[q(kx, ky)] (layout of torch.fft.fft2) on the training grid, or resampled to an
        image of `shape`; complex in mode 'complex'."""
        if self.mode == 'none':
            return None
        size = self.inv.shape[-1]
        if shape is None or tuple(shape) == (size, size):
            re = self.weight[self.inv]
            im = self.weight_im[self.inv] if self.mode == 'complex' else None
        else:
            re = self._resampled(self.weight, shape)
            im = self._resampled(self.weight_im, shape) if self.mode == 'complex' else None
        if self.mode in ('prop', 'bank'):   # [K, H, W]: the gain times the phase of each distance
            phase = (self.alpha * self.alpha_scale)[:, None, None] * self.grid_q(shape if shape is not None
                                                                                 else (size, size))[None]
            return (re.double()[None] * torch.exp(1j * phase)).to(torch.complex64)
        return re if im is None else torch.complex(re, im)

    def forward(self, x):  # [B, H, W] -> [B, 1, H, W]   ('complex': [B, 3, H, W]; 'none' keeps [B, C, H, W])
        if self.mode == 'none':
            return x.unsqueeze(1) if x.dim() == 3 else x
        h, w = x.shape[-2:]
        x = fast_pad(x)
        shape = tuple(x.shape[-2:])
        if self.training:
            t = self.transfer(shape)
        else:  # cached until the weights change
            key = (tuple(p._version for p in self.parameters()), getattr(self, 'alpha_scale', 1.0), shape,
                   str(x.device))
            if getattr(self, '_key', None) != key:
                self._t = self.transfer(shape).detach()
                self._key = key
            t = self._t
        if self.mode in ('prop', 'bank'):
            y = torch.fft.ifft2(torch.fft.fft2(x)[:, None] * t[None])            # [B, K, H, W]
            y = torch.stack([y.real, y.imag, torch.sqrt(y.real ** 2 + y.imag ** 2 + 1e-12)], 2)
            return y.flatten(1, 2)[..., :h, :w]                                   # re, im, |.| of each distance
        if self.mode == 'complex':
            y = torch.fft.ifft2(torch.fft.fft2(x) * t)
            return torch.stack([y.real, y.imag, torch.sqrt(y.real ** 2 + y.imag ** 2 + 1e-12)], 1)[..., :h, :w]
        if self.training:
            return torch.fft.ifft2(torch.fft.fft2(x) * t).real.unsqueeze(1)[..., :h, :w]
        # Inference: x is real and W[q(k)] = W[q(-k)], so the real FFT gives exactly the same result on half the
        # spectrum.
        return torch.fft.irfft2(torch.fft.rfft2(x) * t[:, :shape[1] // 2 + 1], s=shape).unsqueeze(1)[..., :h, :w]


class HoloEmbedder(nn.Module):
    def __init__(self, n_classes, mode='radial', crop=64, proj_dim=128, pretrained=True, n_dist=1):
        super().__init__()
        self.fourier = FourierLayer(IMAGE_SIZE, mode, n_dist)
        self.crop = crop
        m = torchvision.models.resnet18(weights='IMAGENET1K_V1' if pretrained else None)
        m.fc = nn.Identity()
        cin = self.fourier.out_channels or 3
        if cin not in (1, 3):   # a focal stack: the first convolution takes every triplet like the RGB of ImageNet
            conv = nn.Conv2d(cin, 64, 7, 2, 3, bias=False)
            conv.weight.data = m.conv1.weight.data.repeat(1, cin // 3, 1, 1) / (cin // 3)
            m.conv1 = conv
        self.backbone = m
        self.proj = nn.Sequential(nn.Linear(512, 512), nn.BatchNorm1d(512), nn.ReLU(), nn.Linear(512, proj_dim))
        self.cls = nn.Parameter(torch.randn(n_classes, proj_dim) * 0.01)  # CosFace proxies (training only)

    def filtered(self, imgs_u8):
        """imgs_u8: uint8 tensor [B, H, W] (or [B, C, H, W] with mode 'none') -> filtered images [B, C', H, W]."""
        x = imgs_u8.to(self.cls.device).float() / 255.0
        x = x - x.mean(dim=(-2, -1), keepdim=True)
        return self.fourier(x)

    def embed_boxes(self, filt, boxes):
        """filt [B,1,H,W]; boxes float [N,5] = (batch_index, x0, y0, x1, y1) -> L2-normalised embeddings [N,128]."""
        c = roi_align(filt, boxes.to(filt.device), output_size=self.crop, spatial_scale=1.0, sampling_ratio=2, aligned=True)
        c = (c - c.mean(dim=(2, 3), keepdim=True)) / (c.std(dim=(2, 3), keepdim=True) + 1e-6)
        return F.normalize(self.proj(self.backbone(c.expand(-1, 3, -1, -1) if c.shape[1] == 1 else c)), dim=1)

    def forward(self, imgs_u8, boxes):
        return self.embed_boxes(self.filtered(imgs_u8), boxes)


def square_boxes(xyxy, buffer=0.25, jitter=0.0, rng=None):
    """Square crop boxes around detections: side = max(w, h) * (1 + buffer), optional random jitter."""
    xyxy = np.asarray(xyxy, dtype=np.float64).reshape(-1, 4)
    x0, y0, x1, y1 = xyxy.T
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    side = np.maximum(x1 - x0, y1 - y0) * (1 + buffer)
    if jitter > 0:
        n = len(cx)
        cx = cx + rng.uniform(-jitter, jitter, n) * side
        cy = cy + rng.uniform(-jitter, jitter, n) * side
        side = side * rng.uniform(1 - jitter, 1 + jitter, n)
    return np.stack([cx - side / 2, cy - side / 2, cx + side / 2, cy + side / 2], 1)


_PICKED = {}  # the device of this process and the real index of its GPU: chosen once


def pick_device(name='auto'):
    """'cpu', 'cuda:N', or 'auto' / 'cuda' (the first GPU when CUDA is available, else the CPU).

    ONE GPU per process. The chosen GPU is selected by hiding the others (CUDA_VISIBLE_DEVICES) before CUDA starts, so
    it becomes cuda:0 of the process and no library can open a context on another GPU -- ultralytics, for one, maps
    any GPU index to "cuda:0" and would otherwise run the detector on a different GPU from the rest of the pipeline.
    `physical_gpu()` gives the real index of the GPU in use. Nothing here probes or spreads work over several GPUs."""
    name = str(name)
    if name == 'cpu':
        return torch.device('cpu')
    if _PICKED:
        return _PICKED['device']
    idx = int(name.split(':')[1]) if ':' in name else 0
    physical = str(idx)
    visible = os.environ.get('CUDA_VISIBLE_DEVICES')
    if not torch.cuda.is_initialized() and visible != '':
        ids = [v for v in visible.split(',') if v] if visible else None
        physical = ids[idx] if ids and idx < len(ids) else str(idx)
        os.environ['CUDA_VISIBLE_DEVICES'] = physical
    if not torch.cuda.is_available():  # (this call is also what makes CUDA read the variable set above)
        return torch.device('cpu') if name == 'auto' else torch.device(name)
    hidden = getattr(torch._C, '_cuda_getDeviceCount', torch.cuda.device_count)() == 1  # the others are really hidden
    _PICKED.update(device=torch.device('cuda:0' if hidden else f'cuda:{idx}'), physical=physical if hidden else str(idx),
                   visible=os.environ.get('CUDA_VISIBLE_DEVICES'))
    return _PICKED['device']


def physical_gpu():
    """'cuda:N' with the real index of the GPU picked by `pick_device` (None on the CPU)."""
    return f"cuda:{_PICKED['physical']}" if _PICKED else None


def device_env():
    """Environment for child processes: the same single GPU (libraries may have rewritten CUDA_VISIBLE_DEVICES)."""
    env = dict(os.environ)
    if _PICKED and _PICKED['visible'] is not None:
        env['CUDA_VISIBLE_DEVICES'] = _PICKED['visible']
    return env


def load_model(path, device='cpu'):
    """Load a checkpoint saved by `holo_openset train` (dict with 'state_dict' and 'meta')."""
    ck = torch.load(path, map_location=device, weights_only=False)
    meta = {}
    if isinstance(ck, dict) and 'state_dict' in ck:
        meta, state = ck.get('meta', {}), ck['state_dict']
    else:
        state = ck
    n_classes = state['cls'].shape[0]
    n_dist = state['fourier.alpha'].numel() if 'fourier.alpha' in state else 1
    mode = ('bank' if n_dist > 1 else 'prop') if 'fourier.alpha' in state else \
        'complex' if 'fourier.weight_im' in state else 'radial' if 'fourier.inv' in state else 'none'
    model = HoloEmbedder(n_classes, mode=mode, pretrained=False, n_dist=n_dist)
    model.load_state_dict(state)
    model.to(device).eval()
    return model, meta
