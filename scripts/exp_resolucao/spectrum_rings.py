"""The factor b blind, from the data (docs/exp_resolucao/PROTOCOLO.md, A.2.2; rule pre-registered in CADERNO.md, 13:11):
the ring-averaged power spectrum of I/B and of I on 256 TRAINING holograms of a set, its noise floor and the
frequency where the spectrum meets it.

  floor   median ring power over the top fifth of the rings up to Nyquist (k = 257..320 on the 640 grid)
  cut-off the lowest ring k_c above which every ring stays below k_thr x floor (k_thr = 2; 1.5 and 3 as sensitivity)
  b       floor(320 / k_c)

Writes $HOLO_RESULTS/spectrum_rings.csv (one row per set, signal and ring) and spectrum_cutoff.csv.

    python scripts/exp_resolucao/spectrum_rings.py [--sets realistic small_z0 small_near] [--device cuda:0]
"""
import argparse

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.sim.physics import PIXEL

N_IMAGES, SEED = 256, 0
K_THR, K_SENS = 2.0, (1.5, 2.0, 3.0)


def rings(n):
    k = np.fft.fftfreq(n, d=1.0 / n)
    r = np.rint(np.sqrt(k[None, :] ** 2 + k[:, None] ** 2)).astype(int)
    return r


def cutoff(power, k, k_thr):
    """power[k] for k = 1..K -> (floor, k_c)."""
    K = k.max()
    top = k > K - K // 5
    floor = float(np.median(power[top]))
    above = np.where(power >= k_thr * floor)[0]
    k_c = int(k[above[-1]]) + 1 if len(above) else int(k[0])   # K + 1: the spectrum never meets the floor
    return floor, k_c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sets', nargs='+', default=['realistic', 'small_z0', 'small_near'])
    ap.add_argument('--device', default='cpu')
    a = ap.parse_args()
    torch.set_num_threads(4)
    dev = torch.device(a.device)
    rows, cuts = [], []
    for s in a.sets:
        root = paths.dataset(s)
        meta = pd.read_csv(root / 'metadata.csv')
        holo = np.load(root / 'holograms.npy', mmap_mode='r')
        bg = np.load(root / 'backgrounds.npy', mmap_mode='r')
        row = {int(i): j for j, i in enumerate(meta.image_id)}
        ids = np.random.RandomState(SEED).choice(meta[meta.split == 'train'].image_id.to_numpy(), N_IMAGES,
                                                 replace=False)
        h, w = holo.shape[1:]
        assert h == w, 'square windows only'
        win = torch.from_numpy(np.outer(np.hanning(h), np.hanning(w))).to(dev)
        norm = float((win ** 2).sum())
        acc = {'I/B': torch.zeros(h, w, dtype=torch.float64, device=dev),
               'I': torch.zeros(h, w, dtype=torch.float64, device=dev)}
        session = dict(zip(meta.image_id, meta.session))
        for i in ids:
            x = torch.from_numpy(np.array(holo[row[int(i)]])).to(dev).double()
            b = torch.from_numpy(np.array(bg[session[int(i)]])).to(dev).double().clamp(min=1.0)
            for name, y in (('I/B', x / b), ('I', x)):
                y = (y - y.mean()) * win
                acc[name] += torch.fft.fft2(y).abs() ** 2 / norm
        r = rings(h)
        K = h // 2
        k = np.arange(1, K + 1)
        for name, p in acc.items():
            p = (p / len(ids)).cpu().numpy()
            power = np.array([p[r == kk].mean() for kk in k])
            for kk, v in zip(k, power):
                rows.append(dict(set=s, signal=name, k=int(kk), f_cyc_per_mm=kk / (h * PIXEL) / 1e3, power=v))
            for kt in K_SENS:
                floor, k_c = cutoff(power, k, kt)
                cuts.append(dict(set=s, signal=name, k_thr=kt, preregistered=kt == K_THR, floor=floor, k_c=k_c,
                                 f_c_cyc_per_mm=k_c / (h * PIXEL) / 1e3, b_blind=max(1, K // k_c),
                                 n_images=len(ids), image_ids_first=','.join(map(str, ids[:5]))))
        print(s, 'done', flush=True)
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(paths.RESULTS / 'spectrum_rings.csv', index=False, float_format='%.6g')
    t = pd.DataFrame(cuts)
    t.to_csv(paths.RESULTS / 'spectrum_cutoff.csv', index=False, float_format='%.6g')
    pd.set_option('display.width', 250)
    print(t.drop(columns='image_ids_first').to_string(index=False))


if __name__ == '__main__':
    main()
