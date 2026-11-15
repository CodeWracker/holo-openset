"""Checks of the sets recorded again at another distance (distance tests, CADERNO_CURVA_DISTANCIA.md; run by
scripts/exp_resolucao/distance_tests.sh, step `checks`). For each set of --sets (a split of --ref recorded again with
simulate like and only z0 changed), against --ref:

  physics.json   the only differences: physics.z0 (= --z0) and the keys like / split; the depth law (every physics
                 field with 'depth' in its name) written out and compared with that of --ref
  annotations    the rows of that split of --ref, every column equal except z; and z - depth (the session distance)
                 equal to that of --ref times z0 / z0_ref (the session draws are relative, so they must scale exactly)
  metadata.csv   the rows of that split, every column equal except z, and z in the same ratio
  sessions.csv   every column equal except z, and z in the same ratio
  dust.csv       the rows of that split, equal
  camera         camera(CAMERA_SEED, physics, layout) of the set and of --ref: the same PRNU and the same window dust
  backgrounds    the blank frames of the sessions of that split against those of --ref (recorded, not required equal)
  rebuilt        one image (the first of the first session of the split) rebuilt from its seed and recorded with the
                 physics of the set exactly as generate() records it, against the stored hologram (equal = the set is
                 what the seeds say), and the same image of --ref (must differ: the distance changed)
-> one json with a block per set (--out), printed.

    python scripts/exp_resolucao/distance_checks.py --sets bench_1mm_robust/z09 bench_1mm_robust/z09_val \
        --ref bench_1mm --z0 0.9e-3 --out $HOLO_RESULTS/distance_checks_z09.json --device cuda:N
"""
import argparse
import json

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.model import pick_device
from holo_openset.sim.generate import CAMERA_SEED, frame_session, layout_of
from holo_openset.sim.physics import physics_from_dict, record, sensor_intensity
from holo_openset.sim.scene import camera, make_scene, session


def scene_of(i, cfg, phys, lay):
    """As generate._scene (the same as controls_checks.scene_of)."""
    seed = cfg['seed'] * 1_000_000 + int(i)
    while True:
        sc = make_scene(seed, phys, lay=lay)
        if sc is not None:
            return sc
        seed += 7919 * 1000003


def record_as_generate(sc, i, cfg, phys, cam, dev):
    """What generate() stores for image i of a set (no tilt, no drift in these sets; as controls_checks)."""
    seed, per = cfg['seed'], cfg['per_session']
    s = int(i) // per
    ses = frame_session(session(seed * 1000 + s, phys), phys, seed * 1_000_000 + int(i))
    sc = dict(sc, sensor_dust=cam['dust'])
    g = torch.Generator(device=dev).manual_seed(seed * 1_000_000 + int(i) + 700_000_000)
    return record(sensor_intensity(sc, ses, phys, dev), ses, phys, cam, g, dev)


def ratio_check(new, ref, ratio):
    """new / ref against the ratio of the nominal distances: max relative deviation."""
    r = np.asarray(new, float) / np.asarray(ref, float)
    return dict(ratio_expected=ratio, ratio_min=float(r.min()), ratio_max=float(r.max()),
                max_rel_dev=float(np.abs(r / ratio - 1).max()))


def frame_equal(a, b, keep, drop):
    """Columns of `keep` except `drop`, row by row, after resetting the index."""
    a, b = a.reset_index(drop=True), b.reset_index(drop=True)
    cols = [c for c in keep if c not in drop]
    return dict(rows=len(a), rows_ref=len(b), same_columns=list(a.columns) == list(b.columns),
                columns_equal={c: bool(len(a) == len(b) and a[c].equals(b[c])) for c in cols})


def check(name, ref, z0, dev):
    root, rroot = paths.dataset(name), paths.dataset(ref)
    cfg, rcfg = json.load(open(root / 'physics.json')), json.load(open(rroot / 'physics.json'))
    split = cfg['split']
    res = dict(set=name, ref=ref, split=split)
    top = {k: (cfg.get(k), rcfg.get(k)) for k in set(cfg) | set(rcfg) if k != 'physics' and cfg.get(k) != rcfg.get(k)}
    ph = {k: (cfg['physics'].get(k), rcfg['physics'].get(k)) for k in set(cfg['physics']) | set(rcfg['physics'])
          if cfg['physics'].get(k) != rcfg['physics'].get(k)}
    res['physics_json_differences'] = dict(top=top, physics=ph)
    res['physics_only_z0'] = set(ph) == {'z0'} and abs(cfg['physics']['z0'] - z0) < 1e-12 and set(top) <= {'like', 'split'}
    ratio = cfg['physics']['z0'] / rcfg['physics']['z0']
    # the depth law the set was recorded with (every physics field with 'depth' in its name), and that of --ref
    res['depth_law'] = {k: v for k, v in cfg['physics'].items() if 'depth' in k}
    res['depth_law_equal_ref'] = res['depth_law'] == {k: v for k, v in rcfg['physics'].items() if 'depth' in k}

    A, R = pd.read_csv(root / 'annotations.csv'), pd.read_csv(rroot / 'annotations.csv')
    R = R[R.split == split]
    res['annotations'] = frame_equal(A, R, list(R.columns), ['z'])
    res['annotations']['session_z'] = ratio_check(A.z - A.depth, R.z.to_numpy() - R.depth.to_numpy(), ratio)
    M, MR = pd.read_csv(root / 'metadata.csv'), pd.read_csv(rroot / 'metadata.csv')
    MR = MR[MR.split == split]
    res['metadata'] = frame_equal(M, MR, list(MR.columns), ['z'])
    res['metadata']['z'] = ratio_check(M.z, MR.z, ratio)
    res['metadata']['z_mm'] = dict(min=float(M.z.min() * 1e3), mean=float(M.z.mean() * 1e3), max=float(M.z.max() * 1e3))
    S, SR = pd.read_csv(root / 'sessions.csv'), pd.read_csv(rroot / 'sessions.csv')
    res['sessions'] = frame_equal(S, SR, list(SR.columns), ['z'])
    res['sessions']['z'] = ratio_check(S.z, SR.z, ratio)
    D, DR = pd.read_csv(root / 'dust.csv'), pd.read_csv(rroot / 'dust.csv')
    DR = DR[DR.image_id.isin(M.image_id)]
    res['dust'] = frame_equal(D, DR, list(DR.columns), [])

    phys, rphys = physics_from_dict(cfg['physics']), physics_from_dict(rcfg['physics'])
    lay, rlay = layout_of(cfg), layout_of(rcfg)
    cam, rcam = camera(cfg.get('camera_seed', CAMERA_SEED), phys, lay), camera(rcfg.get('camera_seed', CAMERA_SEED),
                                                                               rphys, rlay)
    same_dust = len(cam['dust']) == len(rcam['dust']) and all(
        all(np.array_equal(np.asarray(a[k]), np.asarray(b[k])) for k in a) and set(a) == set(b)
        for a, b in zip(cam['dust'], rcam['dust']))
    res['camera'] = dict(prnu_equal=bool(torch.equal(cam['prnu'], rcam['prnu'])), window_dust_n=len(cam['dust']),
                         window_dust_equal=bool(same_dust), seed=cfg.get('camera_seed'),
                         layout_params_equal=cfg.get('layout_params') == rcfg.get('layout_params'))

    used = sorted(M.session.unique())
    bg, rbg = np.load(root / 'backgrounds.npy', mmap_mode='r'), np.load(rroot / 'backgrounds.npy', mmap_mode='r')
    d = np.array([np.abs(bg[s] - rbg[s]).max() for s in used])
    res['backgrounds'] = dict(sessions=[int(s) for s in used], equal_to_ref=bool((d == 0).all()),
                              max_abs_diff_dn=float(d.max()), mean_level=float(np.mean([bg[s].mean() for s in used])),
                              mean_level_ref=float(np.mean([rbg[s].mean() for s in used])))

    i = int(M[M.session == used[0]].image_id.min())
    k = int(np.where(M.image_id.to_numpy() == i)[0][0])
    sc = scene_of(i, cfg, phys, lay)
    img = record_as_generate(sc, i, cfg, phys, cam, dev)
    holo = np.load(root / 'holograms.npy', mmap_mode='r')
    rholo = np.load(rroot / 'holograms.npy', mmap_mode='r')
    diff = img.astype(int) - holo[k].astype(int)
    dref = holo[k].astype(float) - rholo[i].astype(float)
    res['rebuilt'] = dict(image_id=i, row=k, session=int(used[0]), n_letters=len(sc['rows']),
                          equal_stored=bool(np.array_equal(img, holo[k])), max_abs_dn=int(np.abs(diff).max()),
                          stored_minus_ref_rms_dn=float(dref.std()), stored_minus_ref_max_abs_dn=float(np.abs(dref).max()))
    print(json.dumps(res, indent=1, default=float), flush=True)
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sets', nargs='+', required=True)
    ap.add_argument('--ref', default='bench_1mm')
    ap.add_argument('--z0', type=float, required=True, help='the distance the sets must have been recorded at (m)')
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    torch.set_num_threads(4)
    dev = pick_device(a.device)
    out = {s: check(s, a.ref, a.z0, dev) for s in a.sets}
    json.dump(out, open(a.out, 'w'), indent=1, default=float)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
