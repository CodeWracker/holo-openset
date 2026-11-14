"""Sanity (a) of T3: the set reduced with b = 1 is the set of the sensor, byte for byte (holograms, blank frames, csv
files, auxiliary scenes of r1, and the back-propagation cache rebuilt through the pixel-aware path).

    python scripts/exp_resolucao/check_b1.py
"""
import filecmp
import hashlib

from holo_openset import paths

PAIRS = [('realistic', 'realistic_b1', ['holograms.npy', 'backgrounds.npy', 'annotations.csv', 'metadata.csv',
                                       'sessions.csv', 'dust.csv', 'aux/r1_images.npy', 'aux/r1_boxes.csv',
                                       'rec_z0.npy'])]
PAIRS += [(f'variants_val/{v}', f'variants_val_b1/{v}', ['holograms.npy', 'backgrounds.npy', 'annotations.csv',
                                                         'metadata.csv', 'sessions.csv', 'dust.csv'])
          for v in ('fullwell_500', 'beam_narrow')]


def sha(p, n=1 << 24):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while b := f.read(n):
            h.update(b)
    return h.hexdigest()[:16]


def main():
    bad = 0
    for a, b, files in PAIRS:
        for f in files:
            pa, pb = paths.dataset(a) / f, paths.dataset(b) / f
            if not pb.exists():
                print('missing', pb)
                bad += 1
                continue
            same = filecmp.cmp(pa, pb, shallow=False)
            bad += not same
            print('identical' if same else 'DIFFERENT', f'{a}/{f}', sha(pb) if pb.stat().st_size < 3e9 else '')
    print('all identical' if not bad else f'{bad} differ or missing')


if __name__ == '__main__':
    main()
