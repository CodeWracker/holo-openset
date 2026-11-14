"""Sanity (b) of T3: the label-free calibration of the propagation phase (train.calibrate_alpha) on the SAME 32 training
holograms that `train --flow prop --rep 1` draws (seed 0), at every b. alpha = pi lambda z / (N pixel)^2 and N pixel
is the same field at every b, so the four values must agree. Writes $HOLO_RESULTS/alpha_b.csv.

    python scripts/exp_resolucao/alpha_b.py --device cuda:N [--bins 1 2 4 8]
"""
import argparse
import time

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.data import Dataset
from holo_openset.model import IMAGE_SIZE, load_model, pick_device
from holo_openset.protocol import classes
from holo_openset.resolution import grid_size
from holo_openset.sim.physics import PIXEL, WAVELENGTH, Z0
from holo_openset.train import calibrate_alpha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--bins', type=int, nargs='+', default=[1, 2, 4, 8])
    a = ap.parse_args()
    torch.set_num_threads(4)
    dev = pick_device(a.device)
    bench = np.pi * WAVELENGTH * Z0 / (IMAGE_SIZE * PIXEL) ** 2
    paper = float(load_model(paths.PROJECT / 'models' / 'realistic' / 'prop_r1.pt')[0].fourier.alpha.item())
    rows = []
    for b in a.bins:
        ds = Dataset(paths.dataset('realistic' if b == 1 else f'realistic_b{b}'))
        seen = classes(1)[0]
        tr = ds.ann[(ds.ann.split == 'train') & ds.ann.classe.isin(seen)]
        ids = np.random.RandomState(0).choice(np.unique(tr.image_id), 32, replace=False)   # as train() draws them
        imgs = ds.images(ids)
        t0 = time.time()
        alpha = calibrate_alpha(imgs, dev, size=grid_size(ds.pixel, IMAGE_SIZE))
        rows.append(dict(b=b, image_side=imgs.shape[-1], pixel_um=ds.pixel * 1e6, grid=grid_size(ds.pixel, IMAGE_SIZE),
                         alpha=alpha, alpha_bench=bench, alpha_paper_prop_r1_trained=paper,
                         z_implied_mm=alpha / bench * Z0 * 1e3, seconds=time.time() - t0,
                         ids_first=','.join(map(str, ids[:5]))))
        print(rows[-1], flush=True)
    t = pd.DataFrame(rows)
    t['rel_to_b1'] = t.alpha / t.alpha[t.b == 1].iloc[0] - 1 if (t.b == 1).any() else np.nan
    t['rel_to_bench'] = t.alpha / bench - 1
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    t.to_csv(paths.RESULTS / 'alpha_b.csv', index=False, float_format='%.8g')
    print(t.drop(columns='ids_first').to_string(index=False))


if __name__ == '__main__':
    main()
