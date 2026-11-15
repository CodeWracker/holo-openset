"""How many letters the scene generator places at a density level (Q2/Q3-L of docs/exp_resolucao/CADERNO_CURVA.md):
the test of results_exp_resolucao/curve_feasibility_343.csv (CADERNO_CURVA_DENSIDADE.md, D1) at other levels, on the
same 20 scenes (images 0, 263, ..., 4999 of a set with seed 17), the physics of bench_1mm with the depth spread of
that test (50 / 150 um: the depths do not move the placement), the layout of bench_1mm with fill_mean = level. No
hologram is recorded. Per scene: the fillers asked (window, band), placed, skipped, the letters per window obtained,
the covered area (sum of the ink boxes of the letters in the window / window area, the measure of K2) and the seconds
of the scene (one process).
    python scripts/exp_resolucao/curve_feasibility.py --levels 514 771 --out curve_feasibility_dense.csv
"""
import argparse
import json
import time

import numpy as np
import pandas as pd

from holo_openset import paths
from holo_openset.sim.generate import make_layout
from holo_openset.sim.physics import physics_from_dict
from holo_openset.sim.scene import make_scene


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--levels', type=float, nargs='+', required=True)
    ap.add_argument('--n', type=int, default=20)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    cfg = json.load(open(paths.dataset('bench_1mm') / 'physics.json'))
    phys = physics_from_dict(cfg['physics']).replace(depth_std=50e-6, depth_max=150e-6)
    m0, (h, w) = phys.margin, phys.window
    rows = []
    for lvl in a.levels:
        lay = make_layout('fresnel', dict(cfg['layout_params'], fill_mean=lvl))
        for i in np.linspace(0, 4999, a.n).astype(int):
            t = time.time()
            sc = make_scene(17_000_000 + int(i), phys, lay=lay)
            dt = time.time() - t
            f = sc['fill']
            area = 0.0
            for o in sc['objects']:
                if o['kind'] not in ('letter', 'filler'):
                    continue
                x0, y0 = o['mx'] / lay.factor - m0, o['my'] / lay.factor - m0
                x1, y1 = x0 + o['master'].shape[1] / lay.factor, y0 + o['master'].shape[0] / lay.factor
                if x0 >= 0 and y0 >= 0 and x1 <= w and y1 <= h:
                    area += (x1 - x0) * (y1 - y0)
            rows.append(dict(level=lvl, image_id=int(i), seconds=dt, annotated=len(sc['rows']), **f,
                             skipped=f['target_window'] + f['target_band'] - f['placed_window'] - f['placed_band'],
                             skipped_window=f['target_window'] - f['placed_window'],
                             per_window=len(sc['rows']) + f['placed_window'],
                             asked_per_window=len(sc['rows']) + f['target_window'], covered=area / (h * w)))
            print(rows[-1], flush=True)
    t = pd.DataFrame(rows)
    t.to_csv(paths.RESULTS / a.out, index=False, float_format='%.6g')
    print(t.groupby('level')[['seconds', 'asked_per_window', 'per_window', 'skipped_window', 'skipped', 'covered',
                              'target_band', 'placed_band']].agg(['mean', 'min', 'max']).T.to_string())


if __name__ == '__main__':
    main()
