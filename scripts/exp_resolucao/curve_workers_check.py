"""Before recording the density curve (CADERNO_CURVA_DENSIDADE.md): (1) the number of scene builders does not change
the images; (2) the wall time per image at a level, with a number of builders.

  same     the first N images of bench_1mm_dense (fill_mean 154) recorded again by generate() into $TMPDIR with
           --workers 1 and with --workers W: holograms, annotations and metadata compared with each other and with
           the stored set (byte for byte)
  timing   N images of a level (fill_mean, depth law d50) recorded by generate() into $TMPDIR with W builders: wall
           seconds per image after the first chunk, and the ready threads of the container sampled meanwhile
Nothing is written under data/; the $TMPDIR copies are deleted.
    python scripts/exp_resolucao/curve_workers_check.py same --n 16 --workers 8 --device cuda:N
    python scripts/exp_resolucao/curve_workers_check.py timing --level 343 --n 96 --workers 8 --device cuda:N
"""
import argparse
import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.model import pick_device
from holo_openset.sim.generate import generate

PHYS_1MM = dict(z0=1.0e-3, oversample=4, margin=394, reach=233)
LAYOUT = dict(letters_mean=8, letters_std=3, letters_min=3, letters_max=18)


def ready_threads():
    out = subprocess.run(['ps', '-eLo', 'stat='], capture_output=True, text=True).stdout.split()
    return sum(s.startswith('R') for s in out)


def same(a, dev):
    tmp = Path(os.environ['TMPDIR']) / 'curve_workers_same'
    ref = paths.dataset('bench_1mm_dense')
    phys = dict(PHYS_1MM, depth_std=2.6e-6, depth_max=7.8e-6)
    res = {}
    for w in (1, a.workers):
        out = tmp / f'w{w}'
        t0 = time.time()
        generate(out, phys=phys, n_images=a.n, per_session=100, workers=w, dev=dev, layout='fresnel',
                 layout_params=dict(LAYOUT, fill_mean=154), log=lambda *x: None)
        res[w] = dict(seconds=time.time() - t0, holo=np.load(out / 'holograms.npy'),
                      ann=(out / 'annotations.csv').read_bytes(), meta=pd.read_csv(out / 'metadata.csv'))
    stored = np.load(ref / 'holograms.npy', mmap_mode='r')[:a.n]
    sann = pd.read_csv(ref / 'annotations.csv')
    sann = sann[sann.image_id < a.n].drop(columns=['split'])
    a1, aw = res[1], res[a.workers]
    t1 = pd.read_csv(tmp / 'w1' / 'annotations.csv').drop(columns=['split'])
    out = dict(n=a.n, workers=[1, a.workers], seconds={str(k): v['seconds'] for k, v in res.items()},
               holograms_equal_between_workers=bool(np.array_equal(a1['holo'], aw['holo'])),
               annotations_equal_between_workers=a1['ann'] == aw['ann'],
               metadata_equal_between_workers=bool(a1['meta'].equals(aw['meta'])),
               holograms_equal_to_stored=bool(np.array_equal(a1['holo'], stored)),
               annotations_equal_to_stored=bool(t1.reset_index(drop=True).equals(sann.reset_index(drop=True))),
               note='the split column differs: a set of one session puts it in train; dropped from the comparison')
    shutil.rmtree(tmp)
    print(json.dumps(out, indent=1))
    return out


def timing(a, dev):
    tmp = Path(os.environ['TMPDIR']) / f'curve_timing_{a.level}_w{a.workers}'
    phys = dict(PHYS_1MM, depth_std=50e-6, depth_max=150e-6)
    samples, stop = [], threading.Event()

    def watch():
        while not stop.is_set():
            samples.append(ready_threads())
            time.sleep(1.0)
    th = threading.Thread(target=watch, daemon=True)
    marks = []
    th.start()
    t0 = time.time()
    generate(tmp, phys=phys, n_images=a.n, per_session=100, workers=a.workers, dev=dev, layout='fresnel',
             layout_params=dict(LAYOUT, fill_mean=a.level), log=lambda *x: marks.append(time.time()))
    total = time.time() - t0
    stop.set()
    th.join()
    meta = pd.read_csv(tmp / 'metadata.csv')
    shutil.rmtree(tmp)
    # marks: 'k/n' at k = 0 (first image recorded) and 'wrote' at the end
    per_img = (marks[-1] - marks[0]) / max(1, a.n - 1)
    out = dict(level=a.level, n=a.n, workers=a.workers, total_s=total, s_per_image_after_first=per_img,
               estimate_5000_min=per_img * 5000 / 60, ready_threads=dict(mean=float(np.mean(samples)),
                                                                         p95=float(np.percentile(samples, 95)),
                                                                         max=int(max(samples))),
               letters_per_window=float((meta.n_letters + meta.n_fill_window).mean()),
               skipped=int(meta.n_fill_skipped.sum()))
    print(json.dumps(out, indent=1))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('what', choices=['same', 'timing'])
    ap.add_argument('--n', type=int, default=16)
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--level', type=int, default=343)
    ap.add_argument('--device', default='cpu')
    a = ap.parse_args()
    torch.set_num_threads(4)
    dev = pick_device(a.device)
    res = same(a, dev) if a.what == 'same' else timing(a, dev)
    p = paths.RESULTS / 'curve_workers_check.json'
    allr = json.load(open(p)) if p.exists() else {}
    allr[a.what if a.what == 'same' else f'timing_L{a.level}_w{a.workers}'] = res
    json.dump(allr, open(p, 'w'), indent=1)


if __name__ == '__main__':
    main()
