"""R4 of the pilot at 1.0 mm (CADERNO_PILOTO_1MM.md): sanity of a recorded set before training, against the base set.
Reads only the TRAIN split (nothing is looked at on validation or test).

  contact sheet   8 panels: 4 whole holograms of train sessions and 4 zooms (192 x 192 px) around one of their
                  letters; boxes drawn on half of each (2 + 2) -> docs/exp_resolucao/img/<set>_examples.png
  set             images per split, letters per image, box side p5 / p50 / p95 (the integer box, and the ink box when
                  the set has it), Fresnel number of those sides at the set's z0
  exposure        mean grey level of 100 train holograms, and of their blank frames
  noise           4 train holograms rebuilt from their seeds and recorded again WITHOUT shot noise, read noise and
                  quantisation (same scene, session, camera, PRNU): stored - noise-free = the noise of the recording
                  (mean and rms in grey levels; the mean near 0 also says the set is rebuilt exactly from its seeds)
-> $HOLO_RESULTS/<set>_sanity.json (and the same for --ref, the base set, without the contact sheet)

    python scripts/exp_resolucao/bench_sanity.py --set bench_1mm --ref realistic --device cuda:N
"""
import argparse
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np   # noqa: E402
import pandas as pd   # noqa: E402
import torch   # noqa: E402

from holo_openset import paths   # noqa: E402
from holo_openset.model import pick_device   # noqa: E402
from holo_openset.sim.generate import CAMERA_SEED, layout_of   # noqa: E402
from holo_openset.sim.physics import PIXEL, WAVELENGTH, physics_from_dict, record, sensor_intensity   # noqa: E402
from holo_openset.sim.scene import camera, make_scene, session   # noqa: E402

IMG = paths.PROJECT / 'docs' / 'exp_resolucao' / 'img'


def scene_of(i, cfg, phys, lay):
    seed = cfg['seed'] * 1_000_000 + int(i)
    while True:   # as generate._scene
        sc = make_scene(seed, phys, lay=lay)
        if sc is not None:
            return sc
        seed += 7919 * 1000003


def stats(name, dev, n_noise=4):
    root = paths.dataset(name)
    cfg = json.load(open(root / 'physics.json'))
    phys = physics_from_dict(cfg['physics'])
    meta = pd.read_csv(root / 'metadata.csv')
    ann = pd.read_csv(root / 'annotations.csv')
    holo = np.load(root / 'holograms.npy', mmap_mode='r')
    bg = np.load(root / 'backgrounds.npy', mmap_mode='r')
    row = {int(i): k for k, i in enumerate(meta.image_id)}
    side = np.maximum(ann.x1 - ann.x0, ann.y1 - ann.y0).to_numpy(float)
    q = [5, 50, 95]
    nf = lambda L: (L * PIXEL / 2) ** 2 / (WAVELENGTH * phys.z0)   # noqa: E731
    out = dict(set=name, z0_mm=phys.z0 * 1e3, oversample=getattr(phys, 'oversample', 1),
               images=dict(meta.groupby('split').size()), letters_per_image=dict(
                   mean=float(meta.n_letters.mean()), min=int(meta.n_letters.min()), max=int(meta.n_letters.max())),
               box_side_px_p5_p50_p95=[float(v) for v in np.percentile(side, q)],
               fresnel_p5_p50_p95=[float(nf(v)) for v in np.percentile(side, q)])
    if 'bx0' in ann:
        ink = np.maximum(ann.bx1 - ann.bx0, ann.by1 - ann.by0).to_numpy(float)
        out.update(ink_side_px_p5_p50_p95=[float(v) for v in np.percentile(ink, q)],
                   fresnel_ink_p5_p50_p95=[float(nf(v)) for v in np.percentile(ink, q)])
    train = meta[meta.split == 'train']
    ids = train.image_id.to_numpy()[np.linspace(0, len(train) - 1, 100).astype(int)]
    out['mean_grey_100_train'] = float(np.mean([holo[row[int(i)]].mean() for i in ids]))
    out['mean_grey_blank_train_sessions'] = float(np.mean([bg[s].mean() for s in train.session.unique()]))
    # the noise: rebuild and record without noise
    lay = layout_of(cfg)
    cam = camera(cfg.get('camera_seed', CAMERA_SEED), phys, lay)
    clean = phys.replace(full_well=0.0, read_noise=0.0, bits=0)
    res = []
    for i in ids[:n_noise]:
        i = int(i)
        sc = scene_of(i, cfg, phys, lay)
        sc['sensor_dust'] = cam['dust']
        ses = session(cfg['seed'] * 1000 + i // cfg['per_session'], phys)
        nf_img = record(sensor_intensity(sc, ses, clean, dev), ses, clean, cam, None, dev)
        d = holo[row[i]].astype(np.float64) - nf_img
        res.append((float(d.mean()), float(d.std()), float(nf_img.std())))
    out['noise'] = dict(image_ids=[int(i) for i in ids[:n_noise]], mean_dn=[r[0] for r in res],
                        rms_dn=[r[1] for r in res], noise_free_std_dn=[r[2] for r in res])
    return out, (root, meta, ann, holo)


def contact(name, data, out):
    root, meta, ann, holo = data
    row = {int(i): k for k, i in enumerate(meta.image_id)}
    train = meta[meta.split == 'train']
    first = train.groupby('session').image_id.min().to_numpy()
    pick = first[np.linspace(0, len(first) - 1, 4).astype(int)]
    fig, axes = plt.subplots(2, 4, figsize=(13, 6.8), constrained_layout=True)
    for k, i in enumerate(pick):
        img = holo[row[int(i)]]
        boxes = ann[ann.image_id == i]
        lo, hi = np.percentile(img, 0.5), np.percentile(img, 99.5)
        ax = axes[0, k]
        ax.imshow(img, cmap='gray', vmin=lo, vmax=hi, interpolation='nearest')
        r = boxes.iloc[0]
        cx, cy = int((r.x0 + r.x1) / 2), int((r.y0 + r.y1) / 2)
        z0, z1 = min(max(cx - 96, 0), 640 - 192), min(max(cy - 96, 0), 640 - 192)
        ax.add_patch(plt.Rectangle((z0 - 0.5, z1 - 0.5), 192, 192, fill=False, ec='#3182bd', lw=0.8, ls=':'))
        zax = axes[1, k]
        zax.imshow(img[z1:z1 + 192, z0:z0 + 192], cmap='gray', vmin=lo, vmax=hi, interpolation='nearest')
        if k % 2 == 0:   # boxes on half of the panels
            for _, b in boxes.iterrows():
                for a_, off in ((ax, (0, 0)), (zax, (z0, z1))):
                    a_.add_patch(plt.Rectangle((b.x0 - off[0] - 0.5, b.y0 - off[1] - 0.5), b.x1 - b.x0, b.y1 - b.y0,
                                               fill=False, ec='#e6550d', lw=0.7))
        ax.set_title(f'image {int(i)} (train, session {int(meta.session[row[int(i)]])}), {len(boxes)} letters'
                     + (', boxes' if k % 2 == 0 else ''), fontsize=8)
        zax.set_title(f'zoom 192 x 192 px around {r.classe}' + (', boxes' if k % 2 == 0 else ''), fontsize=8)
        for a_ in (ax, zax):
            a_.set_xticks([])
            a_.set_yticks([])
    fig.suptitle(f'{name}: holograms as stored (8 bits), grey range 0.5-99.5 percentile of each image', fontsize=9)
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--set', required=True)
    ap.add_argument('--ref', help='the base set to compare with')
    ap.add_argument('--device', default='cpu')
    a = ap.parse_args()
    torch.set_num_threads(4)
    dev = pick_device(a.device)
    res, data = stats(a.set, dev)
    contact(a.set, data, IMG / f'{a.set}_examples.png')
    res['contact_sheet'] = str((IMG / f'{a.set}_examples.png').relative_to(paths.PROJECT))
    if a.ref:
        res['ref'] = stats(a.ref, dev)[0]
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(paths.RESULTS / f'{a.set}_sanity.json', 'w'), indent=1, default=int)
    print(json.dumps(res, indent=1, default=int))


if __name__ == '__main__':
    main()
