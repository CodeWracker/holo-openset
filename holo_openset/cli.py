"""Command line interface:  python -m holo_openset <command> [options]

Build the data and the models (each command uses ONE device, --device cpu | cuda:N):
  simulate      simulate an acquisition: base | ideal | variant NAME | variants | aux --rep R | full | small
  reconstruct   conventional reconstructions of a set (back-propagation, autofocus, per-object focus, twin removal)
  yolo          train the class-agnostic YOLO localiser of a repetition
  train         train the embedding network of a flow on the seen classes of a repetition
  evaluate      strict open-set evaluation of a flow (paper protocol)
  experiment    the experiments of the paper (see holo_openset/experiments)
  paper         figures and tables of the paper from the results
Use the system:
  enroll        build (or extend) a gallery from annotated images, with a calibrated threshold
  predict       detect + recognise patterns in hologram images (known class or 'unknown'), with figures
  discover      group the patterns rejected as 'unknown' into candidate new classes
  demo          end-to-end demonstration: unknown letters are rejected, then recognised after enrollment
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

from holo_openset import paths


def _device(a):
    from holo_openset.model import physical_gpu, pick_device
    dev = pick_device(a.device)
    print(f'device {physical_gpu() or dev}', file=sys.stderr, flush=True)
    return dev


def _set(a):
    return paths.dataset(a.set)


# ------------------------------------------------------------------------------------------------ build
def cmd_simulate(a):
    from holo_openset.sim import generate as G
    from holo_openset.sim.physics import IDEAL
    from holo_openset.sim.variants import VARIANTS
    dev = _device(a)
    base = paths.dataset(paths.BASE)
    sets = G.parse_sets(a.set_physics)
    if a.what == 'base':
        G.generate(base, phys=sets, n_images=a.n_images, workers=a.workers, dev=dev)
    elif a.what == 'ideal':
        G.generate(paths.dataset(paths.IDEAL), phys={**IDEAL, **sets}, like=base, workers=a.workers, dev=dev)
    elif a.what in ('variant', 'variants'):
        names = a.names or list(VARIANTS)
        for v in names:
            out = paths.dataset(f'variants/{v}')
            if (out / 'physics.json').exists() and not a.force:
                print('exists', out)
                continue
            G.generate(out, phys=VARIANTS[v][2], like=base, split='test', workers=a.workers, dev=dev)
    elif a.what == 'aux':
        for r in a.rep:
            G.aux(paths.dataset(a.set), paths.dataset(a.set) / 'aux', r, n_images=a.aux_images, workers=a.workers,
                  dev=dev)
    elif a.what == 'full':
        G.full_frames(base, paths.dataset('full_frames'), n_images=a.n_images or 40, phys=sets, workers=a.workers,
                      dev=dev)
    elif a.what == 'small':
        from holo_openset.sim.physics import Z0
        for name, z in [('small_z0', Z0), ('small_near', 2e-3)]:   # letters of 20-60 um at 19 mm and at 2 mm
            if not (paths.dataset(name) / 'physics.json').exists() or a.force:
                G.generate(paths.dataset(name), phys=dict(sets, z0=z), n_images=a.n_images, workers=a.workers,
                           dev=dev, layout='small')


def cmd_reconstruct(a):
    from holo_openset.reconstruct import METHODS, build_caches
    dev = _device(a)
    for aux in ([None] if not a.aux else a.aux):
        build_caches(_set(a), a.methods or METHODS, dev, aux=aux)


def cmd_yolo(a):
    from holo_openset.yolo import train
    _device(a)
    for r in a.rep:
        train(r, _set(a), epochs=a.epochs, patience=a.patience)


def cmd_train(a):
    import torch
    from holo_openset.flows import FLOWS, aux_scenes, dataset
    from holo_openset.protocol import classes, held_out_seen
    from holo_openset.train import save_checkpoint, train
    torch.set_num_threads(a.threads)
    dev = _device(a)
    f = FLOWS[a.flow]
    for r in a.rep:
        out = Path(a.out) if a.out else paths.weights(a.flow, r, a.set, a.tag + ('_cal' if a.cal else ''))
        if out.exists() and not a.force:
            print('exists', out)
            continue
        seen = classes(r)[0]
        if a.cal:
            seen = sorted(set(seen) - set(held_out_seen(r)))
        aux = aux_scenes(a.flow, r, _set(a), cal=a.cal) if not a.no_aux else None
        model = train(dataset(a.flow, _set(a)), seen, steps=a.steps, mode=f['mode'], fourier=f['fourier'],
                      lr_fourier=a.lr_fourier, aux_scenes=aux, threads=a.threads, seed=a.seed, device=dev,
                      **f.get('train', {}))
        save_checkpoint(model, out, flow=a.flow, set=a.set, classes=seen, rep=r, steps=a.steps,
                        lr_fourier=a.lr_fourier, cal=a.cal, aux=not a.no_aux)
        print(f'saved {out}', flush=True)


def cmd_evaluate(a):
    from holo_openset.evaluate import evaluate
    from holo_openset.flows import dataset
    from holo_openset.model import load_model
    dev = _device(a)
    out_dir = paths.RESULTS / 'eval' / a.set
    out_dir.mkdir(parents=True, exist_ok=True)
    for r in a.rep:
        model = load_model(Path(a.model) if a.model else paths.weights(a.flow, r, a.train_set or a.set, a.tag), dev)[0]
        res = evaluate(model, dataset(a.flow, _set(a)), r)
        res.update(flow=a.flow, set=a.set, train_set=a.train_set or a.set, tag=a.tag)
        name = f'{a.flow}{a.tag}' + (f'_from_{a.train_set}' if a.train_set else '')
        json.dump(res, open(out_dir / f'{name}_r{r}.json', 'w'), indent=1)
        print(name, r, {k: round(res[k], 4) for k in ['novel_auroc', 'novel_unknown_rejection', 'novel_open_macro_f1']})


def cmd_experiment(a):
    import importlib
    mod = importlib.import_module(f'holo_openset.experiments.{a.name}')
    mod.main(a.args)


def cmd_reproduce(a):
    from holo_openset.reproduce import main
    sys.exit(main(a))


def cmd_paper(a):
    import importlib
    for name in a.what:
        importlib.import_module(f'holo_openset.paper.{name}').main()


# ------------------------------------------------------------------------------------------------ use
def _model(a, dev):
    from holo_openset.model import load_model
    return load_model(Path(a.model) if a.model else paths.weights(a.flow, a.rep[0], a.set), dev)[0]


def _images(a):
    from holo_openset.flows import dataset
    return dataset(a.flow, _set(a))


def _detector(a, ds, dev):
    from holo_openset.detect import CsvBoxes, GtBoxes, YoloDetector
    if a.detector == 'gt':
        return GtBoxes(ds.ann)
    if a.detector == 'csv':
        return CsvBoxes(a.boxes_csv)
    return YoloDetector(a.yolo_weights or paths.yolo_weights(a.rep[0], a.set), conf=a.conf, device=dev)


def cmd_enroll(a):
    from holo_openset.data import embed_annotations
    from holo_openset.gallery import Gallery
    from holo_openset.protocol import classes
    dev = _device(a)
    ds, model = _images(a), _model(a, dev)
    seen, unseen = classes(a.rep[0])
    cls = {'seen': seen, 'unseen': unseen, 'all': seen + unseen}.get(a.classes) or list(a.classes.replace(',', ''))
    rows = ds.ann[(ds.ann.split == a.split) & ds.ann.classe.isin(cls)]
    if a.max_per_class:
        rows = rows.groupby('classe', group_keys=False).apply(lambda g: g.sample(min(len(g), a.max_per_class),
                                                                                  random_state=0))
    emb = embed_annotations(model, ds, rows)
    boxes = rows[['x0', 'y0', 'x1', 'y1']].to_numpy()
    if a.add_to:
        g = Gallery.load(a.add_to)
        g.add(emb, rows.classe.to_numpy(), rows.image_id.to_numpy(), boxes)
    else:
        g = Gallery(emb, rows.classe.to_numpy(), rows.image_id.to_numpy(), meta=dict(flow=a.flow, set=a.set),
                    boxes=boxes)
        g.calibrate(a.frr)
    g.save(a.out)
    print(json.dumps(g.summary(), indent=1))


def cmd_predict(a):
    from holo_openset.gallery import Gallery
    from holo_openset.predict import predict, plot
    dev = _device(a)
    ds, model = _images(a), _model(a, dev)
    gallery = Gallery.load(a.gallery)
    det = _detector(a, ds, dev)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for p in a.images:
        holo, view, dets = predict(model, a.flow, gallery, p, det, dev)
        json.dump(dets, open(out / f'{Path(p).stem}.json', 'w'), indent=1)
        plot(holo, view, dets, gallery, ds, out / f'{Path(p).stem}.png', title=Path(p).name)
        print(Path(p).stem, ' '.join(d['decision'] for d in dets))


def cmd_discover(a):
    from holo_openset.experiments.discovery import discover_files
    dev = _device(a)
    discover_files(a, dev)


def cmd_demo(a):
    from holo_openset.predict import demo
    dev = _device(a)
    demo(a, dev)


# ------------------------------------------------------------------------------------------------ parser
def main(argv=None):
    ap = argparse.ArgumentParser(prog='python -m holo_openset', description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--device', default='cpu', help="'cpu' or 'cuda:N' (one GPU per process)")
    common.add_argument('--set', default=paths.BASE, help='dataset under data/holo_openset (default: realistic)')
    common.add_argument('--threads', type=int, default=4)
    flow = argparse.ArgumentParser(add_help=False)
    flow.add_argument('--flow', default='learned', help='raw, learned, complex, wiener, rec_z0, rec_af, rec_edf, rec_twin')
    flow.add_argument('--rep', type=int, nargs='+', default=[2], help='repetitions (class splits) 1-5')
    flow.add_argument('--model', help='checkpoint (default: models/holo_openset/<set>/<flow>_r<rep>.pt)')
    flow.add_argument('--tag', default='', help='suffix of the checkpoint name (variants of the training recipe)')
    det = argparse.ArgumentParser(add_help=False)
    det.add_argument('--detector', choices=['yolo', 'gt', 'csv'], default='yolo')
    det.add_argument('--yolo-weights')
    det.add_argument('--boxes-csv')
    det.add_argument('--conf', type=float, default=0.25)
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('simulate', parents=[common], help='simulate an acquisition')
    p.add_argument('what', choices=['base', 'ideal', 'variant', 'variants', 'aux', 'full', 'small'])
    p.add_argument('names', nargs='*', help='variant names (default: all)')
    p.add_argument('--n-images', type=int, default=5000)
    p.add_argument('--aux-images', type=int, default=2000)
    p.add_argument('--rep', type=int, nargs='+', default=[1, 2, 3, 4, 5])
    p.add_argument('--set-physics', nargs='*', default=[], help='physics overrides key=value (sim/physics.py)')
    p.add_argument('--workers', type=int, default=8)
    p.add_argument('--force', action='store_true')
    p.set_defaults(fn=cmd_simulate)

    p = sub.add_parser('reconstruct', parents=[common], help='conventional reconstruction caches of a set')
    p.add_argument('--methods', nargs='*', help='z0 af edf twin (default: all)')
    p.add_argument('--aux', nargs='*', help='auxiliary scenes instead (r1 r1_cal ...)')
    p.set_defaults(fn=cmd_reconstruct)

    p = sub.add_parser('yolo', parents=[common], help='train the YOLO localiser')
    p.add_argument('--rep', type=int, nargs='+', default=[2])
    p.add_argument('--epochs', type=int, default=40)
    p.add_argument('--patience', type=int, default=10)
    p.set_defaults(fn=cmd_yolo)

    p = sub.add_parser('train', parents=[common, flow], help='train the embedding network of a flow')
    p.add_argument('--steps', type=int, default=3000)
    p.add_argument('--lr-fourier', type=float, default=3e-1)
    p.add_argument('--cal', action='store_true', help='calibration twin: without the held-out seen classes')
    p.add_argument('--no-aux', action='store_true', help='without the auxiliary font scenes')
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--out')
    p.add_argument('--force', action='store_true')
    p.set_defaults(fn=cmd_train)

    p = sub.add_parser('evaluate', parents=[common, flow], help='strict open-set evaluation')
    p.add_argument('--train-set', help='set the model was trained on (default: --set)')
    p.set_defaults(fn=cmd_evaluate)

    p = sub.add_parser('experiment', help='run an experiment of the paper')
    p.add_argument('name', help='e2e, robustness, oracle, discovery, full_frames, timing, fidelity, gaps')
    p.add_argument('args', nargs=argparse.REMAINDER)
    p.set_defaults(fn=cmd_experiment)

    p = sub.add_parser('paper', help='figures and tables of the paper')
    p.add_argument('what', nargs='*', default=['tables', 'figures'])
    p.set_defaults(fn=cmd_paper)

    p = sub.add_parser('reproduce', help='reproduce the paper (docs/REPRODUCIBILITY.md)')
    p.add_argument('what', choices=['check', 'download', 'evaluate', 'full', 'compare', 'verify-data', 'compare-data',
                                    'package', 'write-data-sums'])
    p.add_argument('path', nargs='?', help='results (compare), data (compare-data) or output (package) directory')
    p.add_argument('--gpus', nargs='+', default=['0'], help='physical GPU indices (each job uses one)')
    p.add_argument('--record', help='Zenodo record of the data')
    p.set_defaults(fn=cmd_reproduce)

    p = sub.add_parser('enroll', parents=[common, flow], help='build or extend a gallery')
    p.add_argument('--classes', default='seen', help="'seen', 'unseen', 'all' or letters")
    p.add_argument('--split', default='val')
    p.add_argument('--max-per-class', type=int, default=0, help='k-shot enrollment (0 = all)')
    p.add_argument('--frr', type=float, default=0.05)
    p.add_argument('--add-to', help='existing gallery to extend (keeps its threshold)')
    p.add_argument('--out', required=True)
    p.set_defaults(fn=cmd_enroll)

    p = sub.add_parser('predict', parents=[common, flow, det], help='recognise patterns in hologram images')
    p.add_argument('--gallery', required=True)
    p.add_argument('--out-dir', default='holo_openset_out')
    p.add_argument('images', nargs='+')
    p.set_defaults(fn=cmd_predict)

    p = sub.add_parser('discover', parents=[common, flow, det], help='cluster unknown patterns into new classes')
    p.add_argument('--gallery', required=True)
    p.add_argument('--cut', type=float, help='clustering cut (default: the calibrated one)')
    p.add_argument('--min-size', type=int, default=3)
    p.add_argument('--out')
    p.add_argument('images', nargs='+')
    p.set_defaults(fn=cmd_discover)

    p = sub.add_parser('demo', parents=[common, flow, det], help='two-step open-set demonstration')
    p.add_argument('--n-images', type=int, default=4)
    p.add_argument('--shots', type=int, default=5)
    p.add_argument('--frr', type=float, default=0.05)
    p.add_argument('--out-dir', default='holo_openset_demo')
    p.set_defaults(fn=cmd_demo)

    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == '__main__':
    main()
