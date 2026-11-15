"""Table of test J2 (CADERNO_CURVA.md Q3, section J2; CADERNO_CURVA_DISTANCIA.md, D4 on). Nothing is evaluated here.

Banks: bank_jit (5 planes over +-5 %, jitter 5 %), bank_wide (7 over +-12 %, jitter 12 %), bank_w2 (9 over +-12 %,
jitter 12 %), bank_w3 (7 over +-12 %, jitter 5 %), trained on curve_u50_L008, r1-r5.
  1.0 mm             eval/curve_u50_L008/<bank>_r<k>.json
  0.9, 1.1, 0.7 mm   robustness_curve_u50_L008_banks_<bank>.csv (banks_distance.sh): as is (flow <bank>) and
                     recalibrated by ratio (<bank>+recal_ratio); bank_jit r1 as is: robustness_curve_u50_L008_bank_jit.csv
                     (test J)
  layer and reconstruction (prop, rec_z0; as is and recalibrated by ratio, r1-r5): read from distance_tests_u50_rows.csv
                     (d2, 6 decimals as stored), not recomputed
Columns f1 (novel_open_macro_f1), rejection (novel_unknown_rejection), closed_acc, known_acc.

  banks_distance_rows.csv  per bank, repetition, distance, condition: the metrics (kind = metric); the drop against the
                           bank itself at 1.0 mm (kind = drop; as is and recalibrated); the verdict of the rule of Q3-J2
                           per repetition (kind = verdict: holds if, as is, at 0.9 AND 1.1 mm the F1 is less than 0.10
                           and the rejection less than 0.30 below its own values at 1.0 mm); the differences (kind = diff):
                           price at 1.0 mm (bank - rec_z0, bank - prop), bank as is - rec_z0 as is, bank as is - rec_z0
                           recalibrated, bank recalibrated - rec_z0 recalibrated, bank recalibrated - prop recalibrated
                           ("recalibrated" = by ratio, the main variant of d2, for the three)
  banks_distance.csv       per bank: the metrics, drops and differences as mean / min / max / n over the repetitions,
                           with the count of positive differences (k of 5 at one distance; k of 10 over 0.9 and 1.1;
                           k of 15 with 0.7) and the verdict "holds in k of 5" (holds the change of distance if k >= 4)

    python scripts/exp_resolucao/banks_distance.py
"""
import json

import numpy as np
import pandas as pd

from holo_openset import paths

SET = 'curve_u50_L008'
BANKS = ['bank_jit', 'bank_wide', 'bank_w2', 'bank_w3']
REPS = [1, 2, 3, 4, 5]
MET = {'f1': 'novel_open_macro_f1', 'rejection': 'novel_unknown_rejection', 'closed_acc': 'novel_closed_acc',
       'known_acc': 'novel_known_acc'}
DIST = {'z09': 0.9, 'z11': 1.1, 'z07': 0.7}


def main():
    R = paths.RESULTS
    rows = []
    for b in BANKS:
        for rep in REPS:
            p = R / 'eval' / SET / f'{b}_r{rep}.json'
            j = json.load(open(p))
            assert j['rep'] == rep and j['flow'] == b
            rows.append(dict(kind='metric', flow=b, rep=rep, distance_mm=1.0, condition='as_is',
                             **{k: j[c] for k, c in MET.items()}, source=str(p.relative_to(R))))
        files = [f'robustness_curve_u50_L008_banks_{b}.csv'] + \
            (['robustness_curve_u50_L008_bank_jit.csv'] if b == 'bank_jit' else [])
        for csv in files:
            t = pd.read_csv(R / csv)
            t = t[t.rep.isin(REPS) & t.variant.isin(list(DIST)) & t.flow.isin([b, f'{b}+recal_ratio'])]
            for _, r in t.iterrows():
                rows.append(dict(kind='metric', flow=b, rep=int(r.rep), distance_mm=DIST[r.variant],
                                 condition='recal_ratio' if r.flow.endswith('+recal_ratio') else 'as_is',
                                 **{k: r[c] for k, c in MET.items()}, source=csv))
    m = pd.DataFrame(rows)
    key = ['flow', 'rep', 'distance_mm', 'condition']
    assert not m.duplicated(key).any(), m[m.duplicated(key, keep=False)]
    need = {(b, r, d, c) for b in BANKS for r in REPS for d, c in
            [(1.0, 'as_is')] + [(d, c) for d in DIST.values() for c in ('as_is', 'recal_ratio')]}
    missing = need - set(map(tuple, m[key].values))
    assert not missing, sorted(missing)
    # layer and reconstruction of d2, as stored
    d2 = pd.read_csv(R / 'distance_tests_u50_rows.csv')
    d2 = d2[(d2.kind == 'metric') & d2.flow.isin(['prop', 'rec_z0']) & d2.condition.isin(['as_is', 'recal_ratio'])]
    ref = d2.set_index(['flow', 'rep', 'distance_mm', 'condition'])
    ix = m.set_index(key)

    der = []
    for b in BANKS:
        for rep in REPS:
            b0 = ix.loc[(b, rep, 1.0, 'as_is')]
            ok = []
            for d in DIST.values():
                for c in ('as_is', 'recal_ratio'):
                    x = ix.loc[(b, rep, d, c)]
                    der.append(dict(kind='drop', flow=b, rep=rep, distance_mm=d, condition=f'{c} - own 1.0 mm',
                                    f1=x.f1 - b0.f1, rejection=x.rejection - b0.rejection))
                    if c == 'as_is' and d in (0.9, 1.1):
                        ok.append(b0.f1 - x.f1 < 0.10 and b0.rejection - x.rejection < 0.30)
                a, rr = ix.loc[(b, rep, d, 'as_is')], ix.loc[(b, rep, d, 'recal_ratio')]
                for name, x, y in [('bank as_is - rec_z0 as_is', a, ref.loc[('rec_z0', rep, d, 'as_is')]),
                                   ('bank as_is - rec_z0 recal_ratio', a, ref.loc[('rec_z0', rep, d, 'recal_ratio')]),
                                   ('bank recal_ratio - rec_z0 recal_ratio', rr,
                                    ref.loc[('rec_z0', rep, d, 'recal_ratio')]),
                                   ('bank recal_ratio - prop recal_ratio', rr, ref.loc[('prop', rep, d, 'recal_ratio')])]:
                    der.append(dict(kind='diff', flow=b, rep=rep, distance_mm=d, condition=name,
                                    f1=x.f1 - y.f1, rejection=x.rejection - y.rejection))
            for f in ('rec_z0', 'prop'):
                y = ref.loc[(f, rep, 1.0, 'as_is')]
                der.append(dict(kind='diff', flow=b, rep=rep, distance_mm=1.0, condition=f'price: bank - {f} at 1.0 mm',
                                f1=b0.f1 - y.f1, rejection=b0.rejection - y.rejection))
            der.append(dict(kind='verdict', flow=b, rep=rep, distance_mm=np.nan,
                            condition='holds (as is, 0.9 AND 1.1 mm, rule of Q3-J2)', holds=bool(all(ok))))
    per = pd.concat([m, pd.DataFrame(der)], ignore_index=True)
    per.to_csv(R / 'banks_distance_rows.csv', index=False, float_format='%.6f')

    summ = []
    for (kind, b, d, c), x in per[per.kind != 'verdict'].groupby(['kind', 'flow', 'distance_mm', 'condition'],
                                                                  sort=False):
        row = dict(kind=kind, flow=b, distance_mm=d, condition=c, n=len(x))
        for k in ('f1', 'rejection', 'closed_acc', 'known_acc'):
            if k in x and x[k].notna().all():
                row.update({f'{k}_mean': x[k].mean(), f'{k}_min': x[k].min(), f'{k}_max': x[k].max()})
        if kind == 'diff':
            row.update(f1_positive=int((x.f1 > 0).sum()), rejection_positive=int((x.rejection > 0).sum()))
        summ.append(row)
    # sign counts over distances (k of 10: 0.9 and 1.1; k of 15: with 0.7)
    dd = per[(per.kind == 'diff') & per.distance_mm.isin([0.9, 1.1, 0.7])]
    for (b, c), x in dd.groupby(['flow', 'condition'], sort=False):
        for name, ds in [('0.9 + 1.1', [0.9, 1.1]), ('0.9 + 1.1 + 0.7', [0.9, 1.1, 0.7])]:
            y = x[x.distance_mm.isin(ds)]
            summ.append(dict(kind='diff_count', flow=b, distance_mm=np.nan, condition=f'{c} ({name})', n=len(y),
                             f1_mean=y.f1.mean(), f1_min=y.f1.min(), f1_max=y.f1.max(),
                             rejection_mean=y.rejection.mean(), rejection_min=y.rejection.min(),
                             rejection_max=y.rejection.max(),
                             f1_positive=int((y.f1 > 0).sum()), rejection_positive=int((y.rejection > 0).sum())))
    v = per[per.kind == 'verdict']
    for b in BANKS:
        k = int(v[v.flow == b].holds.sum())
        summ.append(dict(kind='verdict', flow=b, distance_mm=np.nan, n=len(REPS), holds_in=k,
                         condition=f'holds in {k} of 5; holds the change of distance: {k >= 4}',
                         holds=bool(k >= 4)))
    s = pd.DataFrame(summ)
    s.to_csv(R / 'banks_distance.csv', index=False, float_format='%.6f')
    pd.set_option('display.width', 250)
    pd.set_option('display.max_rows', 500)
    cols = ['kind', 'flow', 'distance_mm', 'condition', 'n', 'f1_mean', 'f1_min', 'f1_max', 'rejection_mean',
            'rejection_min', 'rejection_max', 'f1_positive', 'rejection_positive']
    print(s[[c for c in cols if c in s]].round(4).to_string(index=False))
    print('wrote', R / 'banks_distance.csv', R / 'banks_distance_rows.csv')


if __name__ == '__main__':
    main()
