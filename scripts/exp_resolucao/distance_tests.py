"""Table of the distance tests, round d1 (CADERNO_CURVA.md Q0 item d; CADERNO_CURVA_DISTANCIA.md): the five models of
the pilot (bench_1mm, trained at 1.0 mm) at 0.7, 0.9, 1.0 and 1.1 mm. Nothing is evaluated here: the rows are read.

  1.0 mm   rows `base` of robustness_bench_1mm.csv (copied; they equal the eval json of bench_1mm)
  0.7 mm   rows `z07` of robustness_bench_1mm.csv and recal_bench_1mm_z07.json (copied; pilot_1mm.sh)
  0.9 mm   rows `z09` / `z11` of robustness_bench_1mm_dist.csv and recal_bench_1mm_z09.json / _z11.json
  1.1 mm   (distance_tests.sh)
Conditions: as_is (models, gallery, threshold of 1.0 mm; rec_z0 at 1.0 mm), recal_literal (flow+recal: the alpha
recalibrated without labels replaces the trained one; rec_z0 at the recalibrated z), recal_ratio (flow+recal_ratio:
the trained alpha times alpha / alpha_ref; rec_z0 at 1.0 mm times the ratio). Metrics: novel_open_macro_f1 (f1) and
novel_unknown_rejection (rejection), test split, threshold from validation.

  distance_tests_rows.csv   per repetition: kind = metric (distance, flow, condition: f1, rejection, closed and known
                            accuracy, source file), loss_as_is (as is - 1.0 mm, same flow and repetition),
                            recovered (recalibrated - as is), rec_minus_prop (rec_z0 recalibrated, literal or by ratio,
                            - prop recalibrated by ratio)
  distance_tests.csv        the same kinds, mean / min / max / n over the five repetitions; and kind = recal: the
                            distance the recalibration found (z of the literal variant, z_ratio of the ratio variant,
                            z_ref of the same calibration on the same ids at 1.0 mm) against the true one (the mean
                            session distance of the 32 validation holograms it used, from the set's metadata.csv),
                            and the nominal one, in mm

    python scripts/exp_resolucao/distance_tests.py

Round d2 (CADERNO_CURVA.md Q1), --family u50: the five models of the sparse level of the standard family
(curve_u50_L008), all three other distances read from robustness_curve_u50_L008_dist.csv and
recal_curve_u50_L008_z<ZZ>.json (distance_tests.sh FAM=u50), the 1.0 mm row copied from the eval json of the set
(eval/curve_u50_L008/<flow>_r<n>.json) -> distance_tests_u50.csv, distance_tests_u50_rows.csv.

    python scripts/exp_resolucao/distance_tests.py --family u50
"""
import argparse
import json

import numpy as np
import pandas as pd

from holo_openset import paths

REPS = [1, 2, 3, 4, 5]
FLOWS = ['raw', 'prop', 'rec_z0']
DIST = {'z07': 0.7, 'base': 1.0, 'z09': 0.9, 'z11': 1.1}
SRC = {'z07': 'robustness_bench_1mm.csv', 'base': 'robustness_bench_1mm.csv', 'z09': 'robustness_bench_1mm_dist.csv',
       'z11': 'robustness_bench_1mm_dist.csv'}
COND = {'': 'as_is', '+recal': 'recal_literal', '+recal_ratio': 'recal_ratio'}
MET = {'f1': 'novel_open_macro_f1', 'rejection': 'novel_unknown_rejection', 'closed_acc': 'novel_closed_acc',
       'known_acc': 'novel_known_acc'}


FAMILIES = {
    # d1: robustness_bench_1mm.csv holds 0.7 mm and the 1.0 mm rows (`base`), robustness_bench_1mm_dist.csv the rest
    'pilot': dict(set='bench_1mm', src=SRC, base_from_eval=False, out='distance_tests'),
    # d2: every distance in its own csv; 1.0 mm from the eval json of the set
    'u50': dict(set='curve_u50_L008', src={v: 'robustness_curve_u50_L008_dist.csv' for v in DIST if v != 'base'},
                base_from_eval=True, out='distance_tests_u50'),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--family', default='pilot', choices=list(FAMILIES))
    fam = FAMILIES[ap.parse_args().family]
    R = paths.RESULTS
    rows = []
    if fam['base_from_eval']:
        for rep in REPS:
            for f in FLOWS:
                p = R / 'eval' / fam['set'] / f'{f}_r{rep}.json'
                j = json.load(open(p))
                rows.append(dict(kind='metric', distance_mm=1.0, flow=f, condition='as_is', rep=rep,
                                 **{k: j[c] for k, c in MET.items()}, source=str(p.relative_to(R))))
    for v, d in DIST.items():
        if v == 'base' and fam['base_from_eval']:
            continue
        src = fam['src'][v]
        t = pd.read_csv(R / src)
        t = t[(t.variant == v) & t.rep.isin(REPS)]
        for _, r in t.iterrows():
            flow, cond = r.flow, ''
            for suf in ('+recal_ratio', '+recal'):
                if flow.endswith(suf):
                    flow, cond = flow[:-len(suf)], suf
                    break
            rows.append(dict(kind='metric', distance_mm=d, flow=flow, condition=COND[cond], rep=int(r.rep),
                             **{k: r[c] for k, c in MET.items()}, source=src))
    m = pd.DataFrame(rows)
    key = ['distance_mm', 'flow', 'condition', 'rep']
    assert not m.duplicated(key).any()
    assert len(m[m.condition == 'as_is']) == 4 * 3 * len(REPS), 'an as-is row is missing'
    # the 1.0 mm rows are those of the eval json of the set
    for _, r in m[m.distance_mm == 1.0].iterrows():
        j = json.load(open(R / 'eval' / fam['set'] / f'{r.flow}_r{r.rep}.json'))
        assert abs(j['novel_open_macro_f1'] - r.f1) < 1e-9 and abs(j['novel_unknown_rejection'] - r.rejection) < 1e-9
    ix = m.set_index(key)
    der = []
    for (d, flow, cond, rep), r in ix.iterrows():
        if d == 1.0:
            continue
        if cond == 'as_is':
            ref = ix.loc[(1.0, flow, 'as_is', rep)]
            der.append(dict(kind='loss_as_is', distance_mm=d, flow=flow, condition='as_is - 1.0 mm', rep=rep,
                            f1=r.f1 - ref.f1, rejection=r.rejection - ref.rejection))
        else:
            ref = ix.loc[(d, flow, 'as_is', rep)]
            der.append(dict(kind='recovered', distance_mm=d, flow=flow, condition=f'{cond} - as_is', rep=rep,
                            f1=r.f1 - ref.f1, rejection=r.rejection - ref.rejection))
            if flow == 'rec_z0' and (d, 'prop', 'recal_ratio', rep) in ix.index:
                p = ix.loc[(d, 'prop', 'recal_ratio', rep)]
                der.append(dict(kind='rec_minus_prop', distance_mm=d, flow='rec_z0 - prop',
                                condition=f'rec_z0 {cond} - prop recal_ratio', rep=rep,
                                f1=r.f1 - p.f1, rejection=r.rejection - p.rejection))
    per = pd.concat([m, pd.DataFrame(der)], ignore_index=True)
    order = {k: i for i, k in enumerate(['metric', 'loss_as_is', 'recovered', 'rec_minus_prop'])}
    per = per.sort_values(['kind', 'distance_mm', 'flow', 'condition', 'rep'],
                          key=lambda s: s.map(order) if s.name == 'kind' else s).reset_index(drop=True)
    per.to_csv(R / f"{fam['out']}_rows.csv", index=False, float_format='%.6f')

    summ = []
    for (kind, d, flow, cond), x in per.groupby(['kind', 'distance_mm', 'flow', 'condition'], sort=False):
        row = dict(kind=kind, distance_mm=d, flow=flow, condition=cond, n=len(x))
        for k in ('f1', 'rejection'):
            row.update({f'{k}_mean': x[k].mean(), f'{k}_min': x[k].min(), f'{k}_max': x[k].max()})
        summ.append(row)
    for v, d in DIST.items():
        if v == 'base':
            continue
        j = json.load(open(R / f"recal_{fam['set']}_{v}.json"))
        meta = pd.read_csv(paths.dataset(j['set']) / 'metadata.csv').set_index('image_id')
        z_true = float(meta.loc[j['image_ids']].z.mean() * 1e3)
        meta_ref = pd.read_csv(paths.dataset(j['ref']) / 'metadata.csv').set_index('image_id')
        z_true_ref = float(meta_ref.loc[j['image_ids']].z.mean() * 1e3)
        summ.append(dict(kind='recal', distance_mm=d, flow='prop, rec_z0', condition='calibration (32 val holograms)',
                         n=j['n'], z_nominal_mm=j['nominal_z0_of_set'] * 1e3, z_true_mm=z_true,
                         z_literal_mm=j['z'] * 1e3, z_ratio_mm=j['z_ratio'] * 1e3,
                         z_literal_minus_true_mm=j['z'] * 1e3 - z_true, z_ratio_minus_true_mm=j['z_ratio'] * 1e3 - z_true,
                         alpha=j['alpha'], alpha_ref=j['alpha_ref'], ratio=j['ratio'], z_ref_mm=j['z_ref'] * 1e3,
                         z_true_ref_mm=z_true_ref, source=f"recal_{fam['set']}_{v}.json"))
    s = pd.DataFrame(summ)
    s.to_csv(R / f"{fam['out']}.csv", index=False, float_format='%.6f')
    pd.set_option('display.width', 250)
    pd.set_option('display.max_columns', 30)
    print(s[s.kind != 'recal'].drop(columns=[c for c in s.columns if c.startswith(('z_', 'alpha', 'ratio', 'source'))])
          .round(4).to_string(index=False))
    print(s[s.kind == 'recal'].dropna(axis=1).round(5).to_string(index=False))
    print('wrote', R / f"{fam['out']}.csv", R / f"{fam['out']}_rows.csv")


if __name__ == '__main__':
    main()
