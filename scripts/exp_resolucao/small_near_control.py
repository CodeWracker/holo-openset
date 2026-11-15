"""The table of control S and the reading of Q2 (docs/exp_resolucao/CADERNO_CURVA.md), applied mechanically.

Rows of $HOLO_RESULTS/small_near_control.csv (r1, test; F1 = novel_open_macro_f1, rejection = novel_unknown_rejection,
closed accuracy, threshold):
  reference   small_near as on disk (native recording), trained now, --no-aux   eval/small_near/<flow>_r1.json
  control     small_near_newrec (oversampled path), the same recipe            eval/small_near_newrec/<flow>_r1.json
  paper       the r1 of the paper for small_near (results/eval/small_near, read only; reference only)
  R_curva     the crops (raw) of the standard 1 mm family in r1 at the overlap of the control: linear interpolation in
              log(pi D^2 sigma) between the two levels that bracket the control's value (density_curve_reps.csv)
with, for each set, D (hologram_diameter_<set>_summary.json, the axis measure), the letter density in the window
(metadata) and pi D^2 sigma and the overlap ratio. Reading (crops only): nearer to R_curva than to R_ant in both
metrics -> the native sampling explains the deviation; nearer to R_ant in both -> it does not; one of each ->
inconclusive. -> small_near_control.csv, small_near_control_reading.json
"""
import json
import math

import numpy as np
import pandas as pd

from holo_openset import paths
from holo_openset.sim.physics import PIXEL

FLOWS = ['raw', 'prop', 'rec_z0']
M = {'novel_open_macro_f1': 'f1', 'novel_unknown_rejection': 'rejection', 'novel_closed_acc': 'closed_acc',
     'threshold': 'threshold'}
WINDOW_MM2 = (640 * PIXEL * 1e3) ** 2


def geometry(name):
    s = json.load(open(paths.RESULTS / f'hologram_diameter_{name}_summary.json'))
    d_mm = s['D_ef_px'][s['axis']] * PIXEL * 1e3
    m = pd.read_csv(paths.dataset(name) / 'metadata.csv')
    sigma = float(m.n_letters.mean()) / WINDOW_MM2
    x = math.pi * d_mm ** 2 * sigma
    return dict(D_um=d_mm * 1e3, D_axis=s['axis'], per_mm2=sigma, pi_D2_sigma=x, overlap=1 - math.exp(-x))


def main():
    rows = []
    geo = {k: geometry(k) for k in ['small_near', 'small_near_newrec']}
    for role, root, name in [('reference', paths.RESULTS / 'eval', 'small_near'),
                             ('control', paths.RESULTS / 'eval', 'small_near_newrec'),
                             ('paper r1 (reference only)', paths.PROJECT / 'results' / 'eval', 'small_near')]:
        for f in FLOWS:
            p = root / name / f'{f}_r1.json'
            j = json.load(open(p))
            rows.append(dict(role=role, set=name, flow=f, rep=1, source=str(p.relative_to(paths.PROJECT)),
                             **{v: j[k] for k, v in M.items()}, **geo[name]))
    # R_curva: the crops of the family at the control's pi D^2 sigma, r1
    reps = pd.read_csv(paths.RESULTS / 'density_curve_reps.csv')
    fam = reps[(reps.rep == 1) & (reps.flow == 'raw')].sort_values('pi_D2_sigma')
    x = geo['small_near_newrec']['pi_D2_sigma']
    lx = np.log(fam.pi_D2_sigma.to_numpy())
    if not lx[0] <= math.log(x) <= lx[-1]:
        raise SystemExit(f'the control (pi D^2 sigma = {x:.3f}) is outside the family: no interpolation')
    k = int(np.searchsorted(lx, math.log(x)))
    k = max(1, min(k, len(lx) - 1))
    lo, hi = fam.iloc[k - 1], fam.iloc[k]
    w = (math.log(x) - lx[k - 1]) / (lx[k] - lx[k - 1])
    curva = {m: (1 - w) * lo[m] + w * hi[m] for m in ['f1', 'rejection', 'closed_acc']}
    rows.append(dict(role='R_curva (family u50, crops, r1, interpolated)', set=f'levels {int(lo.level)}-{int(hi.level)}',
                     flow='raw', rep=1, source='results_exp_resolucao/density_curve_reps.csv', **curva,
                     pi_D2_sigma=x, overlap=1 - math.exp(-x)))
    t = pd.DataFrame(rows)
    get = lambda role, f, m: float(t[(t.role == role) & (t.flow == f)][m].iloc[0])   # noqa: E731
    ant = dict(f1=get('reference', 'raw', 'f1'), rej=get('reference', 'raw', 'rejection'))
    ctl = dict(f1=get('control', 'raw', 'f1'), rej=get('control', 'raw', 'rejection'))
    cur = dict(f1=curva['f1'], rej=curva['rejection'])
    dist = {m: dict(to_R_ant=abs(ctl[m] - ant[m]), to_R_curva=abs(ctl[m] - cur[m])) for m in ('f1', 'rej')}
    near = {m: 'R_curva' if d['to_R_curva'] < d['to_R_ant'] else 'R_ant' if d['to_R_ant'] < d['to_R_curva']
            else 'tie' for m, d in dist.items()}
    both = set(near.values())
    outcome = ('the native sampling explains the deviation' if both == {'R_curva'} else
               'the sampling does not explain it' if both == {'R_ant'} else 'inconclusive')
    for m, mm in [('f1', 'f1'), ('rej', 'rejection')]:
        t.loc[(t.role == 'control') & (t.flow == 'raw'), f'dist_{mm}_to_R_ant'] = dist[m]['to_R_ant']
        t.loc[(t.role == 'control') & (t.flow == 'raw'), f'dist_{mm}_to_R_curva'] = dist[m]['to_R_curva']
    t.to_csv(paths.RESULTS / 'small_near_control.csv', index=False, float_format='%.6g')
    reading = dict(R_ant=ant, control=ctl, R_curva=cur,
                   R_curva_from=dict(levels=[int(lo.level), int(hi.level)], weight_upper=w,
                                     pi_D2_sigma=[float(lo.pi_D2_sigma), float(hi.pi_D2_sigma)]),
                   geometry=geo, distances=dist, nearer=near, outcome=outcome,
                   note='the control changes two pieces at once: the oversampled propagation and the drawing of the '
                        'letters (continuous font sizes and positions, master raster, spacing on the pixel box of '
                        'the ink, dust on the master grid)')
    json.dump(reading, open(paths.RESULTS / 'small_near_control_reading.json', 'w'), indent=1)
    with pd.option_context('display.width', 250, 'display.max_columns', 30):
        print(t.to_string())
    print(json.dumps(reading, indent=1))


if __name__ == '__main__':
    main()
