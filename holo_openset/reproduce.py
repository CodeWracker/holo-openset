"""Reproduce the numbers of the paper at three levels (docs/REPRODUCIBILITY.md).

    python -m holo_openset reproduce check                     # level 1: tables and numbers from results/, CPU
    python -m holo_openset reproduce download                  # level 2: models and holograms from Zenodo
    python -m holo_openset reproduce evaluate --gpus 0         # level 2: evaluate the trained models again
    python -m holo_openset reproduce full --gpus 0 1 2 3       # level 3: everything from the seeds
    python -m holo_openset reproduce compare output/level2/results
    python -m holo_openset reproduce verify-data               # checksums of the data on disk
    python -m holo_openset reproduce compare-data OTHER_DATA   # a regenerated set against the published one
    python -m holo_openset reproduce package OUT               # maintainers: the archives of the Zenodo record

`check` must match expected/ byte by byte. `compare` allows a tolerance: a new run on other hardware gives close, not
identical, numbers, and the times of the stages depend on the machine.
"""
import filecmp
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

from holo_openset import paths

ZENODO_RECORD = None   # set when the data record is published
# what the Zenodo record holds: archive -> paths inside it, relative to data/ or models/
SET_FILES = ['holograms.npy', 'backgrounds.npy', 'annotations.csv', 'metadata.csv', 'sessions.csv', 'dust.csv',
             'physics.json', 'objects', 'labels']
DATA_SETS = ['realistic', 'ideal', 'small_z0', 'small_near', 'full_frames']
MODEL_SETS = ['realistic', 'ideal', 'small_z0', 'small_near']
# level 2: everything that needs neither new scenes nor training
LEVEL2_JOBS = ['rec_base', 'rec_ideal', 'rec_small', 'eval_', 'exp_e2e', 'exp_discovery', 'exp_full_frames',
               'exp_fidelity']
# macros that measure the machine, not the method
MACHINE = re.compile(r'^(T[A-Z]|Full.*(S|Ms)$|TrainMinutes)')
NUM = re.compile(r'\\newcommand\{\\(\w+)\}\{([^}]*)\}')
TOLERANCE = 0.01


def sh(*cmd, env=None):
    print('$', ' '.join(map(str, cmd)), flush=True)
    return subprocess.run(list(map(str, cmd)), env={**os.environ, **(env or {})}, cwd=paths.PROJECT).returncode


def tables(out, results=None):
    """Tables and numbers.tex of the paper from a results directory, written to `out`."""
    env = {'HOLO_PAPER': str(out)}
    if results:
        env['HOLO_RESULTS'] = str(results)
    return sh(sys.executable, '-m', 'holo_openset', 'paper', 'tables', env=env)


def check():
    """Level 1: the tables and numbers of the paper, rebuilt from results/, against expected/."""
    with tempfile.TemporaryDirectory() as t:
        out = Path(t)
        if tables(out):
            return 1
        names = ['numbers.tex'] + [f'tables/{p.name}' for p in sorted((paths.EXPECTED / 'tables').glob('*.tex'))]
        bad = [n for n in names if not (out / n).exists() or not filecmp.cmp(out / n, paths.EXPECTED / n, shallow=False)]
    print(f'{len(names) - len(bad)}/{len(names)} files identical to expected/')
    for n in bad:
        print('  differs:', n)
    return 1 if bad else 0


def macros(f):
    return dict(NUM.findall(Path(f).read_text()))


def compare(results):
    """A new run against the paper: every number within the tolerance, the times of the machine set apart."""
    with tempfile.TemporaryDirectory() as t:
        if tables(t, results):
            return 1
        new, old = macros(Path(t) / 'numbers.tex'), macros(paths.EXPECTED / 'numbers.tex')
    same, close, far, machine, text = 0, 0, [], 0, 0
    for k, v in old.items():
        if MACHINE.match(k):
            machine += 1
            continue
        try:
            a, b = float(v), float(new.get(k, 'nan'))
        except ValueError:
            text += 1
            same += new.get(k) == v
            continue
        if a == b:
            same += 1
        elif abs(a - b) <= max(TOLERANCE, 0.01 * abs(a)):
            close += 1
        else:
            far.append((k, v, new.get(k)))
    print(f'{same} identical, {close} within {TOLERANCE} or 1 %, {len(far)} further apart, {machine} machine-dependent '
          f'(not compared), {text} text')
    for k, v, w in far:
        print(f'  {k}: paper {v}, this run {w}')
    return 1 if far else 0


def evaluate(gpus):
    """Level 2: reconstructions, evaluations and experiments from the downloaded models and holograms."""
    out = paths.PROJECT / 'output/level2'
    env = {'HOLO_RESULTS': str(out / 'results'), 'HOLO_LOGS': str(out / 'logs')}
    (out / 'results').mkdir(parents=True, exist_ok=True)
    for f in ['figure_numbers.json', 'run_summary.json', 'gaps.json', 'robustness.csv', 'oracle.csv', 'timing_cpu.csv',
              'timing_gpu.csv']:   # not rerun at this level
        shutil.copy(paths.RESULTS / f, out / 'results' / f)
    rc = sh(sys.executable, '-m', 'holo_openset.pipeline', '--gpus', *gpus, '--assume-done', 'simulate', 'yolo', 'train',
            '--match', *LEVEL2_JOBS, env=env)
    return rc or compare(out / 'results')


def full(gpus):
    """Level 3: the whole pipeline, then every table and figure."""
    rc = sh(sys.executable, '-m', 'holo_openset.pipeline', '--gpus', *gpus)
    return rc or compare(paths.RESULTS)


def sha256(f):
    h = hashlib.sha256()
    with open(f, 'rb') as o:
        for b in iter(lambda: o.read(1 << 24), b''):
            h.update(b)
    return h.hexdigest()


def read_sums(f):
    return {name: s for s, name in (ln.split(maxsplit=1) for ln in Path(f).read_text().splitlines() if ln.strip())}


def verify_data():
    """Checksums of the holograms on disk, the proof that a regenerated set is the set of the paper."""
    sums = read_sums(paths.CHECKSUMS / 'data.sha256')
    missing, bad, good = 0, [], 0
    for name, s in sums.items():
        f = paths.DATA / name
        if not f.exists():
            missing += 1
        elif sha256(f) == s:
            good += 1
        else:
            bad.append(name)
    print(f'{good} files match, {len(bad)} differ, {missing} not on disk')
    for n in bad:
        print('  differs:', n)
    return 1 if bad else 0


def compare_data(other, sets=('realistic',)):
    """A rebuilt set against the one on disk. The simulation repeats exactly on one build of the software; another
    build of CUDA rounds differently, and a few pixels of each image move."""
    import numpy as np
    for s in sets:
        a = np.load(paths.DATA / s / 'holograms.npy', mmap_mode='r')
        b = np.load(Path(other) / s / 'holograms.npy', mmap_mode='r')
        n = min(len(a), len(b))
        step = max(1, n // 200)
        d = [np.asarray(a[i], np.float32) - np.asarray(b[i], np.float32) for i in range(0, n, step)]
        d = np.stack(d)
        print(f'{s}: {n} images compared in steps of {step}; {(d != 0).mean():.4%} of the pixels differ, '
              f'rms {np.sqrt((d ** 2).mean()):.3f} grey levels')
    return 0


def download(record=None):
    record = record or ZENODO_RECORD
    if record is None:
        print('The Zenodo record is not published yet: pass --record, or rebuild the data with level 3.')
        return 1
    sums = read_sums(paths.CHECKSUMS / 'zenodo.sha256')
    tmp = paths.PROJECT / 'output/download'
    tmp.mkdir(parents=True, exist_ok=True)
    for name, s in sums.items():
        f = tmp / name
        if not (f.exists() and sha256(f) == s):
            url = f'https://zenodo.org/records/{record}/files/{name}?download=1'
            print('downloading', url, flush=True)
            urllib.request.urlretrieve(url, f)
            if sha256(f) != s:
                print('checksum mismatch:', name)
                return 1
        root = paths.DATA if name.startswith('data_') else paths.MODELS
        root.mkdir(parents=True, exist_ok=True)
        with tarfile.open(f) as t:
            t.extractall(root, filter='data')
    return 0


def package(out):
    """Maintainers: one tar per set (Zenodo takes at most 100 files per record), with their checksums."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    lines = []
    for s in DATA_SETS:
        f = out / f'data_{s}.tar'
        with tarfile.open(f, 'w') as t:
            for n in SET_FILES:
                p = paths.DATA / s / n
                if p.exists():
                    t.add(p, arcname=f'{s}/{n}')
        lines.append(f'{sha256(f)}  {f.name}')
        print(lines[-1], flush=True)
    for s in MODEL_SETS:
        f = out / f'models_{s}.tar'
        with tarfile.open(f, 'w') as t:
            for p in sorted((paths.MODELS / s).glob('*.pt')):
                t.add(p, arcname=f'{s}/{p.name}')
        lines.append(f'{sha256(f)}  {f.name}')
        print(lines[-1], flush=True)
    paths.CHECKSUMS.mkdir(exist_ok=True)
    (paths.CHECKSUMS / 'zenodo.sha256').write_text('\n'.join(lines) + '\n')
    return 0


def write_data_sums():
    """Maintainers: checksums of the holograms and blank frames of every set, auxiliary and robustness sets included."""
    files = sorted(p for n in ['holograms*.npy', 'backgrounds*.npy'] for p in paths.DATA.rglob(n))
    lines = [f'{sha256(p)}  {p.relative_to(paths.DATA)}' for p in files]
    paths.CHECKSUMS.mkdir(exist_ok=True)
    (paths.CHECKSUMS / 'data.sha256').write_text('\n'.join(lines) + '\n')
    print(len(lines), 'files')
    return 0


def main(a):
    fn = {'check': check, 'verify-data': verify_data, 'write-data-sums': write_data_sums}.get(a.what)
    if fn:
        return fn()
    if a.what == 'download':
        return download(a.record)
    if a.what == 'evaluate':
        return evaluate(a.gpus)
    if a.what == 'full':
        return full(a.gpus)
    if a.what == 'compare':
        return compare(a.path)
    if a.what == 'compare-data':
        return compare_data(a.path)
    return package(a.path)
