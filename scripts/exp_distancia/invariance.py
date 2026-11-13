"""Invariance of what the paper rests on (protocol, section 6.1): with the new effects off, the code of the distance
study must record the same holograms and write the same reconstructions as the code of the paper.

    python scripts/exp_distancia/invariance.py --device cuda:N            # the set variants/session_5 of stage 0
    python scripts/exp_distancia/invariance.py --device cuda:N --base     # the whole base set, against its checksums

  1. variants/session_5 is recorded again into data/_check/session_5 and compared with data/variants/session_5, which
     the code of the paper wrote at stage 0: holograms, blank frames, annotations, metadata, dust, sessions;
  2. its caches rec_z0 and rec_af and its autofocus.csv are rebuilt and compared;
  3. --base: the base set is recorded again into data/_check/realistic and compared with data/realistic and with
     checksums/data.sha256.
Nothing outside data/_check is written.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

from holo_openset import paths
from holo_openset.model import pick_device
from holo_openset.reconstruct import build_caches
from holo_openset.reproduce import read_sums, sha256
from holo_openset.sim import generate as G
from holo_openset.sim.variants import VARIANTS

NEW_FIELDS = ('frame_z_std', 'frame_z_walk', 'tilt_deg')
OK = True


def report(name, same, detail=''):
    global OK
    OK &= bool(same)
    print(f"{'identical' if same else 'DIFFERENT'}  {name}  {detail}", flush=True)


def arrays(name, a, b):
    a, b = np.load(a, mmap_mode='r'), np.load(b, mmap_mode='r')
    if a.shape != b.shape:
        return report(name, False, f'shapes {a.shape} {b.shape}')
    diff, sq, n = 0, 0.0, 0
    for k in range(0, len(a), 64):
        d = np.asarray(a[k:k + 64], np.float32) - np.asarray(b[k:k + 64], np.float32)
        diff += int((d != 0).sum())
        sq += float((d ** 2).sum())
        n += d.size
    report(name, diff == 0, f'{a.shape} {diff / n:.4%} of the values differ, rms {np.sqrt(sq / n):.4f}')


def texts(name, a, b):
    report(name, Path(a).read_bytes() == Path(b).read_bytes())


def physics(name, a, b):
    pa, pb = json.load(open(a)), json.load(open(b))
    for p in (pa, pb):
        for k in NEW_FIELDS:
            assert p['physics'].get(k, 0.0) == 0.0, f'{k} is on'
            p['physics'].pop(k, None)
        p.pop('like', None)
    report(name, pa == pb, '(without the new fields, all of them off)')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--device', default='cuda:0')
    ap.add_argument('--base', action='store_true', help='record the whole base set again (hours)')
    ap.add_argument('--workers', type=int, default=8)
    a = ap.parse_args()
    dev = pick_device(a.device)
    check = paths.DATA / '_check'
    base = paths.dataset(paths.BASE)
    if not a.base:
        old, new = paths.dataset('variants/session_5'), check / 'session_5'
        if not (new / 'physics.json').exists():
            G.generate(new, phys=VARIANTS['session_5'][2], like=base, split='test', workers=a.workers, dev=dev)
        for f in ['holograms.npy', 'backgrounds.npy']:
            arrays(f'session_5/{f}', old / f, new / f)
        for f in ['annotations.csv', 'metadata.csv', 'dust.csv', 'sessions.csv']:
            texts(f'session_5/{f}', old / f, new / f)
        physics('session_5/physics.json', old / 'physics.json', new / 'physics.json')
        if not (new / 'autofocus.csv').exists():
            build_caches(new, ['z0', 'af'], dev)
        for f in ['rec_z0.npy', 'rec_af.npy']:
            arrays(f'session_5/{f}', old / f, new / f)
        texts('session_5/autofocus.csv', old / 'autofocus.csv', new / 'autofocus.csv')
    else:
        new = check / 'realistic'
        if not (new / 'physics.json').exists():
            G.generate(new, n_images=5000, workers=a.workers, dev=dev)
        sums = read_sums(paths.CHECKSUMS / 'data.sha256')
        for f in ['holograms.npy', 'backgrounds.npy']:
            arrays(f'realistic/{f}', base / f, new / f)
            report(f'realistic/{f} against checksums/data.sha256', sha256(new / f) == sums[f'realistic/{f}'])
        for f in ['annotations.csv', 'metadata.csv', 'dust.csv', 'sessions.csv']:
            texts(f'realistic/{f}', base / f, new / f)
        physics('realistic/physics.json', base / 'physics.json', new / 'physics.json')
    print('ALL IDENTICAL' if OK else 'SOMETHING DIFFERS')
    sys.exit(0 if OK else 1)


if __name__ == '__main__':
    main()
