"""Build the datasets with the forward model of holo_openset.sim.physics.

Layout of a set (data/holo_openset/<name>):
  holograms.npy              what the camera stores, uint8 [N, h, w] (memmap)
  backgrounds.npy            blank frame of each session (no sample; mean of 8 exposures, float32 [S, h, w])
  annotations.csv            one row per letter in the window (box, font, rotation, absorption, phase, depth, z)
  metadata.csv               one row per image (split, session, distance, counts)
  sessions.csv, dust.csv     session parameters; dust particles visible in the window
  physics.json               the configuration and the seeds
  images/, labels/           PNG copies and YOLO labels (sets that cover every split)
  objects/                   amplitude (x255) and phase (x255/pi) of the letters of the test split, in their plane
Splits are drawn by SESSION (35 / 7 / 8 of 50 sessions of 100 images): the test sample was never mounted in training.

A set made `like` another records the same scenes again with other physics (same ids, same rows): the idealised set
(all splits) and the robustness variants (test split only).
"""
import dataclasses
import json
import random
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image

from holo_openset.sim.letters import AUX_FONTS, CLASSES, FONTS, write_yolo_label
from holo_openset.sim.physics import FULL_FRAME, Physics, physics_from_dict, record, sensor_intensity
from holo_openset.sim.scene import Layout, SmallLayout, camera, make_scene, object_maps, session

CAMERA_SEED = 7
N_BLANKS = 8
LAYOUTS = {'default': Layout, 'small': SmallLayout}


def parse_sets(items):
    """['key=value', ...] -> overrides of Physics (tuples as comma-separated values)."""
    out = {}
    fields = {f.name for f in dataclasses.fields(Physics)}
    for it in items or []:
        k, v = it.split('=', 1)
        if k not in fields:
            raise SystemExit(f'unknown physics parameter {k}')
        cur = getattr(Physics(), k)
        out[k] = tuple(type(cur[0])(float(x)) for x in v.split(',')) if isinstance(cur, tuple) else \
            (v.lower() in ('1', 'true', 'yes')) if isinstance(cur, bool) else type(cur)(float(v))
    return out


_ARGS = None


def _init(args):
    global _ARGS
    _ARGS = args


def _scene(seed):
    phys, classes, fonts, outside, lay = _ARGS
    while True:
        sc = make_scene(seed, phys, classes, fonts, lay, outside_classes=outside)
        if sc is not None:
            return sc
        seed += 7919 * 1000003  # placement failed: another draw (deterministic)


def scenes(seeds, phys, workers, classes=CLASSES, fonts=FONTS, outside=None, lay=Layout, chunk=32):
    """The scenes of `seeds`, in order, built by a pool one chunk ahead of the consumer (bounded memory)."""
    with Pool(workers, initializer=_init, initargs=((phys, classes, fonts, outside, lay),)) as p:
        chunks = [seeds[k:k + chunk] for k in range(0, len(seeds), chunk)]
        nxt = p.map_async(_scene, chunks[0], chunksize=1) if chunks else None
        for k in range(len(chunks)):
            cur = nxt.get()
            nxt = p.map_async(_scene, chunks[k + 1], chunksize=1) if k + 1 < len(chunks) else None
            yield from cur


def blank(ses, phys, cam, dev, seed):
    """Blank frame of a session: the mean of N_BLANKS exposures without the sample."""
    g = torch.Generator(device=dev).manual_seed(seed)
    inten = sensor_intensity(dict(objects=[], dust=[], sensor_dust=cam['dust']), ses, phys, dev, sample=False)
    return np.mean([record(inten, ses, phys, cam, g, dev).astype(np.float32) for _ in range(N_BLANKS)], 0)


def split_sessions(n_sessions, seed):
    order = random.Random(seed).sample(range(n_sessions), n_sessions)
    n_tr, n_va = round(0.7 * n_sessions), round(0.14 * n_sessions)
    return {s: 'train' if k < n_tr else 'val' if k < n_tr + n_va else 'test' for k, s in enumerate(order)}


def _rows(i, sc, ses, split, phys, fn):
    h, w = phys.window
    m0 = sc['margin']
    ann = [dict(image_id=i, **r, z=ses['z'] + r['depth'], filename=fn, split=split) for r in sc['rows']]
    dust = []
    for o in sc['dust']:
        dh, dw = o['mask'].shape
        x, y = o['x'] - m0, o['y'] - m0
        if x + dw > 0 and y + dh > 0 and x < w and y < h:
            dust.append(dict(image_id=i, x0=x, y0=y, x1=x + dw, y1=y + dh, depth=o['depth'], absorption=o['absorption'],
                             phase=o['phase']))
    return ann, dust


def generate(out, phys=None, n_images=5000, per_session=100, seed=17, like=None, split=None, layout='default',
             workers=8, dev='cpu', log=print):
    """Write a set to `out`. like: an existing set whose scenes are recorded again (its physics, overridden by the
    fields of `phys` given as a dict); split: with like, only that split."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if like:
        base = json.load(open(Path(like) / 'physics.json'))
        phys = physics_from_dict(base['physics']).replace(**(phys or {}))
        seed, per_session, layout = base['seed'], base['per_session'], base.get('layout', 'default')
        meta = pd.read_csv(Path(like) / 'metadata.csv')
        n_sessions = int(meta.session.max()) + 1
        split_of_session = meta.groupby('session').split.first().to_dict()
        if split:
            meta = meta[meta.split == split]
        ids = meta.image_id.to_numpy()
    else:
        phys = Physics().replace(**(phys or {}))
        ids = np.arange(n_images)
        n_sessions = -(-n_images // per_session)
        split_of_session = split_sessions(n_sessions, seed)
    full = split is None
    if full:
        for d in ['images', 'labels', 'objects']:
            (out / d).mkdir(exist_ok=True)
    cam = camera(CAMERA_SEED, phys)
    sessions = {s: session(seed * 1000 + s, phys) for s in range(n_sessions)}
    used = sorted({int(i) // per_session for i in ids})
    h, w = phys.window

    bg = np.zeros((n_sessions, h, w), np.float32)
    for s in used:
        bg[s] = blank(sessions[s], phys, cam, dev, seed * 1000 + s + 500000)
    np.save(out / 'backgrounds.npy', bg)

    holo = np.lib.format.open_memmap(out / 'holograms.npy', mode='w+', dtype=np.uint8 if phys.bits == 8 else np.float32,
                                     shape=(len(ids), h, w))
    meta_rows, ann_rows, dust_rows = [], [], []
    seeds = [seed * 1_000_000 + int(i) for i in ids]
    for k, (i, sc) in enumerate(zip(ids, scenes(seeds, phys, workers, lay=LAYOUTS[layout]))):
        i = int(i)
        s = i // per_session
        ses, sp = sessions[s], split_of_session[i // per_session]
        sc['sensor_dust'] = cam['dust']
        g = torch.Generator(device=dev).manual_seed(seed * 1_000_000 + i + 700_000_000)
        img = record(sensor_intensity(sc, ses, phys, dev), ses, phys, cam, g, dev)
        holo[k] = img
        fn = f'{i:06d}.png'
        if full:
            Image.fromarray(img).save(out / 'images' / fn)
            write_yolo_label(out / 'labels' / f'{i:06d}.txt', sc['rows'], w, h)
            if sp == 'test':
                amp, ph = object_maps(sc, phys)
                Image.fromarray((amp * 255).round().astype(np.uint8)).save(out / 'objects' / f'{i:06d}_amp.png')
                Image.fromarray((ph * 255 / np.pi).round().clip(0, 255).astype(np.uint8)).save(
                    out / 'objects' / f'{i:06d}_phase.png')
        a, d = _rows(i, sc, ses, sp, phys, fn)
        ann_rows += a
        dust_rows += d
        meta_rows.append(dict(image_id=i, filename=fn, label_filename=f'{i:06d}.txt', split=sp, session=s, z=ses['z'],
                              n_letters=len(sc['rows']), n_outside=sum(o['kind'] == 'outside' for o in sc['objects']),
                              n_dust=len(sc['dust']), classes=''.join(sorted({r['classe'] for r in sc['rows']}))))
        if k % 250 == 0:
            log(f'{k}/{len(ids)}')
    holo.flush()
    pd.DataFrame(meta_rows).to_csv(out / 'metadata.csv', index=False)
    pd.DataFrame(ann_rows).to_csv(out / 'annotations.csv', index=False)
    pd.DataFrame(dust_rows, columns=['image_id', 'x0', 'y0', 'x1', 'y1', 'depth', 'absorption', 'phase']).to_csv(
        out / 'dust.csv', index=False)
    pd.DataFrame([dict(session=s, split=split_of_session[s], **sessions[s]) for s in range(n_sessions)]).to_csv(
        out / 'sessions.csv', index=False)
    json.dump(dict(physics=dataclasses.asdict(phys), seed=seed, per_session=per_session, layout=layout,
                   camera_seed=CAMERA_SEED, n_blanks=N_BLANKS, like=str(like) if like else None, split=split,
                   fonts=[f.name for f in FONTS]), open(out / 'physics.json', 'w'), indent=1)
    log(f'wrote {out} {holo.shape}')


def aux(base, out, rep, n_images=2000, workers=8, dev='cpu', log=print):
    """Seen letters of repetition `rep` in the extra fonts, recorded in the training sessions of `base` (the letters
    around the window are seen letters too): <out>/r{rep}_images.npy + r{rep}_boxes.csv; and the same without the
    held-out seen classes for the calibration twin of discovery (r{rep}_cal_*)."""
    from holo_openset.protocol import classes, held_out_seen
    base, out = Path(base), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    cfg = json.load(open(base / 'physics.json'))
    phys, seed = physics_from_dict(cfg['physics']), cfg['seed']
    lay = LAYOUTS[cfg.get('layout', 'default')]
    cam = camera(CAMERA_SEED, phys)
    ses_tab = pd.read_csv(base / 'sessions.csv')
    train_sessions = ses_tab[ses_tab.split == 'train'].session.tolist()
    seen = classes(rep)[0]
    for name, allowed, offset in [(f'r{rep}', set(seen), 200000),
                                  (f'r{rep}_cal', set(seen) - set(held_out_seen(rep)), 300000)]:
        imgs = np.lib.format.open_memmap(out / f'{name}_images.npy', mode='w+', dtype=np.uint8,
                                         shape=(n_images, *phys.window))
        boxes = []
        seeds = [seed * 1_000_000 + offset + 1000 * rep + k for k in range(n_images)]
        for k, sc in enumerate(scenes(seeds, phys, workers, classes=sorted(allowed), fonts=AUX_FONTS,
                                      outside=sorted(allowed), lay=lay)):
            s = random.Random(seeds[k]).choice(train_sessions)
            ses = session(seed * 1000 + s, phys)
            sc['sensor_dust'] = cam['dust']
            g = torch.Generator(device=dev).manual_seed(seeds[k] + 700_000_000)
            imgs[k] = record(sensor_intensity(sc, ses, phys, dev), ses, phys, cam, g, dev)
            boxes += [(k, r['classe'], r['x0'], r['y0'], r['x1'], r['y1'], s) for r in sc['rows']]
        imgs.flush()
        b = pd.DataFrame(boxes, columns=['image_id', 'classe', 'x0', 'y0', 'x1', 'y1', 'session'])
        assert set(b.classe) <= allowed
        b.to_csv(out / f'{name}_boxes.csv', index=False)
        log(f'{name} {imgs.shape} {len(b)} letters')


def full_frames(base, out, n_images=40, phys=None, workers=8, dev='cpu', log=print):
    """Full frames of the sensor of the bench (3840 x 2748 px, 29.4 mm^2), acquired in the TEST sessions of `base`
    with its physics (overridden by `phys`), letters of every class at the density of the dataset."""
    base, out = Path(base), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    cfg = json.load(open(base / 'physics.json'))
    p = physics_from_dict(cfg['physics']).replace(window=FULL_FRAME, **(phys or {}))
    seed, lay = cfg['seed'], LAYOUTS[cfg.get('layout', 'default')]
    cam = camera(CAMERA_SEED + 1, p)
    ses_tab = pd.read_csv(base / 'sessions.csv')
    test_sessions = ses_tab[ses_tab.split == 'test'].session.tolist()
    sessions = {s: session(seed * 1000 + s, p) for s in test_sessions}
    h, w = p.window
    bg = np.zeros((int(ses_tab.session.max()) + 1, h, w), np.float32)
    for s in test_sessions:
        bg[s] = blank(sessions[s], p, cam, dev, seed * 1000 + s + 900000)
        log(f'blank {s}')
    np.save(out / 'backgrounds.npy', bg)
    holo = np.lib.format.open_memmap(out / 'holograms.npy', mode='w+', dtype=np.uint8, shape=(n_images, h, w))
    meta_rows, ann_rows, dust_rows = [], [], []
    seeds = [seed * 1_000_000 + 400_000_000 + k for k in range(n_images)]
    for k, sc in enumerate(scenes(seeds, p, workers, lay=lay, chunk=4)):
        s = test_sessions[k % len(test_sessions)]
        ses = sessions[s]
        sc['sensor_dust'] = cam['dust']
        g = torch.Generator(device=dev).manual_seed(seeds[k] + 700_000_000)
        holo[k] = record(sensor_intensity(sc, ses, p, dev), ses, p, cam, g, dev)
        fn = f'{k:06d}.png'
        a, d = _rows(k, sc, ses, 'test', p, fn)
        ann_rows += a
        dust_rows += d
        meta_rows.append(dict(image_id=k, filename=fn, split='test', session=s, z=ses['z'], n_letters=len(sc['rows']),
                              n_outside=sum(o['kind'] == 'outside' for o in sc['objects']), n_dust=len(sc['dust'])))
        log(f'frame {k}/{n_images}: {len(sc["rows"])} letters')
    holo.flush()
    pd.DataFrame(meta_rows).to_csv(out / 'metadata.csv', index=False)
    pd.DataFrame(ann_rows).to_csv(out / 'annotations.csv', index=False)
    pd.DataFrame(dust_rows, columns=['image_id', 'x0', 'y0', 'x1', 'y1', 'depth', 'absorption', 'phase']).to_csv(
        out / 'dust.csv', index=False)
    ses_tab.to_csv(out / 'sessions.csv', index=False)
    json.dump(dict(physics=dataclasses.asdict(p), seed=seed, per_session=None, layout=cfg.get('layout', 'default'),
                   camera_seed=CAMERA_SEED + 1, n_blanks=N_BLANKS, like=str(base), split='test',
                   fonts=[f.name for f in FONTS]), open(out / 'physics.json', 'w'), indent=1)
    log(f'wrote {out} {holo.shape}')
