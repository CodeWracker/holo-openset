"""Time of every stage, from a 640 x 640 window to a full frame of the sensor, on one CPU core and on one GPU.

The images are regions of the simulated full frames (real content, real boxes), of growing size; at the full frame
size, the frame itself. Each stage is timed alone, after warm-up:
  CPU: CPU time of the process with one intra-op thread (time.process_time) -- the cost on one core, unaffected by the
       load of a shared server; GPU: wall clock with the device synchronised before and after (the minimum over the
       repetitions is the estimate for an idle device, the median is also kept).
Stages: flat field, learned layer (real; one transform pair, inference path), complex layer, one back-propagation,
blind autofocus (114 reconstructions), per-object focus (25 more), twin-image removal (50 passes), channels of the
network input, YOLO in tiles, ResNet18 embedding of the boxes, gallery search (5k gallery). Nothing is extrapolated.

    python -m holo_openset experiment timing --device cpu      (one core)
    python -m holo_openset experiment timing --device cuda:N
Output: results/holo_openset/timing.csv
"""
import time

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.detect import YoloDetector
from holo_openset.experiments.common import device, model, parser, save
from holo_openset.experiments.full_frames import embed_boxes
from holo_openset.reconstruct import Holograms, autofocus, backprop, channels, per_object, remove_twin

SIZES = [(640, 640), (1280, 1280), (2048, 2048), (2748, 3840)]


def measure(fn, dev, n, warm=1):
    for _ in range(warm):
        fn()
    out = []
    for _ in range(n):
        if dev.type == 'cuda':
            torch.cuda.synchronize(dev)
            t0 = time.perf_counter()
            fn()
            torch.cuda.synchronize(dev)
            out.append(time.perf_counter() - t0)
        else:
            t0 = time.process_time()
            fn()
            out.append(time.process_time() - t0)
    return out


def main(argv=None):
    ap = parser(__doc__)
    ap.add_argument('--n', type=int, default=None, help='repetitions per stage (default: 20 GPU, 5 CPU, 2 for the '
                                                        'iterative stages on the CPU above 1 MP)')
    ap.add_argument('--sizes', nargs='+', default=None, help='HxW')
    ap.add_argument('--stages', nargs='+', default=None, help='only these stages (default: all)')
    a = ap.parse_args(argv)
    a.threads = 1 if a.device == 'cpu' else a.threads
    dev = device(a)
    rep = a.rep[0]
    src = Holograms(paths.dataset('full_frames'))
    ann = pd.read_csv(paths.dataset('full_frames') / 'annotations.csv')
    i = int(src.ids[0])
    full = torch.from_numpy(np.array(src.holo[src.row[i]])).to(dev)
    bg = torch.from_numpy(np.array(src.bg[src.session[i]])).to(dev)
    m_learned, m_complex, m_raw = model('learned', rep, dev), model('complex', rep, dev), model('rec_z0', rep, dev)
    extra = {f'layer_{f}': model(f, rep, dev) for f in ('prop', 'bank', 'bank_w1', 'bank_w3')}   # exploration flows, when trained
    extra = {k: m for k, m in extra.items() if m is not None}
    yolo = YoloDetector(paths.yolo_weights(rep), device=dev)
    gal = torch.nn.functional.normalize(torch.randn(5000, 128, device=dev), dim=1)
    sizes = [tuple(int(v) for v in s.split('x')) for s in a.sizes] if a.sizes else SIZES
    rows = []
    for h, w in sizes:
        holo, b = full[:h, :w].contiguous(), bg[:h, :w].contiguous()
        g = ann[(ann.image_id == i) & (ann.x1 <= w) & (ann.y1 <= h)][['x0', 'y0', 'x1', 'y1']].to_numpy(float)
        from holo_openset.reconstruct import normalise
        amp = normalise(holo, b)
        z = autofocus(amp, src.z0)[0]
        u = backprop(amp, [z])[0]
        x3 = channels(u)
        big = h * w > 1.5e6
        n = a.n or (20 if dev.type == 'cuda' else 5)
        n_iter = a.n or (20 if dev.type == 'cuda' else (2 if big else 5))
        with torch.no_grad():
            filt = m_raw.filtered(x3[None])
            e = torch.from_numpy(embed_boxes(m_raw, filt, g)).to(dev)
            stages = {
                'flat_field': (lambda: normalise(holo, b), n),
                'layer_real': (lambda: m_learned.filtered(holo[None]), n),
                'layer_complex': (lambda: m_complex.filtered(holo[None]), n),
                **{k: (lambda m=m: m.filtered(holo[None]), n) for k, m in extra.items()},
                'backprop': (lambda: backprop(amp, [z]), n),
                'autofocus': (lambda: autofocus(amp, src.z0), n_iter),
                'per_object': (lambda: per_object(amp, z, g), n_iter),
                'twin': (lambda: remove_twin(amp, z), n_iter),
                'channels': (lambda: channels(u), n),
                'yolo_tiled': (lambda: yolo(holo.cpu().numpy()), n),
                'embed': (lambda: embed_boxes(m_raw, filt, g), n),
                'decide': (lambda: (e @ gal.T).max(1), n),
            }
            for name, (fn, k) in stages.items():
                if a.stages and name not in a.stages:
                    continue
                t = measure(fn, dev, k)
                rows.append(dict(device='gpu' if dev.type == 'cuda' else 'cpu', height=h, width=w, megapixels=h * w / 1e6,
                                 area_mm2=h * w * 1.67e-3 ** 2, n_boxes=len(g), stage=name, n=k,
                                 median_s=float(np.median(t)), min_s=float(np.min(t))))
                print(h, w, name, f'{np.median(t):.4f} s', flush=True)
        save(rows, f'timing_{"gpu" if dev.type == "cuda" else "cpu"}', keys=['height', 'width', 'stage'])
