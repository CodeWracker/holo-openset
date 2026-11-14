"""Empirical checks of the pairing of the scenes of the distance study (docs/exp_distancia/CADERNO.md, entry A2).
Reads data/ only; CPU. From the root of the repository, after source scripts/exp_distancia/env.sh:

    python scripts/exp_distancia/pairing_check.py

(a) full frames: every set of data/full_frames_* has the annotations of data/full_frames (ids, boxes, classes,
    fonts, order) except depth and z; tilt0 and frame5 keep the depths of the paper frames; the tilt adds
    tan(theta) * r to the depth, with r the same for every angle and linear in the position of the letter along the
    azimuth of its session (drawn by random.Random(seed * 1000 + s + 650_000)); the z of each frame is the design one
    (recomputed from the seeds of sim/generate.py).
(b) windows: data/variants/{frame_2, frame_5, walk_05} against data/realistic (test split): the same annotations except
    depth-dependent z, and the z of each image recomputed from the seeds (jitter: random.Random(scene seed +
    800_000_000); drift: generate.session_walk); measured sigma of the jitter and step of the drift.
(d) pixels: the frame_5 test images whose distance moved least, against the same base images; and an unpaired pair
    as the scale. full_frames_tilt0 against full_frames: the share of differing pixels.
"""
import math
import random

import numpy as np
import pandas as pd

from holo_openset.sim.generate import session_walk
from holo_openset.sim.physics import Z0

SEED = 17
D = 'data'
KEYS = ['image_id', 'det_idx', 'classe', 'class_id', 'x0', 'y0', 'x1', 'y1', 'font_size', 'font_name', 'rotation',
        'absorption', 'phase', 'filename', 'split']


def same(a, b, cols):
    return len(a) == len(b) and all((a[c].values == b[c].values).all() for c in cols)


def full_frames():
    print('(a) full frames')
    ref = pd.read_csv(f'{D}/full_frames/annotations.csv')
    meta_ref = pd.read_csv(f'{D}/full_frames/metadata.csv')
    ses = pd.read_csv(f'{D}/realistic/sessions.csv').set_index('session').z
    print(f'  full_frames: {len(ref)} letters in {ref.image_id.nunique()} frames; metadata z == session z: '
          f'{np.allclose(meta_ref.z, ses.loc[meta_ref.session].values, rtol=0, atol=0)}')
    r_of = {}
    for name in ['frame5', 'tilt0', 'tilt1', 'tilt2', 'tilt5', 'tilt10', 'tilt15']:
        a = pd.read_csv(f'{D}/full_frames_{name}/annotations.csv')
        m = pd.read_csv(f'{D}/full_frames_{name}/metadata.csv')
        cols_meta = ['image_id', 'filename', 'split', 'session', 'n_letters', 'n_outside', 'n_dust']
        line = (f'  {name}: annotations except depth and z identical: {same(a, ref, KEYS)}; metadata except z '
                f'identical: {same(m, meta_ref, cols_meta)}; depth identical: {(a.depth.values == ref.depth.values).all()}')
        k = m.image_id.to_numpy()
        zs = ses.loc[m.session].to_numpy()
        if name == 'frame5':
            h = np.array([random.Random(SEED * 1_000_000 + 400_000_000 + int(i) + 800_000_000).gauss(0.0, 1.0)
                          for i in k])
            design = zs * (1 + 0.05 * h)
            jit = m.z.to_numpy() / zs - 1
            line += (f'; z == z_session (1 + 0.05 h) recomputed: max |diff| {np.abs(m.z - design).max():.1e} m; '
                     f'jitter sd {jit.std(ddof=1):.4f}, mean {jit.mean():+.4f}, n {len(jit)}')
        else:
            line += f'; z == session z: {np.array_equal(m.z.to_numpy(), zs)}'
        # annotation z = frame z + depth
        zf = m.set_index('image_id').z.loc[a.image_id].to_numpy()
        line += f'; annotation z == frame z + depth: max |diff| {np.abs(a.z - (zf + a.depth)).max():.1e}'
        print(line)
        if name.startswith('tilt') and name != 'tilt0':
            th = int(name[4:])
            r_of[th] = (a.depth.values - ref.depth.values) / math.tan(math.radians(th))
    # the lever arm r of each letter must not depend on the angle, and must be the projection of its position on the
    # azimuth of its session
    rs = np.vstack([r_of[t] for t in sorted(r_of)])
    print(f'  tilt: (depth_theta - depth_paper) / tan(theta), largest spread across 1, 2, 5, 10, 15 deg: '
          f'{np.abs(rs - rs.mean(0)).max():.2e} m (letters {rs.shape[1]})')
    sess = meta_ref.set_index('image_id').session.loc[ref.image_id].to_numpy()
    cx, cy = (ref.x0 + ref.x1).to_numpy() / 2, (ref.y0 + ref.y1).to_numpy() / 2
    r = rs.mean(0)
    worst_phi, worst_fit = 0.0, 0.0
    for s in np.unique(sess):
        i = sess == s
        X = np.c_[cx[i], cy[i], np.ones(i.sum())]
        coef, *_ = np.linalg.lstsq(X, r[i], rcond=None)
        phi_fit = math.atan2(coef[1], coef[0]) % (2 * math.pi)
        phi = random.Random(SEED * 1000 + int(s) + 650_000).uniform(0, 2 * math.pi)
        d = abs((phi_fit - phi + math.pi) % (2 * math.pi) - math.pi)
        worst_phi = max(worst_phi, d)
        worst_fit = max(worst_fit, np.abs(X @ coef - r[i]).max())
    print(f'  tilt: azimuth fitted from the lever arms against random.Random(seed*1000+s+650000): largest difference '
          f'{math.degrees(worst_phi):.3f} deg over 8 sessions; largest residual of the linear fit {worst_fit:.2e} m')


def windows():
    print('(b) windows (test split)')
    base_ann = pd.read_csv(f'{D}/realistic/annotations.csv')
    base_ann = base_ann[base_ann.split == 'test'].reset_index(drop=True)
    base_meta = pd.read_csv(f'{D}/realistic/metadata.csv')
    base_meta = base_meta[base_meta.split == 'test'].reset_index(drop=True)
    ses = pd.read_csv(f'{D}/realistic/sessions.csv').set_index('session').z
    out = {}
    for v in ['frame_2', 'frame_5', 'walk_05', 'session_5']:
        a = pd.read_csv(f'{D}/variants/{v}/annotations.csv')
        a = a[a.split == 'test'].reset_index(drop=True)
        m = pd.read_csv(f'{D}/variants/{v}/metadata.csv')
        m = m[m.split == 'test'].reset_index(drop=True)
        cols_meta = ['image_id', 'filename', 'split', 'session', 'n_letters', 'n_outside', 'n_dust', 'classes']
        line = (f'  {v}: {len(a)} letters, {len(m)} images; annotations except z identical: {same(a, base_ann, KEYS)}; '
                f'depth identical: {(a.depth.values == base_ann.depth.values).all()}; metadata except z identical: '
                f'{same(m, base_meta, cols_meta)}')
        i = m.image_id.to_numpy()
        zs = ses.loc[m.session].to_numpy()
        rel = m.z.to_numpy() / zs - 1
        if v.startswith('frame'):
            sd = 0.02 if v == 'frame_2' else 0.05
            h = np.array([random.Random(SEED * 1_000_000 + int(k) + 800_000_000).gauss(0.0, 1.0) for k in i])
            line += (f'; z == z_session (1 + {sd} h) recomputed: max |diff| {np.abs(m.z - zs * (1 + sd * h)).max():.1e} m;'
                     f' measured jitter sd {rel.std(ddof=1):.4f} (design {sd}), mean {rel.mean():+.4f}')
        elif v == 'walk_05':
            design = np.array([session_walk(SEED * 1000 + int(s), 100, 0.005)[int(k) % 100]
                               for s, k in zip(m.session, i)])
            first = m.groupby('session').z.first().to_numpy() / ses.loc[sorted(m.session.unique())].to_numpy() - 1
            steps = np.concatenate([np.diff(m.z[m.session == s].to_numpy() / ses[s] - 1) for s in m.session.unique()])
            line += (f'; z == z_session (1 + walk) recomputed: max |diff| {np.abs(m.z - zs * (1 + design)).max():.1e} m; '
                     f'first image of each session at the session z: max |rel| {np.abs(first).max():.1e}; step sd '
                     f'{steps.std(ddof=1):.5f} (design 0.005), {len(steps)} steps; |drift| after 99 steps: mean '
                     f'{np.mean([abs(rel[m.session == s][-1]) for s in m.session.unique()]):.4f}')
        else:
            sz = pd.read_csv(f'{D}/variants/{v}/sessions.csv').set_index('session').z
            line += f'; z == its session z: {np.array_equal(m.z.to_numpy(), sz.loc[m.session].to_numpy())}'
        out[v] = (m, rel)
        print(line)
    return out


def pixels(win):
    print('(d) pixels')
    m, rel = win['frame_5']
    base = np.load(f'{D}/realistic/holograms.npy', mmap_mode='r')
    f5 = np.load(f'{D}/variants/frame_5/holograms.npy', mmap_mode='r')
    bm = pd.read_csv(f'{D}/realistic/metadata.csv')
    pos = dict(zip(bm.image_id, range(len(bm))))       # row of an image in the base set
    order = np.argsort(np.abs(rel))
    print('  frame_5 against the same base image (uint8 levels); |jitter| = |z / z_session - 1|')
    for j in list(order[:5]) + list(order[len(order) // 2:len(order) // 2 + 1]) + list(order[-1:]):
        i = int(m.image_id[j])
        a, b = base[pos[i]].astype(np.int16), f5[j].astype(np.int16)
        d = np.abs(a - b)
        print(f'    image {i:5d}, |jitter| {abs(rel[j]) * 100:7.4f} %: differing pixels {(d > 0).mean() * 100:6.3f} %, '
              f'mean |diff| {d.mean():.4f}, max {d.max()}, corr {np.corrcoef(a.ravel(), b.ravel())[0, 1]:.6f}')
    i, k = int(m.image_id[order[0]]), int(m.image_id[order[1]])
    d = np.abs(base[pos[i]].astype(np.int16) - base[pos[k]].astype(np.int16))
    print(f'    scale, two different base images ({i}, {k}): differing pixels {(d > 0).mean() * 100:.3f} %, mean |diff| '
          f'{d.mean():.4f}')
    a = np.load(f'{D}/full_frames/holograms.npy', mmap_mode='r')
    b = np.load(f'{D}/full_frames_tilt0/holograms.npy', mmap_mode='r')
    n = mx = tot = 0
    per = []
    for k in range(len(a)):
        d = np.abs(a[k].astype(np.int16) - b[k].astype(np.int16))
        n += int((d > 0).sum())
        tot += d.size
        mx = max(mx, int(d.max()))
        per.append((d > 0).mean())
    print(f'  full_frames_tilt0 against full_frames: differing pixels {n} of {tot} = {n / tot * 100:.4f} %, max |diff| '
          f'{mx} levels, frames with a difference {sum(p > 0 for p in per)}/{len(per)}')


if __name__ == '__main__':
    full_frames()
    pixels(windows())
