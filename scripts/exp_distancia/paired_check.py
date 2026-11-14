"""Paired difference of open-set F1, rec_afc - rec_af, mean over the repetitions with 5 decimals, on the six window
sets without strong noise or a narrow beam (the tables give 3). From the root of the repository, after
source scripts/exp_distancia/env.sh:   python scripts/exp_distancia/paired_check.py"""
import pandas as pd

from holo_openset.paper import distance as D

d = pd.read_csv('results_exp_distancia/robustness.csv')
worst = 0.0
for v in ['base', 'session_2', 'session_5', 'frame_2', 'frame_5', 'walk_05']:
    x = (D.per_rep(d, D.F1, variant=v, flow='rec_afc') - D.per_rep(d, D.F1, variant=v, flow='rec_af')).dropna()
    worst = max(worst, abs(x.mean()))
    print(f'{v}: {x.mean():+.5f} ({len(x)} repetitions)')
print(f'largest |mean|: {worst:.5f}')
