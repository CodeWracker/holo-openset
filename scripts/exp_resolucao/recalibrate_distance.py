"""P0 (b) of the pilot at 1.0 mm (docs/exp_resolucao/CADERNO_PILOTO_1MM.md): the front end recalibrated without labels
for holograms recorded at another distance. The calibration the method already has (train.calibrate_alpha: the alpha
at which the back-propagated holograms are sharpest, Tamura coefficient of the gradient) runs on `--n` holograms of
the validation split recorded at the new distance (no label is read), on its grid extended `--extend` steps below
0.944 mm with the same relative step. The alpha is the phase of the propagation layer ('prop') and gives the distance
of the back-propagation of 'rec_z0':  z = alpha (640 x 1.67 um)^2 / (pi lambda).
The same calibration on the same image ids of the reference set (`--ref`, recorded at the distance the models were
trained at) is written alongside, for the record (it is not used).

    python scripts/exp_resolucao/recalibrate_distance.py --set bench_1mm_robust/z07_val --ref bench_1mm \
        --out $HOLO_RESULTS/recal_bench_1mm_z07.json --device cuda:N
    python scripts/exp_resolucao/recalibrate_distance.py --read FILE z      # prints a value of the file (for shell)
Then:  reconstruct --set <test set at the new distance> --methods z0 --z0 <z> --tag _recal
       experiment robustness ... --alpha-json FILE --rec-tag _recal
"""
import argparse
import json
import math
import sys

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.data import Dataset
from holo_openset.model import IMAGE_SIZE, pick_device
from holo_openset.sim.physics import PIXEL, WAVELENGTH
from holo_openset.train import calibrate_alpha


def z_of(alpha):
    return alpha * (IMAGE_SIZE * PIXEL) ** 2 / (math.pi * WAVELENGTH)


def main():
    if len(sys.argv) == 4 and sys.argv[1] == '--read':
        print(json.load(open(sys.argv[2]))[sys.argv[3]])
        return
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--set', required=True, help='the validation split recorded at the new distance (data/<set>)')
    ap.add_argument('--ref', help='the set the models were trained on (same image ids, its validation split)')
    ap.add_argument('--n', type=int, default=32)
    ap.add_argument('--extend', type=int, default=12, help='steps of the grid below 0.944 mm (12: down to 0.485 mm)')
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    torch.set_num_threads(4)
    dev = pick_device(a.device)
    root = paths.dataset(a.set)
    meta = pd.read_csv(root / 'metadata.csv')
    ids = np.sort(np.random.RandomState(a.seed).choice(meta[meta.split == 'val'].image_id.to_numpy(), a.n,
                                                       replace=False))
    ds = Dataset(root)
    alpha = calibrate_alpha(ds.images(ids), dev, extend=a.extend)
    out = dict(set=a.set, split='val', image_ids=[int(i) for i in ids], n=a.n, extend=a.extend, alpha=alpha,
               z=z_of(alpha), nominal_z0_of_set=ds.z0)
    if a.ref:
        ref = Dataset(paths.dataset(a.ref))
        alpha_ref = calibrate_alpha(ref.images(ids), dev, extend=a.extend)
        out.update(ref=a.ref, alpha_ref=alpha_ref, z_ref=z_of(alpha_ref), nominal_z0_of_ref=ref.z0)
    json.dump(out, open(a.out, 'w'), indent=1)
    print({k: v for k, v in out.items() if k != 'image_ids'})


if __name__ == '__main__':
    main()
