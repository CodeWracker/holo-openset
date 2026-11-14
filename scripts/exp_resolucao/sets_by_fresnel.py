"""R5 (ii) of the pilot at 1.0 mm: the sets by Fresnel number, N_F = (max box side / 2)^2 / (lambda z0), from each set's
annotations (all splits; the box of the old sets is the ink, bench_1mm also gives its integer box), next to the share
of a pattern outside its crop and the open-set F1 and rejection of raw, prop, rec_z0.
  outside the crop   realistic, small_z0, small_near: setup_comparison.csv (pattern_in_crop.py, mean of 4 letters, the
                     box sides of their size class); bench_1mm: pattern_in_crop_bench_1mm_summary.csv (the oversampled
                     recorder, its own ink sides, crop on the ink, 1.0 mm, window 1024)
  F1, rejection      novel_open_macro_f1, novel_unknown_rejection of the test split. 'mean5' rows: the mean of the five
                     repetitions (setup_comparison.csv); 'r1' rows: repetition 1 alone (results/eval/<set>/<flow>_r1.json
                     for the old sets, $HOLO_RESULTS/eval/bench_1mm/<flow>_r1.json for the new one).
-> $HOLO_RESULTS/sets_by_fresnel.csv

    python scripts/exp_resolucao/sets_by_fresnel.py
"""
import json

import numpy as np
import pandas as pd

from holo_openset import paths
from holo_openset.sim.physics import PIXEL, WAVELENGTH

OLD = paths.PROJECT / 'results' / 'eval'
SETS = ['realistic', 'small_z0', 'small_near', 'bench_1mm']
FLOWS = ['raw', 'prop', 'rec_z0']


def nf(side, z):
    return (side * PIXEL / 2) ** 2 / (WAVELENGTH * z)


def main():
    R = paths.RESULTS
    sc = pd.read_csv(R / 'setup_comparison.csv').set_index('set')
    pc = pd.read_csv(R / 'pattern_in_crop_bench_1mm_summary.csv')
    pc = pc[(pc.z_mm == 1.0) & (pc.window == pc.window.max())].set_index('size')
    rows = []
    for s in SETS:
        root = paths.dataset(s)
        z = json.load(open(root / 'physics.json'))['physics']['z0']
        ann = pd.read_csv(root / 'annotations.csv')
        side = np.maximum(ann.x1 - ann.x0, ann.y1 - ann.y0).to_numpy(float)
        base = dict(set=s, z0_mm=round(z * 1e3, 4), n_letters=len(ann))
        if 'bx0' in ann:
            ink = np.maximum(ann.bx1 - ann.bx0, ann.by1 - ann.by0).to_numpy(float)
            base.update({f'side_px_p{q}': float(np.percentile(ink, q)) for q in (5, 50, 95)})
            base.update({f'fresnel_p{q}': nf(np.percentile(ink, q), z) for q in (5, 50, 95)})
            base.update({f'fresnel_intbox_p{q}': nf(np.percentile(side, q), z) for q in (5, 50, 95)})
            base.update({f'outside_crop_p{q}': float(pc.loc[f'p{q}', 'outside_crop_ink']) for q in (5, 50, 95)})
            base['outside_crop_source'] = 'pattern_in_crop_bench_1mm_summary.csv (oversampled, ink crop)'
        else:
            base.update({f'side_px_p{q}': float(np.percentile(side, q)) for q in (5, 50, 95)})
            base.update({f'fresnel_p{q}': nf(np.percentile(side, q), z) for q in (5, 50, 95)})
            base.update({f'outside_crop_p{q}': float(sc.loc[s, f'outside_crop_p{q}']) for q in (5, 50, 95)})
            base['outside_crop_source'] = 'setup_comparison.csv'
        for reps in ('mean5', 'r1'):
            row = dict(base, repetitions=reps)
            for f in FLOWS:
                for m, short in [('novel_open_macro_f1', 'f1'), ('novel_unknown_rejection', 'rejection')]:
                    if reps == 'mean5':
                        v = float(sc.loc[s, f'{short}_{f}']) if s in sc.index else np.nan
                    else:
                        p = (OLD if s != 'bench_1mm' else R / 'eval') / s / f'{f}_r1.json'
                        v = float(json.load(open(p))[m]) if p.exists() else np.nan
                    row[f'{short}_{f}'] = v
            for short in ('f1', 'rejection'):
                row[f'{short}_prop_minus_raw'] = row[f'{short}_prop'] - row[f'{short}_raw']
                row[f'{short}_rec_z0_minus_prop'] = row[f'{short}_rec_z0'] - row[f'{short}_prop']
            if not (reps == 'mean5' and s == 'bench_1mm'):
                rows.append(row)
    t = pd.DataFrame(rows)
    t.to_csv(R / 'sets_by_fresnel.csv', index=False, float_format='%.4f')
    pd.set_option('display.width', 250)
    print(t.T.to_string(header=False))


if __name__ == '__main__':
    main()
