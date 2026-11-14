"""Is the difference between data/full_frames_tilt0 (code of the study, tilt and jitter off) and data/full_frames (the
published frames) a difference of code or of build? Records the first N full frames again with the code of the PAPER
(a copy of the package at the commit of the paper, e.g. `git archive 9488fce holo_openset | tar -x -C DIR`) on this
machine, and compares them with both sets. Frame k depends only on its own seeds, so the first N frames of a run of N
are the first N of the run of 40.

    python scripts/exp_distancia/frames_build_check.py --paper-code DIR --out DIR2 --n 8 --device cuda:0

Writes only to --out (keep it out of data/).
"""
import argparse
import sys
from pathlib import Path


def compare(name, a, b):
    import numpy as np
    d = np.abs(a.astype(np.float64) - b.astype(np.float64))
    print(f'{name}: {a.shape}, differing {(d > 0).mean() * 100:.4f} %, max |diff| {d.max():g}, '
          f'identical: {bool((d == 0).all())}', flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--paper-code', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--n', type=int, default=8)
    ap.add_argument('--device', default='cuda:0')
    ap.add_argument('--workers', type=int, default=1)
    a = ap.parse_args()
    sys.path.insert(0, str(Path(a.paper_code).resolve()))
    import numpy as np
    import pandas as pd
    import holo_openset
    from holo_openset.sim import generate as G
    print('package from', Path(holo_openset.__file__).parent, flush=True)
    assert Path(holo_openset.__file__).resolve().is_relative_to(Path(a.paper_code).resolve())
    data = Path(__file__).resolve().parents[2] / 'data'
    out = Path(a.out)
    if not (out / 'holograms.npy').exists():
        G.full_frames(data / 'realistic', out, n_images=a.n, workers=a.workers, dev=a.device)
    new = np.load(out / 'holograms.npy')
    sessions = pd.read_csv(out / 'metadata.csv').session.unique()
    for ref in ['full_frames_tilt0', 'full_frames']:
        old = np.load(data / ref / 'holograms.npy', mmap_mode='r')[:len(new)]
        compare(f'paper code, this build, against {ref}: holograms', new, np.asarray(old))
        bo = np.load(data / ref / 'backgrounds.npy', mmap_mode='r')
        bn = np.load(out / 'backgrounds.npy', mmap_mode='r')
        compare(f'paper code, this build, against {ref}: blank frames of the test sessions',
                np.asarray(bn[sessions]), np.asarray(bo[sessions]))
        for f in ['annotations.csv', 'metadata.csv']:
            x, y = pd.read_csv(out / f), pd.read_csv(data / ref / f)
            y = y[y.image_id < len(new)].reset_index(drop=True)
            print(f'  {f} of the first {len(new)} frames equal to {ref}: {x.equals(y)}', flush=True)


if __name__ == '__main__':
    main()
