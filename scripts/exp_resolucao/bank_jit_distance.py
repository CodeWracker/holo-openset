"""Table of test J (CADERNO_CURVA.md Q2, section J; CADERNO_CURVA_DISTANCIA.md, D3), r1 only, nothing evaluated here.

  bank_jit as is   1.0 mm: eval/curve_u50_L008/bank_jit_r1.json; 0.9, 1.1 mm and 0.7 mm (stress, outside the rule):
                   robustness_curve_u50_L008_bank_jit.csv (bank_jit_distance.sh)
  rows of r1 that exist (copied): raw, prop, rec_z0 as is (1.0 mm: eval/curve_u50_L008/<flow>_r1.json; the other
                   distances: robustness_curve_u50_L008_dist.csv, d2), prop recalibrated by ratio, rec_z0
                   recalibrated (by ratio, the main variant, and literal)
Columns f1 (novel_open_macro_f1), rejection (novel_unknown_rejection), closed_acc, known_acc.
Differences (kind = diff): bank - bank at 1.0 mm (f1 and rejection) and the rule "aguenta" of Q2 applied
mechanically (holds at a distance if the drop is below 0.10 in F1 AND below 0.30 in rejection; holds the change of
distance if it holds at 0.9 AND at 1.1 mm; 0.7 mm is computed and marked outside the rule); bank as is - rec_z0
recalibrated (ratio and literal) at each shifted distance; the price at 1.0 mm (bank - prop, bank - rec_z0).

    python scripts/exp_resolucao/bank_jit_distance.py -> results_exp_resolucao/bank_jit_distance.csv
"""
import json

import pandas as pd

from holo_openset import paths

SET = 'curve_u50_L008'
MET = {'f1': 'novel_open_macro_f1', 'rejection': 'novel_unknown_rejection', 'closed_acc': 'novel_closed_acc',
       'known_acc': 'novel_known_acc'}
DIST = {'z09': 0.9, 'z11': 1.1, 'z07': 0.7}
COND = {'': 'as_is', '+recal': 'recal_literal', '+recal_ratio': 'recal_ratio'}
KEEP = [('raw', 'as_is'), ('prop', 'as_is'), ('rec_z0', 'as_is'), ('prop', 'recal_ratio'), ('rec_z0', 'recal_ratio'),
        ('rec_z0', 'recal_literal')]


def main():
    R = paths.RESULTS
    rows = []
    for f in ['bank_jit', 'raw', 'prop', 'rec_z0']:
        p = R / 'eval' / SET / f'{f}_r1.json'
        j = json.load(open(p))
        assert j['rep'] == 1
        rows.append(dict(kind='metric', distance_mm=1.0, flow=f, condition='as_is',
                         **{k: j[c] for k, c in MET.items()}, source=str(p.relative_to(R))))
    for csv in ['robustness_curve_u50_L008_bank_jit.csv', 'robustness_curve_u50_L008_dist.csv']:
        t = pd.read_csv(R / csv)
        for _, r in t[(t.rep == 1) & t.variant.isin(list(DIST))].iterrows():
            flow, cond = r.flow, ''
            for suf in ('+recal_ratio', '+recal'):
                if flow.endswith(suf):
                    flow, cond = flow[:-len(suf)], suf
                    break
            if flow != 'bank_jit' and (flow, COND[cond]) not in KEEP:
                continue
            rows.append(dict(kind='metric', distance_mm=DIST[r.variant], flow=flow, condition=COND[cond],
                             **{k: r[c] for k, c in MET.items()}, source=csv))
    m = pd.DataFrame(rows)
    assert not m.duplicated(['distance_mm', 'flow', 'condition']).any()
    ix = m.set_index(['distance_mm', 'flow', 'condition'])
    for d in [1.0, 0.9, 1.1, 0.7]:
        assert (d, 'bank_jit', 'as_is') in ix.index, f'bank_jit at {d} mm missing'
    b0 = ix.loc[(1.0, 'bank_jit', 'as_is')]
    der, holds = [], {}
    for d in [0.9, 1.1, 0.7]:
        b = ix.loc[(d, 'bank_jit', 'as_is')]
        drop_f1, drop_rej = b0.f1 - b.f1, b0.rejection - b.rejection
        h = bool(drop_f1 < 0.10 and drop_rej < 0.30)
        if d != 0.7:
            holds[d] = h
        der.append(dict(kind='diff', distance_mm=d, flow='bank_jit', condition='as_is - bank_jit at 1.0 mm',
                        f1=b.f1 - b0.f1, rejection=b.rejection - b0.rejection, holds=h,
                        note='rule of Q2' if d != 0.7 else 'stress, outside the rule'))
        for cond in ('recal_ratio', 'recal_literal'):
            r = ix.loc[(d, 'rec_z0', cond)]
            der.append(dict(kind='diff', distance_mm=d, flow='bank_jit - rec_z0',
                            condition=f'bank_jit as_is - rec_z0 {cond}', f1=b.f1 - r.f1,
                            rejection=b.rejection - r.rejection,
                            note='' if d != 0.7 else 'stress, outside the rule'))
    for f in ('prop', 'rec_z0'):
        r = ix.loc[(1.0, f, 'as_is')]
        der.append(dict(kind='diff', distance_mm=1.0, flow=f'bank_jit - {f}', condition='price at 1.0 mm (as is)',
                        f1=b0.f1 - r.f1, rejection=b0.rejection - r.rejection))
    der.append(dict(kind='rule', distance_mm=float('nan'), flow='bank_jit',
                    condition='holds the change of distance (holds at 0.9 AND at 1.1 mm)',
                    holds=bool(holds[0.9] and holds[1.1]), note='r1 only: descriptive'))
    out = pd.concat([m, pd.DataFrame(der)], ignore_index=True)
    order = {1.0: 0, 0.9: 1, 1.1: 2, 0.7: 3}
    out['_d'] = out.distance_mm.map(order).fillna(4)
    out['_k'] = out.kind.map({'metric': 0, 'diff': 1, 'rule': 2})
    out = out.sort_values(['_k', '_d'], kind='stable').drop(columns=['_d', '_k']).reset_index(drop=True)
    out.to_csv(R / 'bank_jit_distance.csv', index=False, float_format='%.6f')
    pd.set_option('display.width', 250)
    print(out.drop(columns='source').round(4).to_string(index=False))
    print('wrote', R / 'bank_jit_distance.csv')


if __name__ == '__main__':
    main()
