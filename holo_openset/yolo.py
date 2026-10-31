"""Training of the class-agnostic YOLO12 localiser on the holograms of a set.

For repetition r, every training image that contains a letter of an unseen class is removed (otherwise the detector
learns to treat those letters as background and misses them at test time); validation keeps every image. One class,
"pattern". Recipe: YOLO12-s from COCO weights, AdamW, lr 1e-3, at most 40 epochs with patience 10 (the localiser
reaches mAP50 ~0.99 within ~10 epochs), mild geometric and brightness augmentation, no flips.
Needs ultralytics >= 8.4 (YOLO12); see the README for the environment.
"""
import json
import os
import shutil
from pathlib import Path

import pandas as pd
import yaml

from holo_openset import paths
from holo_openset.protocol import classes

RECIPE = dict(optimizer='AdamW', lr0=0.001, lrf=0.01, degrees=15.0, translate=0.08, scale=0.10, hsv_h=0.0, hsv_s=0.0,
              hsv_v=0.15, fliplr=0.0, flipud=0.0, mosaic=0.20, mixup=0.0, copy_paste=0.0, close_mosaic=20, erasing=0.0)


def _link(src, dst):
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def prepare(root, rep, work):
    """Links to the images and class-agnostic labels of the train and val splits -> data.yaml."""
    root, work = Path(root), Path(work)
    meta = pd.read_csv(root / 'metadata.csv')
    ann = pd.read_csv(root / 'annotations.csv')
    unseen = set(classes(rep)[1])
    bad = set(ann[ann.split.eq('train') & ann.classe.isin(unseen)].filename)
    counts = {}
    for split in ['train', 'val']:
        for d in ['images', 'labels']:
            shutil.rmtree(work / split / d, ignore_errors=True)
            (work / split / d).mkdir(parents=True)
        part = meta[(meta.split == split) & ~meta.filename.isin(bad)]
        for r in part.itertuples():
            _link(root / 'images' / r.filename, work / split / 'images' / r.filename)
            lines = [' '.join(['0'] + l.split()[1:]) for l in (root / 'labels' / r.label_filename).read_text().splitlines()
                     if len(l.split()) == 5]
            (work / split / 'labels' / r.label_filename).write_text('\n'.join(lines) + ('\n' if lines else ''))
        counts[split] = len(part)
    counts['train_removed'] = len(bad)
    yaml.safe_dump(dict(path=str(work), train='train/images', val='val/images', nc=1, names=['pattern']),
                   open(work / 'data.yaml', 'w'))
    return work / 'data.yaml', counts


def train(rep, root=None, out=None, epochs=40, patience=10, batch=8, seed=42, base='yolo12s.pt', log=print):
    from ultralytics import YOLO
    root = Path(root or paths.dataset(paths.BASE))
    out = Path(out or paths.yolo_weights(rep, root.name))
    work = paths.DATA / 'yolo_work' / root.name / f'r{rep}'
    cfg, counts = prepare(root, rep, work)
    log(f'YOLO r{rep}: {counts}')
    model = YOLO(str(paths.PROJECT / base) if (paths.PROJECT / base).exists() else base)
    model.train(data=str(cfg), epochs=epochs, patience=patience, batch=batch, imgsz=640, device=0, workers=4, seed=seed,
                deterministic=True, project=str(work), name='train', exist_ok=True, verbose=False, **RECIPE)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(work / 'train/weights/best.pt', out)
    m = YOLO(str(out)).val(data=str(cfg), split='val', imgsz=640, batch=batch, device=0, project=str(work),
                           name='val', exist_ok=True, verbose=False)
    summary = dict(rep=rep, set=root.name, counts=counts, epochs=epochs, patience=patience, base=base,
                   val_map50=float(m.box.map50), val_map=float(m.box.map), val_precision=float(m.box.mp),
                   val_recall=float(m.box.mr))
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    json.dump(summary, open(paths.RESULTS / f'yolo_{root.name}_r{rep}.json', 'w'), indent=1)
    log(json.dumps(summary))
    return out
