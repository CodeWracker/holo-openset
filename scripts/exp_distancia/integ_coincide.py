"""Integration runs (docs/exp_distancia/CADERNO_INTEGRACAO.md): the rows of results/robustness.csv that the distance
study also wrote (same rep, variant, flow in results_exp_distancia/robustness.csv) must coincide.

    python scripts/exp_distancia/integ_coincide.py [variant ...]
"""
import sys

import numpy as np
import pandas as pd

K = ['rep', 'variant', 'flow']
a = pd.read_csv('results/robustness.csv', dtype={'value': str})
b = pd.read_csv('results_exp_distancia/robustness.csv', dtype={'value': str})
if len(sys.argv) > 1:
    b = b[b.variant.isin(sys.argv[1:])]
m = a.merge(b, on=K, suffixes=('_paper', '_study'))
metrics = [c for c in b.columns if c.startswith(('novel_', 'world'))]
print(f'common rows: {len(m)} of {len(b)} study rows; by flow {m.groupby("flow").size().to_dict()}')
print('effect/value equal:', bool((m.effect_paper == m.effect_study).all() and (m.value_paper == m.value_study).all()))
d = {c: float(np.nanmax(np.abs(m[c + '_paper'] - m[c + '_study']))) for c in metrics}
print('largest |paper - study| per metric:', d)
print('largest of all:', max(d.values()))
