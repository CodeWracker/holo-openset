"""Largest |z / z0 - 1| on the test split of the window sets and the full frames, and what the cheap search (afc)
found on the farthest image of frame_5. From the root of the repository, after source scripts/exp_distancia/env.sh:
    python scripts/exp_distancia/range_check.py"""
import pandas as pd
from holo_openset.sim.physics import Z0
for s in ['realistic', 'variants/session_2', 'variants/session_5', 'variants/fullwell_500', 'variants/beam_narrow',
          'variants/frame_2', 'variants/frame_5', 'variants/walk_05', 'full_frames', 'full_frames_frame5']:
    m = pd.read_csv(f'data/{s}/metadata.csv')
    m = m[m.split == 'test'] if 'split' in m else m
    r = m.z / Z0 - 1
    print(f'{s}: n {len(m)}, z/z0 - 1 in [{r.min():+.4f}, {r.max():+.4f}], beyond +-10 %: {(r.abs() > 0.10).sum()}, '
          f'beyond +-13.33 %: {(r.abs() > 0.4 / 3).sum()}')
e = pd.read_csv('results_exp_distancia/autofocus_logs/variants/frame_5/autofocus_afc.csv')
e['dev'] = e.true_z / Z0 - 1
x = e.loc[e.dev.abs().idxmax()]
print(f'frame_5, largest deviation: image {int(x.image_id)}, true z {x.true_z * 1e3:.4f} mm ({x.dev:+.4f}), afc '
      f'{x.z_af * 1e3:.4f} mm ({x.z_af / Z0 - 1:+.4f}), error {abs(x.z_af - x.true_z) * 1e6:.1f} um')
