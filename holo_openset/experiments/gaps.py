"""What the idealised model leaves out, measured on the scenes of the base test split (opaque letters in one plane,
as that model assumes, so that only the two simplifications differ):

  periodic   the hologram computed on a periodic field the size of the sensor against the same letters on a finite
             sensor inside a larger field: relative L2 difference of the recorded signal 2 Re(P_z s)
  |o|^2      a sensor records |1 + P_z s|^2 = 1 + 2 Re(P_z s) + |P_z s|^2; the idealised model keeps only the linear
             term: energy of |P_z s|^2 relative to that of 2 Re(P_z s)

    python -m holo_openset experiment gaps --device cuda:N [--n 100]
Output: results/holo_openset/gaps.json
"""
import json

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.experiments.common import device, parser
from holo_openset.sim.physics import IDEAL, Physics, propagate, scattered_field
from holo_openset.sim.scene import make_scene


def main(argv=None):
    ap = parser(__doc__)
    ap.add_argument('--n', type=int, default=100)
    a = ap.parse_args(argv)
    dev = device(a)
    cfg = json.load(open(paths.dataset(paths.BASE) / 'physics.json'))
    meta = pd.read_csv(paths.dataset(paths.BASE) / 'metadata.csv')
    ids = meta[meta.split == 'test'].image_id.to_numpy()[:a.n]
    finite = Physics().replace(**{**IDEAL, 'margin': 1728})
    periodic = Physics().replace(**IDEAL)
    per, quad = [], []
    for i in ids:
        out = {}
        for name, p in [('finite', finite), ('periodic', periodic)]:
            sc = make_scene(cfg['seed'] * 1_000_000 + int(i), p)
            s = scattered_field(sc['objects'], p.canvas, dev)
            ps = propagate(s, p.z0)
            m = p.margin
            ps = ps[m:m + p.window[0], m:m + p.window[1]]
            out[name] = ps
        lin_f, lin_p = 2 * out['finite'].real, 2 * out['periodic'].real
        per.append(float(torch.linalg.norm(lin_f - lin_p) / torch.linalg.norm(lin_f)))
        quad.append(float(torch.linalg.norm(out['finite'].abs() ** 2) / torch.linalg.norm(lin_f)))
    res = dict(n_scenes=len(ids), periodic_rel_diff_mean=float(np.mean(per)), periodic_rel_diff_std=float(np.std(per)),
               quadratic_rel_energy_mean=float(np.mean(quad)), quadratic_rel_energy_std=float(np.std(quad)))
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(paths.RESULTS / 'gaps.json', 'w'), indent=1)
    print(res)
