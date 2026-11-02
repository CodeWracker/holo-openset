"""Everything the paper reports, from the simulation to the results, as one queue of jobs.

    python -m holo_openset.pipeline --gpus 3 5 [--jobs-per-gpu 2] [--only train evaluate] [--dry-run]

Each job is one `python -m holo_openset ...` command on ONE device (a GPU of --gpus, or the CPU); jobs whose
dependencies are done are started on the GPU with the fewest running jobs, at most --jobs-per-gpu per GPU and only
while it has --min-free-mb of free memory. A job that succeeded leaves logs/done/<name>.ok and is not run again; its output
is in logs/<name>.log.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from holo_openset import paths
from holo_openset.flows import FLOWS
from holo_openset.sim.variants import VARIANTS

REPS = [1, 2, 3, 4, 5]
PY = [sys.executable, '-m', 'holo_openset']
ALL = list(FLOWS)
IDEAL_FLOWS = ['raw', 'learned', 'complex', 'wiener', 'prop', 'rec_z0']
SMALL_FLOWS = ['raw', 'learned', 'complex', 'wiener', 'prop', 'bank_jit', 'bank_w3', 'rec_z0', 'rec_af', 'rec_twin']


def jobs():
    """name -> (stage, command after `python -m holo_openset`, dependencies, device: 'gpu' | 'cpu')."""
    J = {}

    def add(name, stage, cmd, deps=(), dev='gpu'):
        J[name] = (stage, cmd, list(deps), dev)

    add('sim_base', 'simulate', ['simulate', 'base', '--workers', '16'])
    add('sim_ideal', 'simulate', ['simulate', 'ideal', '--workers', '16'], ['sim_base'])
    for r in REPS:
        add(f'sim_aux_r{r}', 'simulate', ['simulate', 'aux', '--rep', str(r), '--workers', '16'], ['sim_base'])
        add(f'sim_aux_ideal_r{r}', 'simulate', ['simulate', 'aux', '--set', 'ideal', '--rep', str(r), '--workers', '16'],
            ['sim_ideal'])
    add('sim_variants', 'simulate', ['simulate', 'variants', '--workers', '16'], ['sim_base'])
    add('sim_full', 'simulate', ['simulate', 'full', '--n-images', '40', '--workers', '16'], ['sim_base'])
    add('sim_small', 'simulate', ['simulate', 'small', '--workers', '16'], ['sim_base'])

    add('rec_base', 'reconstruct', ['reconstruct'], ['sim_base'])
    add('rec_ideal', 'reconstruct', ['reconstruct', '--set', 'ideal', '--methods', 'z0'], ['sim_ideal'])
    for s in ['small_z0', 'small_near']:
        add(f'rec_{s}', 'reconstruct', ['reconstruct', '--set', s, '--methods', 'z0', 'af', 'twin'], ['sim_small'])
    for r in REPS:
        add(f'rec_aux_r{r}', 'reconstruct', ['reconstruct', '--aux', f'r{r}'], [f'sim_aux_r{r}'])
        add(f'rec_aux_cal_r{r}', 'reconstruct', ['reconstruct', '--aux', f'r{r}_cal', '--methods', 'z0'],
            [f'sim_aux_r{r}'])
        add(f'rec_aux_ideal_r{r}', 'reconstruct', ['reconstruct', '--set', 'ideal', '--aux', f'r{r}', '--methods', 'z0'],
            [f'sim_aux_ideal_r{r}'])
    for v in VARIANTS:
        add(f'rec_var_{v}', 'reconstruct', ['reconstruct', '--set', f'variants/{v}'], ['sim_variants'])

    for r in REPS:
        add(f'yolo_r{r}', 'yolo', ['yolo', '--rep', str(r)], ['sim_base'])

    def needs(flow, r, set_='realistic', cal=False):
        if FLOWS[flow]['rec'] is None:
            return [f'sim_aux_r{r}'] if set_ == 'realistic' else [f'sim_aux_ideal_r{r}'] if set_ == 'ideal' else \
                ['sim_small']
        if set_ == 'realistic':
            return ['rec_base', f'rec_aux_cal_r{r}' if cal else f'rec_aux_r{r}']
        if set_ == 'ideal':
            return ['rec_ideal', f'rec_aux_ideal_r{r}']
        return [f'rec_{set_}']

    for r in REPS:
        for f in ALL:
            add(f'train_{f}_r{r}', 'train', ['train', '--flow', f, '--rep', str(r)], needs(f, r))
            add(f'eval_{f}_r{r}', 'evaluate', ['evaluate', '--flow', f, '--rep', str(r)], [f'train_{f}_r{r}'])
        for f in ['learned', 'prop', 'rec_z0']:   # calibration twins of discovery
            add(f'train_{f}_cal_r{r}', 'train', ['train', '--flow', f, '--rep', str(r), '--cal'], needs(f, r, cal=True))
        # ablations of the proposed layer: learning rate of the layer, auxiliary font scenes
        add(f'train_learned_lr_r{r}', 'train', ['train', '--flow', 'learned', '--rep', str(r), '--lr-fourier', '3e-3',
                                                '--tag', '_lr3e-3'], needs('learned', r))
        add(f'eval_learned_lr_r{r}', 'evaluate', ['evaluate', '--flow', 'learned', '--rep', str(r), '--tag', '_lr3e-3'],
            [f'train_learned_lr_r{r}'])
        add(f'train_learned_noaux_r{r}', 'train', ['train', '--flow', 'learned', '--rep', str(r), '--no-aux', '--tag',
                                                   '_noaux'], ['sim_base'])
        add(f'eval_learned_noaux_r{r}', 'evaluate', ['evaluate', '--flow', 'learned', '--rep', str(r), '--tag',
                                                     '_noaux'], [f'train_learned_noaux_r{r}'])
        # the idealised simulation: trained and evaluated on it, and its models on the realistic set
        for f in IDEAL_FLOWS:
            add(f'train_ideal_{f}_r{r}', 'train', ['train', '--set', 'ideal', '--flow', f, '--rep', str(r)],
                needs(f, r, 'ideal'))
            add(f'eval_ideal_{f}_r{r}', 'evaluate', ['evaluate', '--set', 'ideal', '--flow', f, '--rep', str(r)],
                [f'train_ideal_{f}_r{r}'])
            add(f'eval_ideal2real_{f}_r{r}', 'evaluate', ['evaluate', '--set', 'realistic', '--train-set', 'ideal',
                                                          '--flow', f, '--rep', str(r)],
                [f'train_ideal_{f}_r{r}', 'rec_base'])
        # size of the objects: letters of 20-60 um at 19 mm and at 2 mm (no auxiliary scenes)
        for s in ['small_z0', 'small_near']:
            for f in SMALL_FLOWS:
                add(f'train_{s}_{f}_r{r}', 'train', ['train', '--set', s, '--flow', f, '--rep', str(r), '--no-aux'],
                    needs(f, r, s))
                add(f'eval_{s}_{f}_r{r}', 'evaluate', ['evaluate', '--set', s, '--flow', f, '--rep', str(r)],
                    [f'train_{s}_{f}_r{r}'])

    trained = [f'train_{f}_r{r}' for f in ALL for r in REPS]
    add('exp_e2e', 'experiment', ['experiment', 'e2e'], trained + [f'yolo_r{r}' for r in REPS])
    add('exp_robustness', 'experiment', ['experiment', 'robustness'], trained + [f'rec_var_{v}' for v in VARIANTS])
    add('exp_oracle', 'experiment', ['experiment', 'oracle', '--workers', '16'], ['sim_variants'], dev='cpu')
    add('exp_discovery', 'experiment', ['experiment', 'discovery'],
        trained + [f'train_{f}_cal_r{r}' for f in ['learned', 'prop', 'rec_z0'] for r in REPS])
    add('exp_full_frames', 'experiment', ['experiment', 'full_frames'], trained + ['sim_full'] +
        [f'yolo_r{r}' for r in REPS])
    add('exp_timing_gpu', 'experiment', ['experiment', 'timing', '--rep', '1'], ['sim_full', 'yolo_r1',
                                                                                 'train_learned_r1', 'train_complex_r1',
                                                                                 'train_rec_z0_r1'])
    add('exp_timing_cpu', 'experiment', ['experiment', 'timing', '--rep', '1'], ['exp_timing_gpu'], dev='cpu')
    add('exp_fidelity', 'experiment', ['experiment', 'fidelity'], ['rec_base'])
    add('exp_gaps', 'experiment', ['experiment', 'gaps'], ['sim_base'])
    return J


def already_running(cmd):
    """True when the same command runs in another process (e.g. started by another instance of this queue)."""
    pat = ' '.join(['-m holo_openset'] + cmd) + ' --device'
    out = subprocess.run(['pgrep', '-f', '--', pat], capture_output=True, text=True).stdout.split()
    return any(int(p) != os.getpid() for p in out)


def free_mb(gpu):
    out = subprocess.run(['nvidia-smi', '-i', str(gpu), '--query-gpu=memory.free', '--format=csv,noheader,nounits'],
                         capture_output=True, text=True).stdout.strip()
    return int(out) if out.isdigit() else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--gpus', nargs='+', required=True, help='physical GPU indices to spread the jobs over')
    ap.add_argument('--jobs-per-gpu', type=int, default=2)
    ap.add_argument('--cpu-jobs', type=int, default=1)
    ap.add_argument('--min-free-mb', type=int, default=12000)
    ap.add_argument('--only', nargs='*', help='stages to run (simulate reconstruct yolo train evaluate experiment)')
    ap.add_argument('--match', nargs='*', help='only jobs whose name contains one of these')
    ap.add_argument('--assume-done', nargs='*', default=[], help='stages whose outputs are already there (downloaded)')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    J = jobs()
    done_dir = paths.LOGS / 'done'
    done_dir.mkdir(parents=True, exist_ok=True)
    done = {n for n, j in J.items() if (done_dir / f'{n}.ok').exists() or j[0] in a.assume_done}
    todo = [n for n, (st, _, _, _) in J.items() if n not in done and (not a.only or st in a.only)
            and (not a.match or any(m in n for m in a.match))]
    if a.dry_run:
        for n in todo:
            print(n, ' '.join(J[n][1]), '<-', ','.join(d for d in J[n][2] if d not in done))
        print(len(todo), 'jobs')
        return
    running = {}  # name -> (Popen, gpu or 'cpu')
    failed = set()
    while todo or running:
        for n, (p, g) in list(running.items()):
            if p.poll() is not None:
                del running[n]
                if p.returncode == 0:
                    (done_dir / f'{n}.ok').touch()
                    done.add(n)
                    print(time.strftime('%H:%M'), 'done', n, flush=True)
                else:
                    failed.add(n)
                    print(time.strftime('%H:%M'), 'FAILED', n, f'({paths.LOGS / n}.log)', flush=True)
        for n in list(todo):  # finished by another instance of the queue
            if (done_dir / f'{n}.ok').exists():
                done.add(n)
                todo.remove(n)
        blocked = {n for n in todo if any(d in failed for d in J[n][2])}
        for n in blocked:
            failed.add(n)
            todo.remove(n)
            print('skipped', n, '(a dependency failed)', flush=True)
        for n in list(todo):
            stage, cmd, deps, dev = J[n]
            if any(d not in done for d in deps if d in J) or already_running(cmd):
                continue
            if dev == 'cpu':
                if sum(g == 'cpu' for _, g in running.values()) >= a.cpu_jobs:
                    continue
                g = 'cpu'
            else:
                load = {g: sum(x == g for _, x in running.values()) for g in a.gpus}
                ok = [g for g in a.gpus if load[g] < a.jobs_per_gpu and free_mb(g) >= a.min_free_mb]
                if not ok:
                    continue
                g = min(ok, key=lambda x: load[x])
            full = PY + cmd + ['--device', 'cpu' if g == 'cpu' else f'cuda:{g}']
            if cmd[0] == 'experiment':  # the device goes to the experiment's own parser
                full = PY + cmd + ['--device', 'cpu' if g == 'cpu' else f'cuda:{g}']
            log = open(paths.LOGS / f'{n}.log', 'w')
            env = dict(os.environ, PYTHONUNBUFFERED='1')
            running[n] = (subprocess.Popen(full, stdout=log, stderr=subprocess.STDOUT, cwd=paths.PROJECT, env=env), g)
            todo.remove(n)
            print(time.strftime('%H:%M'), 'start', n, 'on', g, flush=True)
            time.sleep(8)  # let it allocate before the next check of the free memory
        time.sleep(15)
    print('finished;', len(failed), 'failed:', sorted(failed))


if __name__ == '__main__':
    main()
