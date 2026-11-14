"""The oversampled recording of the pilot at 1.0 mm (docs/exp_resolucao/CADERNO_PILOTO_1MM.md, P0): the convergence
test of the oversampling factor, and the measurement of the margin and reach of the simulated field. Nothing is
recorded but the tables.

Scenes: 8 seeded scenes of the layout of the pilot (FresnelLayout, letters x 0.22792, the same physical scene for every
grid), the seeds and sessions of the images 0, 625, ..., 4375 of a set made by `generate` (seed 17), the camera of the
sets (seed 7). Physics: that of the set (`--margin`, `--reach`, z0 = 1.0 mm or 0.7 mm, the depth spread of the letters
given), WITHOUT noise or quantisation (full_well = read_noise = prnu = bits = 0): the camera values of a noise-free
recording, in grey levels of 8 bits (the background at the centre of the beam is 0.45 x 255).

  converge   for each scene and pair (s, 2s) of oversampling factors (s = 1 is the simulator of the paper):
               rel_rms      rms(I_s - I_2s) over the window / rms(I_2s - B_2s), B the recording of the same session
                            without objects (the blank frame, sensor dust still there) on the same grid
               max_abs_dn   max |I_s - I_2s| in grey levels
               rel_noise    rms(I_s - I_2s) / rms of the noise of a real recording at the exposure of the set (shot
                            noise of a full well of 6000 e- and 3 e- of read noise, on I_2s)
               hf_share     share of the energy of I_s - I_2s above half the Nyquist frequency of the sensor
               rel_rms_letters / rel_rms_rest   the same as rel_rms inside the letter boxes (+25 %) / elsewhere
             and the time and peak GPU memory of one recording (intensity + camera) at each s.
             Pass (P0): rel_rms <= 1 % in every scene, at 1.0 mm and at 0.7 mm; the set is recorded with the
             smallest s whose pair (s, 2s) passes.
             -> $HOLO_RESULTS/oversampling_convergence.csv (one row per distance, depth spread, scene and pair) and
                oversampling_timing.csv
  reach      the letters and dust farther than R from the window: a scene drawn with reach 2R, recorded with all its
             objects and without those not entirely within R of the window; rel_change = rms(difference) / rms of the
             pattern, per scene. -> oversampling_reach.csv
  margin     the same scene recorded with margin m and 2m (the periodic field wraps around less): rel_change =
             rms(I_m - I_2m) / rms of the pattern of I_2m. -> oversampling_margin.csv
  dump       the noise-free recordings (and blank frames) of the 8 scenes at the first factor of --s, to --out (npz):
             run it with two versions of the package (PYTHONPATH) to compare two recorders
  compare    two dumps A B: rms(A - B) / rms of the pattern of B, per scene -> --out (csv)

    python scripts/exp_resolucao/oversampling_convergence.py reach --device cuda:N --s 4 --reach 117 233 350
    python scripts/exp_resolucao/oversampling_convergence.py margin --device cuda:N --s 4 --reach R --margin 197 394
    python scripts/exp_resolucao/oversampling_convergence.py converge --device cuda:N --margin M --reach R
"""
import argparse
import math
import time

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.model import pick_device
from holo_openset.sim.generate import CAMERA_SEED
from holo_openset.sim.physics import Physics, record, sensor_intensity
from holo_openset.sim.scene import FresnelLayout, camera, make_scene, session

SEED = 17
IDS = [k * 625 for k in range(8)]     # sessions 0, 6, 12, 18, 25, 31, 37, 43 of a set of 50 sessions of 100
NOISE_FREE = dict(full_well=0.0, read_noise=0.0, prnu=0.0, bits=0)
FULL_WELL, READ_NOISE = Physics.full_well, Physics.read_noise
DEPTHS = {'50um': (50e-6, 150e-6), '2.6um': (2.6e-6, 7.8e-6)}   # depth_std, depth_max: the two candidates (P1)


def physics(z_mm, margin, reach, depth, s=1):
    return Physics().replace(z0=z_mm * 1e-3, margin=margin, reach=reach, depth_std=DEPTHS[depth][0],
                             depth_max=DEPTHS[depth][1], oversample=s, **NOISE_FREE)


def scene(i, phys, lay):
    seed = SEED * 1_000_000 + i
    while True:   # as generate._scene
        sc = make_scene(seed, phys, lay=lay)
        if sc is not None:
            return sc
        seed += 7919 * 1000003


def recording(sc, ses, phys, cam, dev, sample=True):
    """Noise-free camera values (float64 [h, w], grey levels of 8 bits) and the seconds it took."""
    if dev.type == 'cuda':
        torch.cuda.synchronize()
    t0 = time.time()
    inten = sensor_intensity(sc, ses, phys, dev, sample=sample)
    out = torch.from_numpy(record(inten, ses, phys, cam, None, dev)).double()
    if dev.type == 'cuda':
        torch.cuda.synchronize()
    return out, time.time() - t0


def noise_rms(dn):
    """rms over the window of the noise of a real recording of camera values dn (shot + read noise)."""
    e = dn * FULL_WELL / 255
    return float(torch.sqrt(((255 / FULL_WELL) ** 2 * (e.clamp(min=0) + READ_NOISE ** 2)).mean()))


def box_mask(rows, shape, buffer=0.25):
    m = torch.zeros(shape, dtype=torch.bool)
    for r in rows:
        cx, cy = (r['x0'] + r['x1']) / 2, (r['y0'] + r['y1']) / 2
        half = max(r['x1'] - r['x0'], r['y1'] - r['y0']) * (1 + buffer) / 2
        m[max(0, int(cy - half)):int(math.ceil(cy + half)), max(0, int(cx - half)):int(math.ceil(cx + half))] = True
    return m


def hf_share(d):
    e = torch.fft.fft2(d).abs() ** 2
    f = torch.fft.fftfreq(d.shape[0], dtype=torch.float64).abs()
    hi = (f[None, :] > 0.25) | (f[:, None] > 0.25)
    return float(e[hi].sum() / e.sum().clamp(min=1e-30))


def converge(a, dev):
    rows, timing = [], []
    lay = FresnelLayout(**a.layout)
    for depth in a.depths:
        for z in a.z:
            p1 = physics(z, a.margin, a.reach, depth)
            cam = camera(CAMERA_SEED, p1, lay)
            for i in IDS[::len(IDS) // a.n_scenes]:
                sc = scene(i, p1, lay)
                sc['sensor_dust'] = cam['dust']
                ses = session(SEED * 1000 + i // 100, p1)
                prev = None
                for s in a.s:
                    p = p1.replace(oversample=s)
                    if dev.type == 'cuda':
                        torch.cuda.reset_peak_memory_stats()
                    img, dt = recording(sc, ses, p, cam, dev)
                    mem = torch.cuda.max_memory_allocated() / 2 ** 30 if dev.type == 'cuda' else math.nan
                    timing.append(dict(z_mm=z, depth=depth, image_id=i, s=s, seconds=dt, peak_gib=mem))
                    if prev is not None:
                        blank, _ = recording(sc, ses, p, cam, dev, sample=False)
                        d = prev[1] - img
                        pat = img - blank
                        inside = box_mask(sc['rows'], d.shape)
                        rows.append(dict(z_mm=z, depth=depth, letters_mean=lay.letters_mean, image_id=i, session=i // 100, n_letters=len(sc['rows']),
                                         s=prev[0], s2=s, rel_rms=float(d.std() / pat.std()),
                                         max_abs_dn=float(d.abs().max()), rms_dn=float(d.pow(2).mean().sqrt()),
                                         pattern_rms_dn=float(pat.std()), noise_rms_dn=noise_rms(img),
                                         rel_noise=float(d.pow(2).mean().sqrt()) / noise_rms(img),
                                         hf_share=hf_share(d),
                                         rel_rms_letters=float(d[inside].pow(2).mean().sqrt() / pat.std()),
                                         rel_rms_rest=float(d[~inside].pow(2).mean().sqrt() / pat.std())))
                        print({k: (round(v, 5) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)
                    prev = (s, img)
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    t = pd.DataFrame(rows)
    t.to_csv(paths.RESULTS / f'oversampling_convergence{a.tag}.csv', index=False, float_format='%.6g')
    pd.DataFrame(timing).to_csv(paths.RESULTS / f'oversampling_timing{a.tag}.csv', index=False, float_format='%.6g')
    summary = t.groupby(['depth', 'z_mm', 's', 's2']).agg(rel_rms_max=('rel_rms', 'max'), rel_rms_mean=('rel_rms', 'mean'),
                                                          max_abs_dn=('max_abs_dn', 'max'),
                                                          rel_noise_max=('rel_noise', 'max'))
    summary['pass'] = summary.rel_rms_max <= 0.01
    print(summary.to_string())
    ok = summary.groupby(['s', 's2'])['pass'].all()
    chosen = next((int(s) for (s, s2), v in ok.items() if v), None)
    print('pairs passing at every distance and depth spread:', [k for k, v in ok.items() if v],
          '-> oversampling', chosen)


def within(o, phys, r):
    """The object lies entirely within r pixels of the window."""
    m0, (h, w) = phys.margin, phys.window
    mh, mw = o['mask'].shape
    return o['x'] >= m0 - r and o['y'] >= m0 - r and o['x'] + mw <= m0 + w + r and o['y'] + mh <= m0 + h + r


def reach(a, dev):
    rows = []
    lay = FresnelLayout()
    for depth in a.depths:
        for z in a.z:
            for r in a.reach:
                p = physics(z, a.margin_reach or 2 * r + 256, 2 * r, depth, a.s[0])
                cam = camera(CAMERA_SEED, p, lay)
                for i in IDS:
                    sc = scene(i, p, lay)
                    sc['sensor_dust'] = cam['dust']
                    ses = session(SEED * 1000 + i // 100, p)
                    full, _ = recording(sc, ses, p, cam, dev)
                    near = dict(sc, objects=[o for o in sc['objects'] if within(o, p, r)],
                                dust=[o for o in sc['dust'] if within(o, p, r)])
                    cut, _ = recording(near, ses, p, cam, dev)
                    blank, _ = recording(sc, ses, p, cam, dev, sample=False)
                    d = full - cut
                    rows.append(dict(z_mm=z, depth=depth, image_id=i, s=a.s[0], reach=r, margin=p.margin,
                                     n_removed=len(sc['objects']) + len(sc['dust']) - len(near['objects'])
                                     - len(near['dust']), rel_change=float(d.std() / (full - blank).std()),
                                     max_abs_dn=float(d.abs().max())))
                    print({k: (round(v, 5) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)
    t = pd.DataFrame(rows)
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    t.to_csv(paths.RESULTS / 'oversampling_reach.csv', index=False, float_format='%.6g')
    print(t.groupby(['depth', 'z_mm', 'reach']).rel_change.agg(['max', 'mean']).to_string())


def margin(a, dev):
    rows = []
    lay = FresnelLayout()
    for depth in a.depths:
        for z in a.z:
            for m in a.margin_list:
                imgs = []
                for mm in (m, 2 * m):
                    p = physics(z, mm, a.reach[0], depth, a.s[0])
                    cam = camera(CAMERA_SEED, p, lay)
                    out = []
                    for i in IDS:
                        sc = scene(i, p, lay)
                        sc['sensor_dust'] = cam['dust']
                        ses = session(SEED * 1000 + i // 100, p)
                        img, _ = recording(sc, ses, p, cam, dev)
                        blank, _ = recording(sc, ses, p, cam, dev, sample=False)
                        out.append((sc['rows'], len(sc['objects']), len(sc['dust']), img, blank))
                    imgs.append(out)
                for i, (x, y) in zip(IDS, zip(*imgs)):
                    assert x[0] == y[0] and x[1:3] == y[1:3], 'the scene moved with the margin'
                    d = x[3] - y[3]
                    rows.append(dict(z_mm=z, depth=depth, image_id=i, s=a.s[0], reach=a.reach[0], margin=m,
                                     margin2=2 * m, rel_change=float(d.std() / (y[3] - y[4]).std()),
                                     max_abs_dn=float(d.abs().max())))
                    print({k: (round(v, 5) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)
    t = pd.DataFrame(rows)
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    t.to_csv(paths.RESULTS / 'oversampling_margin.csv', index=False, float_format='%.6g')
    print(t.groupby(['depth', 'z_mm', 'margin']).rel_change.agg(['max', 'mean']).to_string())


def dump(a, dev):
    lay = FresnelLayout(**a.layout)
    out = {}
    for depth in a.depths:
        for z in a.z:
            p = physics(z, a.margin, a.reach[0], depth, a.s[0])
            cam = camera(CAMERA_SEED, p, lay)
            for i in IDS:
                sc = scene(i, p, lay)
                sc['sensor_dust'] = cam['dust']
                ses = session(SEED * 1000 + i // 100, p)
                out[f'{depth}|{z}|{i}|img'] = recording(sc, ses, p, cam, dev)[0].numpy()
                out[f'{depth}|{z}|{i}|blank'] = recording(sc, ses, p, cam, dev, sample=False)[0].numpy()
    np.savez(a.out, **out)


def compare(a):
    A, B = np.load(a.dumps[0]), np.load(a.dumps[1])
    rows = []
    for k in sorted(B.files):
        if not k.endswith('|img'):
            continue
        depth, z, i, _ = k.split('|')
        d, pat = A[k] - B[k], B[k] - B[k.replace('|img', '|blank')]
        rows.append(dict(depth=depth, z_mm=float(z), image_id=int(i), rel_rms=float(d.std() / pat.std()),
                         max_abs_dn=float(np.abs(d).max()),
                         blank_rel=float((A[k.replace('|img', '|blank')] - B[k.replace('|img', '|blank')]).std()
                                         / pat.std())))
    t = pd.DataFrame(rows)
    t.to_csv(a.out, index=False, float_format='%.6g')
    print(t.to_string())
    print(t.groupby(['depth', 'z_mm']).agg(rel_min=('rel_rms', 'min'), rel_med=('rel_rms', 'median'),
                                           rel_max=('rel_rms', 'max'), dn_max=('max_abs_dn', 'max')).to_string())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('what', choices=['converge', 'reach', 'margin', 'dump', 'compare'])
    ap.add_argument('dumps', nargs='*', help='compare: two npz written by dump (A B)')
    ap.add_argument('--out', help='dump: npz; compare: csv')
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--z', type=float, nargs='+', default=[1.0, 0.7], help='mm')
    ap.add_argument('--depths', nargs='+', default=list(DEPTHS), choices=list(DEPTHS))
    ap.add_argument('--s', type=int, nargs='+', default=[1, 2, 4, 8],
                    help='converge: the factors compared in pairs; reach, margin: the factor they are measured at')
    ap.add_argument('--margin', type=int, default=394, help='converge: the margin of the set')
    ap.add_argument('--margin-list', type=int, nargs='+', default=[128, 197, 256, 394], help='margin: candidates m')
    ap.add_argument('--margin-reach', type=int, default=0, help='reach: margin of the field (default 2R + 256)')
    ap.add_argument('--layout', nargs='*', default=[], help='converge: parameters of FresnelLayout, key=value')
    ap.add_argument('--tag', default='', help='converge: suffix of the csv names')
    ap.add_argument('--n-scenes', type=int, default=len(IDS), choices=[1, 2, 4, 8],
                    help='converge: that many of the 8 scenes, evenly spaced (default all 8)')
    ap.add_argument('--reach', type=int, nargs='+', default=[233],
                    help='converge, margin: the reach of the set; reach: the candidates R')
    a = ap.parse_args()
    a.layout = {k: float(v) for k, v in (x.split('=', 1) for x in a.layout)}
    torch.set_num_threads(4)
    if a.what == 'compare':
        return compare(a)
    dev = pick_device(a.device)
    if a.what == 'dump':
        return dump(a, dev)
    if a.what == 'converge':
        a.reach = a.reach[0]
        converge(a, dev)
    else:
        {'reach': reach, 'margin': margin}[a.what](a, dev)


if __name__ == '__main__':
    main()
