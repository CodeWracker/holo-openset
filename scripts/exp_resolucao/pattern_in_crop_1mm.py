"""R5 (i) of the pilot at 1.0 mm: how much of the pattern of one letter leaks out of its crop at the letter sizes of
the new set, with the oversampled recorder. Same definition as pattern_in_crop.py (fig_fresnel (c)): one absorbing
letter (a = 0.6, no phase, depth 0) at the centre of the window (no dust, no noise, the source of the set: 7
wavelengths of the 10 nm band, the 100 um pinhole at 15 cm, the pixel), pattern energy e = (I - 1)^2, share = energy
inside a square of side `side` x 1.25 centred on the window over the energy in the whole window. Letters F, A, O, W
(DejaVuSans, upright), drawn on the master grid at the fractional font size whose ink side (max of width and height)
is the target. Targets: the ink side p5 / p50 / p95 of the set's annotations (bx0..by1); the crop is taken on the ink
side (as the old sets, whose boxes are the ink) and on the integer box side p5 / p50 / p95 (what the pipeline crops).
The recorder: physics of the set (oversample 4) with the window 1024 x 1024, margin 512 (the share is also given for a
512 window, to show the window is large enough).
-> $HOLO_RESULTS/pattern_in_crop_<set>.csv (one row per size, letter, z, window) and _summary.csv

    python scripts/exp_resolucao/pattern_in_crop_1mm.py --set bench_1mm --device cuda:N
"""
import argparse
import json

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.model import pick_device
from holo_openset.sim.letters import FONTS, letter_master
from holo_openset.sim.physics import PIXEL, WAVELENGTH, physics_from_dict, sensor_intensity
from holo_openset.sim.scene import FresnelLayout, physical_object

LETTERS = ['F', 'A', 'O', 'W']
F = FresnelLayout.factor


def master_of_side(letter, side):
    """The master raster of the letter whose ink side is `side` px (bisection on the fractional font size)."""
    lo, hi = 2.0, 4 * side
    for _ in range(40):
        fs = (lo + hi) / 2
        m = letter_master(letter, FONTS[0], fs * F, 0.0)
        if max(m.shape) / F < side:
            lo = fs
        else:
            hi = fs
    m = letter_master(letter, FONTS[0], hi * F, 0.0)
    return hi, m


def share(img, side, margin=0.25):
    e = (img - 1) ** 2
    c = img.shape[0] / 2
    a, b = int(c - side * (1 + margin) / 2), int(c + side * (1 + margin) / 2)
    return float(e[a:b, a:b].sum() / e.sum())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--set', default='bench_1mm')
    ap.add_argument('--z', type=float, nargs='+', default=[1.0, 0.7], help='mm')
    ap.add_argument('--windows', type=int, nargs='+', default=[1024, 512])
    ap.add_argument('--device', default='cpu')
    a = ap.parse_args()
    torch.set_num_threads(4)
    dev = pick_device(a.device)
    root = paths.dataset(a.set)
    phys0 = physics_from_dict(json.load(open(root / 'physics.json'))['physics'])
    ann = pd.read_csv(root / 'annotations.csv')
    ink = np.percentile(np.maximum(ann.bx1 - ann.bx0, ann.by1 - ann.by0), [5, 50, 95])
    box = np.percentile(np.maximum(ann.x1 - ann.x0, ann.y1 - ann.y0), [5, 50, 95])
    rows = []
    for label, side_ink, side_box in zip(['p5', 'p50', 'p95'], ink, box):
        for letter in LETTERS:
            fs, m = master_of_side(letter, side_ink)
            s_ink = max(m.shape) / F
            for zmm in a.z:
                for win in a.windows:
                    p = phys0.replace(window=(win, win), margin=win // 2, reach=0, z0=zmm * 1e-3, dust_density=0.0,
                                      sensor_dust_density=0.0)
                    c = (p.margin + win / 2) * F   # the centre of the window on the master grid
                    o = physical_object(m, round(c - m.shape[1] / 2), round(c - m.shape[0] / 2), F, absorption=0.6,
                                        phase=0.0, depth=0.0, kind='letter')
                    img = sensor_intensity(dict(objects=[o], dust=[], sensor_dust=[]), dict(z=zmm * 1e-3), p,
                                           dev).cpu().numpy()
                    rows.append(dict(set=a.set, size=label, letter=letter, font_size=fs, ink_side_px=s_ink,
                                     box_side_px=float(side_box), z_mm=zmm, window=win, oversample=p.oversample,
                                     fresnel_number=(s_ink * PIXEL / 2) ** 2 / (WAVELENGTH * zmm * 1e-3),
                                     share_in_crop_ink=share(img, s_ink), share_in_crop_box=share(img, side_box),
                                     share_in_box_ink=share(img, s_ink, 0.0)))
                    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)
    t = pd.DataFrame(rows)
    t['outside_crop_ink'] = 1 - t.share_in_crop_ink
    t['outside_crop_box'] = 1 - t.share_in_crop_box
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    t.to_csv(paths.RESULTS / f'pattern_in_crop_{a.set}.csv', index=False, float_format='%.5g')
    g = t.groupby(['z_mm', 'window', 'size'], sort=False).agg(
        ink_side_px=('ink_side_px', 'mean'), box_side_px=('box_side_px', 'first'), fresnel=('fresnel_number', 'mean'),
        outside_crop_ink=('outside_crop_ink', 'mean'), outside_ink_min=('outside_crop_ink', 'min'),
        outside_ink_max=('outside_crop_ink', 'max'), outside_crop_box=('outside_crop_box', 'mean')).reset_index()
    g.to_csv(paths.RESULTS / f'pattern_in_crop_{a.set}_summary.csv', index=False, float_format='%.4g')
    print(g.round(4).to_string(index=False))


if __name__ == '__main__':
    main()
