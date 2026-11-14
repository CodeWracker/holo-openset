"""n* on the full frame, GPU (min_s), with each of the two GPU attempts of the E5 timing session (e5_a1, e5_a2),
complete and simple accounting (holo_openset.paper.distance.break_even). From the root of the repository, after
source scripts/exp_distancia/env.sh:   python scripts/exp_distancia/nstar_attempts.py"""
import pandas as pd

from holo_openset.paper import distance as D

R = 'results_exp_distancia'
for a in ['e5_a1', 'e5_a2']:
    df = pd.read_csv(f'{R}/{a}/timing_gpu.csv')
    x = df[(df.height == 2748) & (df.width == 3840)]
    t = dict(zip(x.stage, x.min_s.astype(float)))
    for s in D.STACKS:
        for name, stage, _, _ in D.SEARCHES[:2]:
            print(a, s, name, 'full %.3f' % D.break_even(t, s, stage), 'simple %.3f' % D.break_even(t, s, stage, True))
    print(a, {k: round(t[k] * 1e3, 4) for k in ['flat_field', 'backprop', 'channels', 'layer_bank_jit', 'layer_bank_wide',
                                                'layer_bank_w2', 'autofocus', 'autofocus_afc']})
