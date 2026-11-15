"""The alpha of the propagation layer (prop) of the standard 1 mm family (curve_u50_L*), per set and repetition, as
scripts/exp_resolucao/pilot_five_reps.py writes it for the pilot (pilot_five_reps_alpha.csv), with the same code:
  alpha_calibrated   train.calibrate_alpha on the same 32 training holograms that train() drew (RandomState(0) over the
                     training images with seen classes of the repetition), recomputed here on the CPU, grid extended
                     12 steps (--alpha-extend 12 of the trainings)
  alpha_trained      fourier.alpha of the checkpoint models_exp_resolucao/<set>/prop_r<rep>.pt
  z_*_mm             alpha (640 x 1.67 um)^2 / (pi 385 nm) (pilot_five_reps.mm); change = trained / calibrated - 1
One row per set and repetition whose prop checkpoint exists. No test split is read.
-> $HOLO_RESULTS/curve_alpha.csv
    python scripts/exp_resolucao/curve_alpha.py
"""
import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.flows import dataset
from holo_openset.protocol import classes
from holo_openset.train import calibrate_alpha

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pilot_five_reps import mm   # noqa: E402  (the same conversion as the pilot's table)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--extend', type=int, default=12)
    a = ap.parse_args()
    torch.set_num_threads(4)
    rows = []
    for root in sorted(glob.glob(str(paths.DATA / 'curve_u50_L*'))):
        s = Path(root).name
        level = int(s.rsplit('_L', 1)[1])
        reps = [r for r in range(1, 6) if paths.weights('prop', r, s).exists()]
        if not reps:
            continue
        ds = dataset('prop', paths.dataset(s))
        ann = ds.ann
        for r in reps:
            seen = classes(r)[0]
            tr = ann[(ann.split == 'train') & ann.classe.isin(seen)]
            ids = np.random.RandomState(0).choice(np.unique(tr.image_id), 32, replace=False)   # as train() draws them
            a0 = calibrate_alpha(ds.images(ids), 'cpu', extend=a.extend)
            ck = torch.load(paths.weights('prop', r, s), map_location='cpu', weights_only=False)
            a1 = float(ck['state_dict']['fourier.alpha'].mean())
            rows.append(dict(set=s, level=level, rep=r, alpha_calibrated=a0, z_calibrated_mm=mm(a0), alpha_trained=a1,
                             z_trained_mm=mm(a1), change=a1 / a0 - 1))
            print(rows[-1], flush=True)
    t = pd.DataFrame(rows)
    t.to_csv(paths.RESULTS / 'curve_alpha.csv', index=False, float_format='%.7g')
    print(t.to_string(index=False))


if __name__ == '__main__':
    main()
