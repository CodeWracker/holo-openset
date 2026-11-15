"""Table of the depth rows of the curve stage, phase 2 (CADERNO_CURVA.md Q1; CADERNO_CURVA_DISTANCIA.md), no criterion.
Three depth laws of the 1.0 mm sets: flat (the pilot, bench_1mm: normal 2.6 um, cut at 7.8 um), u50 (the standard
law: uniform over the 50 um channel, curve_u50_L008), wide (normal 50 um, cut at 150 um: bench_1mm_depth50 and its
test split bench_1mm_robust/depth50). Models, gallery and threshold of the set the models were trained on; test
split of the other; novel_open_macro_f1 (f1) and novel_unknown_rejection (rejection).

New rows (depth_tests.sh, r1-r5):
  flat -> u50    robustness_depth_from_bench_1mm.csv, variant curve_u50_L008
  u50 -> flat    robustness_depth_from_curve_u50_L008.csv, variant bench_1mm
  u50 -> wide    robustness_depth_from_curve_u50_L008.csv, variant depth50
Rows that exist, COPIED (not recomputed), with their number of repetitions:
  flat -> flat   pilot_five_reps_robustness.csv (variant base; 5 repetitions; 4 decimals as stored)
  flat -> wide   pilot_five_reps_robustness.csv (variant depth50; 5 repetitions; 4 decimals as stored)
  wide -> wide   depth_training.csv (r1; 4 decimals as stored)
  wide -> flat   depth_training.csv (r1; 4 decimals as stored)
  u50 -> u50     eval/curve_u50_L008/<flow>_r<n>.json (the set's own evaluation; 5 repetitions)

  depth_tests_rows.csv  per repetition, the new rows and u50 -> u50 (kind = metric); and the paired differences, same
                        repetition and flow (kind = diff): flat -> u50 minus u50 -> u50 (training on the flat sample
                        against training on the law, the same test), flat -> u50 minus flat -> flat, u50 -> flat
                        minus u50 -> u50, u50 -> wide minus u50 -> u50
  depth_tests.csv       per trained / tested / flow: n_reps, mean / min / max of f1 and rejection, source; and the
                        differences, mean / min / max

    python scripts/exp_resolucao/depth_tests.py
"""
import json

import pandas as pd

from holo_openset import paths

REPS = [1, 2, 3, 4, 5]
FLOWS = ['raw', 'prop', 'rec_z0']
MET = {'f1': 'novel_open_macro_f1', 'rejection': 'novel_unknown_rejection', 'closed_acc': 'novel_closed_acc',
       'known_acc': 'novel_known_acc'}
U50 = 'curve_u50_L008'


def main():
    R = paths.RESULTS
    rows = []
    for trained, tested, csv, variant in [('flat', 'u50', 'robustness_depth_from_bench_1mm.csv', U50),
                                          ('u50', 'flat', f'robustness_depth_from_{U50}.csv', 'bench_1mm'),
                                          ('u50', 'wide', f'robustness_depth_from_{U50}.csv', 'depth50')]:
        t = pd.read_csv(R / csv)
        t = t[(t.variant == variant) & t.rep.isin(REPS)]
        assert sorted(zip(t.rep, t.flow)) == sorted((r, f) for r in REPS for f in FLOWS), (csv, variant)
        for _, r in t.iterrows():
            rows.append(dict(kind='metric', trained=trained, tested=tested, flow=r.flow, rep=int(r.rep),
                             **{k: r[c] for k, c in MET.items()}, source=csv))
    for rep in REPS:
        for f in FLOWS:
            p = R / 'eval' / U50 / f'{f}_r{rep}.json'
            j = json.load(open(p))
            rows.append(dict(kind='metric', trained='u50', tested='u50', flow=f, rep=rep,
                             **{k: j[c] for k, c in MET.items()}, source=str(p.relative_to(R))))
    m = pd.DataFrame(rows)
    # the flat -> flat rows per repetition, for the paired differences (the eval json of bench_1mm)
    flat = {(f, rep): json.load(open(R / 'eval' / 'bench_1mm' / f'{f}_r{rep}.json')) for f in FLOWS for rep in REPS}
    ix = m.set_index(['trained', 'tested', 'flow', 'rep'])
    der = []
    for f in FLOWS:
        for rep in REPS:
            uu = ix.loc[('u50', 'u50', f, rep)]
            for name, a, b in [('flat->u50 - u50->u50', ix.loc[('flat', 'u50', f, rep)], uu),
                               ('flat->u50 - flat->flat', ix.loc[('flat', 'u50', f, rep)],
                                pd.Series({k: flat[(f, rep)][c] for k, c in MET.items()})),
                               ('u50->flat - u50->u50', ix.loc[('u50', 'flat', f, rep)], uu),
                               ('u50->wide - u50->u50', ix.loc[('u50', 'wide', f, rep)], uu)]:
                der.append(dict(kind='diff', trained=name.split(' - ')[0], tested=name, flow=f, rep=rep,
                                f1=a.f1 - b.f1, rejection=a.rejection - b.rejection))
    per = pd.concat([m, pd.DataFrame(der)], ignore_index=True)
    per.to_csv(R / 'depth_tests_rows.csv', index=False, float_format='%.6f')

    summ = []
    # copied, as stored
    pf = pd.read_csv(R / 'pilot_five_reps_robustness.csv')
    for variant, tested in [('base', 'flat'), ('depth50', 'wide')]:
        for f in FLOWS:
            x = pf[(pf.variant == variant) & (pf.flow == f)].iloc[0]
            summ.append(dict(kind='copied', trained='flat', tested=tested, flow=f,
                             n_reps=int(x.novel_open_macro_f1_count),
                             f1_mean=x.novel_open_macro_f1_mean, f1_min=x.novel_open_macro_f1_min,
                             f1_max=x.novel_open_macro_f1_max, rejection_mean=x.novel_unknown_rejection_mean,
                             rejection_min=x.novel_unknown_rejection_min, rejection_max=x.novel_unknown_rejection_max,
                             source='pilot_five_reps_robustness.csv'))
    dt = pd.read_csv(R / 'depth_training.csv')
    for (tr, te), (trained, tested) in {(50.0, 50.0): ('wide', 'wide'), (50.0, 2.6): ('wide', 'flat')}.items():
        for f in FLOWS:
            x = dt[(dt.trained_um == tr) & (dt.tested_um == te) & (dt.flow == f)]
            assert len(x) == 1 and int(x.rep.iloc[0]) == 1
            x = x.iloc[0]
            summ.append(dict(kind='copied', trained=trained, tested=tested, flow=f, n_reps=1,
                             f1_mean=x.f1, f1_min=x.f1, f1_max=x.f1, rejection_mean=x.rejection,
                             rejection_min=x.rejection, rejection_max=x.rejection, source='depth_training.csv (r1)'))
    for (kind, trained, tested, flow), x in per.groupby(['kind', 'trained', 'tested', 'flow'], sort=False):
        row = dict(kind='new' if kind == 'metric' and (trained, tested) != ('u50', 'u50') else
                   'own_eval' if kind == 'metric' else 'diff', trained=trained, tested=tested, flow=flow,
                   n_reps=len(x), source=x.source.iloc[0] if kind == 'metric' else 'depth_tests_rows.csv')
        for k in ('f1', 'rejection'):
            row.update({f'{k}_mean': x[k].mean(), f'{k}_min': x[k].min(), f'{k}_max': x[k].max()})
        summ.append(row)
    s = pd.DataFrame(summ)
    order = {'flat': 0, 'u50': 1, 'wide': 2}
    s['_k'] = [{'copied': 0, 'own_eval': 0, 'new': 0, 'diff': 1}[k] for k in s.kind]
    s['_t'] = [order.get(t, 9) for t in s.trained]
    s['_e'] = [order.get(t, 9) for t in s.tested]
    s['_f'] = [FLOWS.index(f) for f in s.flow]
    s = s.sort_values(['_k', '_f', '_t', '_e', 'tested']).drop(columns=['_k', '_t', '_e', '_f']).reset_index(drop=True)
    s.to_csv(R / 'depth_tests.csv', index=False, float_format='%.6f')
    pd.set_option('display.width', 250)
    print(s.drop(columns='source').round(4).to_string(index=False))
    print('wrote', R / 'depth_tests.csv', R / 'depth_tests_rows.csv')


if __name__ == '__main__':
    main()
