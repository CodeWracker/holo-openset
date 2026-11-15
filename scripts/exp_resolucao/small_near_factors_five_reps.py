"""Q4 (docs/exp_resolucao/CADERNO_CURVA.md): the two controls of the small letters at 2 mm (small_near_ctlN, the N_F
range of the standard family; small_near_ctlP, its depth law) in five repetitions. The reading of Q4, crops only, per
repetition k: R_reg(k) = the crops of small_near_newrec in k; R_curva(k) = the crops of the standard family (u50) in k at
the control's own pi D^2 sigma (linear interpolation in log(pi D^2 sigma) between the two bracketing levels, levels 15
and 69 here; the code of small_near_factors.py with the repetition as a parameter); the control "returns to the curve"
in k if nearer to R_curva(k) than to R_reg(k) in both metrics, "stays" if nearer to R_reg(k) in both. Verdict: the
factor explains the deviation if it returns in >= 4 of 5; it does not explain if it stays in >= 4 of 5; otherwise
inconclusive. Beside, without criterion: the layer (prop) and the reconstruction (rec_z0) of the controls against those
of small_near_newrec, per repetition and mean / min / max.
-> $HOLO_RESULTS/small_near_factors_five_reps.csv, small_near_factors_five_reps_reading.json
    python scripts/exp_resolucao/small_near_factors_five_reps.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from holo_openset import paths

sys.path.insert(0, str(Path(__file__).resolve().parent))
from small_near_control import M, geometry   # noqa: E402

CONTROLS = {'small_near_ctlN': 'N_F range of the standard family (fonts x sqrt(2.0 / 19.25))',
            'small_near_ctlP': 'depth law of the family (uniform +-25 um)'}
FLOWS = ['raw', 'prop', 'rec_z0']
REPS = [1, 2, 3, 4, 5]


def r_curva(x, rep):
    """The crops of the standard family in repetition `rep` at pi D^2 sigma = x (small_near_factors.r_curva with the
    repetition as a parameter)."""
    reps = pd.read_csv(paths.RESULTS / 'density_curve_reps.csv')
    fam = reps[(reps.rep == rep) & (reps.flow == 'raw')].sort_values('pi_D2_sigma')
    lx = np.log(fam.pi_D2_sigma.to_numpy())
    if not lx[0] <= math.log(x) <= lx[-1]:
        raise SystemExit(f'pi D^2 sigma = {x:.3f} is outside the family: no interpolation')
    k = max(1, min(int(np.searchsorted(lx, math.log(x))), len(lx) - 1))
    lo, hi = fam.iloc[k - 1], fam.iloc[k]
    w = (math.log(x) - lx[k - 1]) / (lx[k] - lx[k - 1])
    return {m: (1 - w) * lo[m] + w * hi[m] for m in ['f1', 'rejection']}, \
        dict(levels=[int(lo.level), int(hi.level)], weight_upper=w)


def ev(s, f, r):
    j = json.load(open(paths.RESULTS / 'eval' / s / f'{f}_r{r}.json'))
    return {v: j[k] for k, v in M.items()}


def main():
    rows, reading = [], {}
    for s, what in CONTROLS.items():
        geo = geometry(s)
        per = []
        for r in REPS:
            c, reg = ev(s, 'raw', r), ev('small_near_newrec', 'raw', r)
            cur, frm = r_curva(geo['pi_D2_sigma'], r)
            d = {m: dict(to_R_reg=abs(c[mm] - reg[mm]), to_R_curva=abs(c[mm] - cur[mm]))
                 for m, mm in [('f1', 'f1'), ('rej', 'rejection')]}
            near = {m: 'R_curva' if x['to_R_curva'] < x['to_R_reg'] else 'R_reg' if x['to_R_reg'] < x['to_R_curva']
                    else 'tie' for m, x in d.items()}
            back = set(near.values()) == {'R_curva'}
            stays = set(near.values()) == {'R_reg'}
            row = dict(control=s, changed=what, rep=r, f1=c['f1'], rejection=c['rejection'],
                       closed_acc=c['closed_acc'], R_reg_f1=reg['f1'], R_reg_rejection=reg['rejection'],
                       R_curva_f1=cur['f1'], R_curva_rejection=cur['rejection'], R_curva_weight_69=frm['weight_upper'],
                       dist_f1_to_R_reg=d['f1']['to_R_reg'], dist_f1_to_R_curva=d['f1']['to_R_curva'],
                       dist_rej_to_R_reg=d['rej']['to_R_reg'], dist_rej_to_R_curva=d['rej']['to_R_curva'],
                       nearer_f1=near['f1'], nearer_rej=near['rej'], returns_to_curve=back, stays_at_R_reg=stays,
                       pi_D2_sigma=geo['pi_D2_sigma'], overlap=geo['overlap'])
            for f in ('prop', 'rec_z0'):   # beside, without criterion
                cf, rf = ev(s, f, r), ev('small_near_newrec', f, r)
                row.update({f'{f}_f1': cf['f1'], f'{f}_rejection': cf['rejection'],
                            f'{f}_f1_newrec': rf['f1'], f'{f}_rejection_newrec': rf['rejection']})
            per.append(row)
        t = pd.DataFrame(per)
        n_back, n_stay = int(t.returns_to_curve.sum()), int(t.stays_at_R_reg.sum())
        verdict = ('the factor explains the deviation' if n_back >= 4 else
                   'the factor does not explain it' if n_stay >= 4 else 'inconclusive')
        num = [c for c in t.columns if t[c].dtype.kind == 'f']
        stats = {st: {c: float(getattr(t[c], st)()) for c in num} for st in ('mean', 'min', 'max')}
        reading[s] = dict(changed=what, returns_to_curve=n_back, stays_at_R_reg=n_stay, of=len(t), verdict=verdict,
                          per_rep=t[['rep', 'f1', 'rejection', 'R_reg_f1', 'R_reg_rejection', 'R_curva_f1',
                                     'R_curva_rejection', 'nearer_f1', 'nearer_rej']].to_dict('records'),
                          mean=stats['mean'], min=stats['min'], max=stats['max'],
                          geometry=geo)
        rows.append(t)
        for st in ('mean', 'min', 'max'):
            rows.append(pd.DataFrame([dict(control=s, changed=what, rep=st, **stats[st])]))
    out = pd.concat(rows, ignore_index=True)
    out.to_csv(paths.RESULTS / 'small_near_factors_five_reps.csv', index=False, float_format='%.6g')
    json.dump(reading, open(paths.RESULTS / 'small_near_factors_five_reps_reading.json', 'w'), indent=1, default=str)
    with pd.option_context('display.width', 250, 'display.max_columns', 40):
        print(out[['control', 'rep', 'f1', 'rejection', 'R_reg_f1', 'R_reg_rejection', 'R_curva_f1',
                   'R_curva_rejection', 'nearer_f1', 'nearer_rej', 'prop_f1', 'prop_rejection', 'rec_z0_f1',
                   'rec_z0_rejection', 'rec_z0_rejection_newrec']].round(4).to_string(index=False))
    for s, v in reading.items():
        print(s, v['returns_to_curve'], v['stays_at_R_reg'], v['verdict'])


if __name__ == '__main__':
    main()
