"""Q3-D (docs/exp_resolucao/CADERNO_CURVA.md): the two controls of the set off the curve, each changing one thing of
small_near_newrec (small_near_ctlN: the font sizes of the standard family at 2.0 mm; small_near_ctlP: the depth law of
the family), r1, crops / layer / reconstruction. Reading (crops only), the code of the Q2-S table
(small_near_control.py): R_reg = small_near_newrec raw r1; R_curva = the crops of the standard 1 mm family in r1 at the
control's own pi D^2 sigma (linear interpolation in log(pi D^2 sigma) between the two levels that bracket it,
density_curve_reps.csv); nearer to R_curva in both metrics -> the factor explains the deviation; nearer to R_reg in
both -> it does not; one of each -> inconclusive.
-> $HOLO_RESULTS/small_near_factors.csv, small_near_factors_reading.json
    python scripts/exp_resolucao/small_near_factors.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from holo_openset import paths

sys.path.insert(0, str(Path(__file__).resolve().parent))
from small_near_control import FLOWS, M, geometry   # noqa: E402  (the same geometry and metrics as Q2-S)

CONTROLS = {'small_near_ctlN': 'N_F range of the standard family (fonts x sqrt(2.0 / 19.25))',
            'small_near_ctlP': 'depth law of the family (uniform +-25 um)'}


def r_curva(x):
    reps = pd.read_csv(paths.RESULTS / 'density_curve_reps.csv')
    fam = reps[(reps.rep == 1) & (reps.flow == 'raw')].sort_values('pi_D2_sigma')
    lx = np.log(fam.pi_D2_sigma.to_numpy())
    if not lx[0] <= math.log(x) <= lx[-1]:
        raise SystemExit(f'pi D^2 sigma = {x:.3f} is outside the family: no interpolation')
    k = max(1, min(int(np.searchsorted(lx, math.log(x))), len(lx) - 1))
    lo, hi = fam.iloc[k - 1], fam.iloc[k]
    w = (math.log(x) - lx[k - 1]) / (lx[k] - lx[k - 1])
    return {m: (1 - w) * lo[m] + w * hi[m] for m in ['f1', 'rejection', 'closed_acc']}, \
        dict(levels=[int(lo.level), int(hi.level)], weight_upper=w)


def main():
    rows, reading = [], {}
    j = json.load(open(paths.RESULTS / 'eval' / 'small_near_newrec' / 'raw_r1.json'))
    reg = dict(f1=j['novel_open_macro_f1'], rej=j['novel_unknown_rejection'])
    geo_reg = geometry('small_near_newrec')
    for f in FLOWS:
        jj = json.load(open(paths.RESULTS / 'eval' / 'small_near_newrec' / f'{f}_r1.json'))
        rows.append(dict(role='R_reg (small_near_newrec)', set='small_near_newrec', flow=f, rep=1,
                         **{v: jj[k] for k, v in M.items()}, **geo_reg))
    for s, what in CONTROLS.items():
        geo = geometry(s)
        for f in FLOWS:
            jj = json.load(open(paths.RESULTS / 'eval' / s / f'{f}_r1.json'))
            rows.append(dict(role=f'control: {what}', set=s, flow=f, rep=1, **{v: jj[k] for k, v in M.items()},
                             **geo))
        cur, frm = r_curva(geo['pi_D2_sigma'])
        rows.append(dict(role=f'R_curva for {s} (family u50, crops, r1)', set=f'levels {frm["levels"][0]}-'
                         f'{frm["levels"][1]}', flow='raw', rep=1, **cur, pi_D2_sigma=geo['pi_D2_sigma'],
                         overlap=geo['overlap']))
        t = pd.DataFrame(rows)
        c = t[(t.set == s) & (t.flow == 'raw')].iloc[0]
        ctl = dict(f1=float(c.f1), rej=float(c.rejection))
        cu = dict(f1=cur['f1'], rej=cur['rejection'])
        dist = {m: dict(to_R_reg=abs(ctl[m] - reg[m]), to_R_curva=abs(ctl[m] - cu[m])) for m in ('f1', 'rej')}
        near = {m: 'R_curva' if d['to_R_curva'] < d['to_R_reg'] else 'R_reg' if d['to_R_reg'] < d['to_R_curva']
                else 'tie' for m, d in dist.items()}
        both = set(near.values())
        reading[s] = dict(changed=what, control=ctl, R_reg=reg, R_curva=cu, R_curva_from=frm, geometry=geo,
                          distances=dist, nearer=near,
                          outcome=('the factor explains the deviation' if both == {'R_curva'} else
                                   'the factor does not explain it' if both == {'R_reg'} else 'inconclusive'))
    t = pd.DataFrame(rows)
    t.to_csv(paths.RESULTS / 'small_near_factors.csv', index=False, float_format='%.6g')
    json.dump(reading, open(paths.RESULTS / 'small_near_factors_reading.json', 'w'), indent=1)
    with pd.option_context('display.width', 250, 'display.max_columns', 30):
        print(t[['role', 'set', 'flow', 'f1', 'rejection', 'closed_acc', 'D_um', 'pi_D2_sigma', 'overlap']].round(4)
              .to_string(index=False))
    print(json.dumps(reading, indent=1))


if __name__ == '__main__':
    main()
