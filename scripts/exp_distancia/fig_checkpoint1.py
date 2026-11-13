"""Checkpoint 1 of the distance study (docs/exp_distancia): one test image of the base set recorded three times, as
generate() records one image, with the base physics, with a distance per frame of 5 % and with a slide tilted by 10 deg.

    python scripts/exp_distancia/fig_checkpoint1.py --device cuda:N [--image 1]

Rows: the hologram; the hologram minus the base hologram; the modulus of the back-propagation at the nominal distance
z0 (flat field with the blank frame of the session). The recording with the base physics is compared bit by bit with
the row of data/realistic/holograms.npy. Output: docs/exp_distancia/img/checkpoint1_holograms.png
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.model import pick_device
from holo_openset.paper.style import plt, setup, show
from holo_openset.reconstruct import backprop, normalise
from holo_openset.sim import generate as G
from holo_openset.sim.letters import CLASSES, FONTS
from holo_openset.sim.physics import physics_from_dict, record, sensor_intensity
from holo_openset.sim.scene import Layout, camera, session

OUT = Path(__file__).resolve().parents[2] / 'docs/exp_distancia/img/checkpoint1_holograms.png'


def recording(phys, seed, per_session, image_id, dev):
    """One image recorded as generate() records it -> hologram (uint8 [h, w]), the session as the image saw it, the
    depths of its letters (m, from the distance of the session)."""
    cam = camera(G.CAMERA_SEED, phys)
    s = image_id // per_session
    ses = session(seed * 1000 + s, phys)
    G._init((phys, CLASSES, FONTS, None, Layout))
    sc = G._scene(seed * 1_000_000 + image_id)   # a fresh scene: apply_tilt changes it in place
    ses = G.frame_session(ses, phys, seed * 1_000_000 + image_id, 0.0)
    G.apply_tilt(sc, phys, seed * 1000 + s)
    sc['sensor_dust'] = cam['dust']
    g = torch.Generator(device=dev).manual_seed(seed * 1_000_000 + image_id + 700_000_000)
    img = record(sensor_intensity(sc, ses, phys, dev), ses, phys, cam, g, dev)
    return img, ses, np.array([r['depth'] for r in sc['rows']])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--device', default='cuda:0')
    ap.add_argument('--image', type=int, default=None, help='image id (default: the first test image with >= 8 letters)')
    a = ap.parse_args()
    dev = pick_device(a.device)
    root = paths.dataset(paths.BASE)
    info = json.load(open(root / 'physics.json'))
    phys = physics_from_dict(info['physics'])
    seed, per_session = info['seed'], info['per_session']
    meta = pd.read_csv(root / 'metadata.csv')
    i = a.image if a.image is not None else int(meta[(meta.split == 'test') & (meta.n_letters >= 8)].image_id.iloc[0])
    m = meta.set_index('image_id').loc[i]
    assert m.split == 'test' and m.n_letters >= 8, (i, m.split, m.n_letters)
    row = int(np.where(meta.image_id.to_numpy() == i)[0][0])
    stored = np.load(root / 'holograms.npy', mmap_mode='r')[row]
    bg = torch.from_numpy(np.array(np.load(root / 'backgrounds.npy', mmap_mode='r')[int(m.session)])).to(dev)
    print(f'image {i}: session {m.session}, {m.n_letters} letters, z {m.z * 1e3:.4f} mm')

    cases = [('base', {}), ('distance per frame 5 %', dict(frame_z_std=0.05)), ('tilt 10 deg', dict(tilt_deg=10.0))]
    out = []
    for name, kw in cases:
        img, ses, depth = recording(phys.replace(**kw), seed, per_session, i, dev)
        out.append((name, img, ses, depth))
        print(f'{name}: z {ses["z"] * 1e3:.4f} mm, letter depths {depth.min() * 1e6:.1f} to {depth.max() * 1e6:.1f} um')

    base = out[0][1].astype(np.int16)
    diff = base != stored
    if diff.any():
        print(f'base recording vs data/realistic/holograms.npy row {row}: NOT identical, '
              f'{diff.mean():.4%} of the pixels differ (max |d| {np.abs(base - stored.astype(np.int16)).max()})')
    else:
        print(f'base recording vs data/realistic/holograms.npy row {row}: identical bit by bit')

    setup()
    fig, axes = plt.subplots(3, 3, figsize=(7.0, 7.4))
    # the difference maps share one scale, the 99.5th percentile of |difference| (a few pixels go further)
    lim = max(1, int(np.ceil(np.percentile(np.concatenate([np.abs(o[1].astype(np.int16) - base).ravel()
                                                           for o in out[1:]]), 99.5))))
    z_ses = out[0][2]['z']
    for c, (name, img, ses, depth) in enumerate(out):
        title = f'{name}\nz = {ses["z"] * 1e3:.3f} mm ({(ses["z"] / z_ses - 1) * 100:+.2f} %)'
        title += f'\nletters {depth.min() * 1e6:+.0f} to {depth.max() * 1e6:+.0f} um from z'
        show(axes[0, c], img, title)
        d = img.astype(np.int16) - base
        show(axes[1, c], d, 'hologram - base' + ('' if c else ' (zero)'), cmap='RdBu_r', vmin=-lim, vmax=lim)
        u = backprop(normalise(torch.from_numpy(np.ascontiguousarray(img)).to(dev), bg), [phys.z0])[0]
        show(axes[2, c], u.abs().cpu().numpy(), f'|U| at z0 = {phys.z0 * 1e3:.2f} mm')
    fig.suptitle(f'Test image {i} of the base set (session {m.session}, {m.n_letters} letters), recorded three times; '
                 f'difference scale +-{lim} grey levels', fontsize=7.5)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches='tight', pad_inches=0.02)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
