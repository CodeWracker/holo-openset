"""P2 / D of the pilot at 1.0 mm: training with the depth spread of the base set (50 / 150 um) against the pilot's
(2.6 / 7.8 um), r1, test split, open-set F1 and rejection of raw, prop, rec_z0. Each model keeps the gallery and the
threshold of the validation split of the set it was trained on.
  trained 2.6 / tested 2.6   $HOLO_RESULTS/eval/bench_1mm/<flow>_r1.json
  trained 2.6 / tested 50    robustness_bench_1mm.csv, variant depth50 (read in r1, copied)
  trained 50 / tested 50     $HOLO_RESULTS/eval/bench_1mm_depth50/<flow>_r1.json
  trained 50 / tested 2.6    robustness_bench_1mm_depth50.csv, variant bench_1mm (experiment robustness --set
                             bench_1mm_depth50 --variants-root . --variants bench_1mm)
-> $HOLO_RESULTS/depth_training.csv

    python scripts/exp_resolucao/depth_training.py
"""
import json

import pandas as pd

from holo_openset import paths

FLOWS = ['raw', 'prop', 'rec_z0']
M = {'f1': 'novel_open_macro_f1', 'rejection': 'novel_unknown_rejection', 'closed_acc': 'novel_closed_acc'}


def main():
    R = paths.RESULTS
    rob = pd.read_csv(R / 'robustness_bench_1mm.csv')
    rob50 = pd.read_csv(R / 'robustness_bench_1mm_depth50.csv')
    rows = []
    for f in FLOWS:
        src = {('2.6', '2.6'): json.load(open(R / 'eval' / 'bench_1mm' / f'{f}_r1.json')),
               ('2.6', '50'): rob[(rob.rep == 1) & (rob.variant == 'depth50') & (rob.flow == f)].iloc[0].to_dict(),
               ('50', '50'): json.load(open(R / 'eval' / 'bench_1mm_depth50' / f'{f}_r1.json')),
               ('50', '2.6'): rob50[(rob50.rep == 1) & (rob50.variant == 'bench_1mm') & (rob50.flow == f)].iloc[0]
               .to_dict()}
        for (tr, te), d in src.items():
            rows.append(dict(trained_um=tr, tested_um=te, flow=f, rep=1, **{k: d[v] for k, v in M.items()}))
    t = pd.DataFrame(rows)
    t.to_csv(R / 'depth_training.csv', index=False, float_format='%.4f')
    print(t.pivot_table(index=['trained_um', 'tested_um'], columns='flow', values=['f1', 'rejection']).round(4)
          .to_string())


if __name__ == '__main__':
    main()
