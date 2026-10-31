"""Scenes: letters on a field larger than the sensor, dust on the glass around them, and the fixed defects of the
camera. Everything is drawn from a seeded generator, so a scene can be rebuilt exactly to record it again with other
physics (the robustness sets are the test scenes recorded again with one effect changed)."""
import math
import random

import numpy as np
import torch
from PIL import Image, ImageDraw

from holo_openset.sim.letters import CLASS_TO_IDX, CLASSES, FONTS, clipped_normal_int, letter_mask
from holo_openset.sim.physics import PIXEL

TILE = 640 * 640  # the letter density is set per 640 x 640 window


class Layout:
    """Letters inside the window: 3-18 per 640 x 640 window (mean 8), ~72 % distinct, font sizes 70-118 px (boxes of
    ~45-125 px, 75-210 um), rotations within +-35 degrees, never overlapping."""
    letters_mean, letters_std, letters_min, letters_max = 8.0, 3.0, 3, 18
    unique_fraction_mean, unique_std = 0.72, 2.0
    font_min, font_max = 70, 118
    rotation = 35.0
    border, margin = 12, 6
    max_attempts_per_letter = 500


class SmallLayout(Layout):
    """Letters of 12-36 px (20-60 um): the scale of planar microstructures, for the analysis of object size."""
    font_min, font_max = 16, 48
    border, margin = 6, 4


def clipped_normal(rng, mean, std, lo, hi):
    # always one draw, so that a variant with std = 0 keeps the rest of the scene identical
    return min(hi, max(lo, mean + std * rng.gauss(0.0, 1.0)))


def letter_list(rng, classes, area_tiles, lay=Layout):
    """How many letters, and which, in a window of `area_tiles` 640 x 640 windows."""
    r = area_tiles
    n = clipped_normal_int(rng, lay.letters_mean * r, lay.letters_std * math.sqrt(r), max(1, round(lay.letters_min * r)),
                           round(lay.letters_max * r))
    max_unique = min(n, len(classes))
    n_unique = clipped_normal_int(rng, min(max_unique, max(1, lay.unique_fraction_mean * n)), lay.unique_std, 1,
                                  max_unique)
    chosen = rng.sample(sorted(classes), n_unique)
    letters = chosen + [rng.choice(chosen) for _ in range(n - n_unique)]
    rng.shuffle(letters)
    return letters


def material(rng, phys):
    return dict(absorption=clipped_normal(rng, phys.absorption_mean, phys.absorption_std, phys.absorption_min, 1.0),
                phase=clipped_normal(rng, phys.phase_mean, phys.phase_std, 0.0, phys.phase_max),
                depth=clipped_normal(rng, 0.0, phys.depth_std, -phys.depth_max, phys.depth_max))


def dust_mask(rng):
    """An irregular particle, a few micrometres to a few tens: an ellipse with a rough edge, antialiased."""
    a = min(25.0, max(1.0, math.exp(rng.gauss(math.log(3.0), 0.6))))
    b = a * rng.uniform(0.5, 1.0)
    s = 4
    size = int(2 * a + 6)
    im = Image.new('L', (size * s, size * s), 0)
    pts = []
    rot = rng.uniform(0, math.pi)
    for k in range(24):
        t = 2 * math.pi * k / 24
        r = 1 + 0.15 * rng.uniform(-1, 1)
        x, y = a * r * math.cos(t), b * r * math.sin(t)
        pts.append(((size / 2 + x * math.cos(rot) - y * math.sin(rot)) * s,
                    (size / 2 + x * math.sin(rot) + y * math.cos(rot)) * s))
    ImageDraw.Draw(im).polygon(pts, fill=255)
    return np.asarray(im.resize((size, size), Image.Resampling.BOX), dtype=np.float32) / 255


def make_dust(rng, n, region, depth):
    x0, y0, x1, y1 = region
    out = []
    for _ in range(n):
        m = dust_mask(rng)
        out.append(dict(mask=m, x=rng.randint(x0, x1 - m.shape[1]), y=rng.randint(y0, y1 - m.shape[0]),
                        absorption=rng.uniform(0.3, 1.0), phase=rng.uniform(0.0, 1.5), depth=depth, kind='dust'))
    return out


def poisson(rng, lam):
    """Poisson draw from a random.Random (Knuth for small means, normal approximation above)."""
    if lam <= 0:
        return 0
    if lam > 50:
        return max(0, int(round(rng.gauss(lam, math.sqrt(lam)))))
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def _draw_letter(rng, letter, fonts, lay):
    size, font, angle = rng.randint(lay.font_min, lay.font_max), rng.choice(fonts), rng.uniform(-lay.rotation,
                                                                                                 lay.rotation)
    return letter_mask(letter, font, size, angle), size, font, angle


def make_scene(seed, phys, classes=CLASSES, fonts=FONTS, lay=Layout, outside_classes=None):
    """-> dict(objects=[letters in and around the window], dust=[...], rows=[annotations, window coordinates]) or
    None when the letters do not fit. Canvas coordinates; the window starts at (margin, margin). The letters around
    the window are drawn from outside_classes (default: all), in the same fonts."""
    rng = random.Random(seed)
    H, W = phys.canvas
    h, w = phys.window
    m0 = phys.margin
    lo_y, hi_y = max(0, m0 - phys.reach), min(H, m0 + h + phys.reach)
    lo_x, hi_x = max(0, m0 - phys.reach), min(W, m0 + w + phys.reach)
    occ = np.zeros((H, W), bool)
    objects, rows = [], []
    for det_idx, letter in enumerate(letter_list(rng, classes, h * w / TILE, lay)):
        for _ in range(lay.max_attempts_per_letter):
            mask, size, font, angle = _draw_letter(rng, letter, fonts, lay)
            mw, mh = mask.size
            x = m0 + rng.randint(lay.border, w - mw - lay.border)
            y = m0 + rng.randint(lay.border, h - mh - lay.border)
            if occ[y - lay.margin:y + mh + lay.margin, x - lay.margin:x + mw + lay.margin].any():
                continue
            occ[y - lay.margin:y + mh + lay.margin, x - lay.margin:x + mw + lay.margin] = True
            mat = material(rng, phys)
            objects.append(dict(mask=np.asarray(mask, np.float32) / 255, x=x, y=y, kind='letter', classe=letter, **mat))
            rows.append(dict(det_idx=det_idx, classe=letter, class_id=CLASS_TO_IDX[letter], x0=x - m0, y0=y - m0,
                             x1=x - m0 + mw, y1=y - m0 + mh, font_size=size, font_name=font.stem, rotation=angle,
                             absorption=mat['absorption'], phase=mat['phase'], depth=mat['depth']))
            break
        else:
            return None
    # the same density of letters around the sensor, never annotated and never overlapping the window
    if phys.reach > 0:
        density = lay.letters_mean / TILE
        target = poisson(rng, density * ((hi_y - lo_y) * (hi_x - lo_x) - h * w))
        placed = 0
        for _ in range(target * 20):
            if placed == target:
                break
            letter = rng.choice(sorted(outside_classes or CLASSES))
            mask, size, font, angle = _draw_letter(rng, letter, fonts, lay)
            mw, mh = mask.size
            x, y = rng.randint(lo_x, hi_x - mw), rng.randint(lo_y, hi_y - mh)
            m = lay.margin
            if x + mw + m > m0 and x - m < m0 + w and y + mh + m > m0 and y - m < m0 + h:
                continue
            if occ[max(0, y - m):y + mh + m, max(0, x - m):x + mw + m].any():
                continue
            occ[max(0, y - m):y + mh + m, max(0, x - m):x + mw + m] = True
            objects.append(dict(mask=np.asarray(mask, np.float32) / 255, x=x, y=y, kind='outside', classe=letter,
                                **material(rng, phys)))
            placed += 1
    dust = []
    area_mm2 = (hi_y - lo_y) * (hi_x - lo_x) * (PIXEL * 1e3) ** 2
    for depth in phys.dust_depths:
        dust += make_dust(rng, poisson(rng, phys.dust_density * area_mm2), (lo_x, lo_y, hi_x, hi_y), depth)
    return dict(objects=objects, dust=dust, rows=rows, margin=m0, seed=seed)


def object_maps(scene, phys):
    """Amplitude and phase of the letters inside the window, in their own plane (the ground truth of a
    reconstruction)."""
    amp = np.ones(phys.window, np.float32)
    ph = np.zeros(phys.window, np.float32)
    m0 = scene['margin']
    for o in scene['objects']:
        if o['kind'] != 'letter':
            continue
        m = o['mask']
        h, w = m.shape
        y, x = o['y'] - m0, o['x'] - m0
        amp[y:y + h, x:x + w] *= 1 - o['absorption'] * m
        ph[y:y + h, x:x + w] += o['phase'] * m
    return amp, ph


def camera(seed, phys):
    """Defects fixed for the camera: photo-response non-uniformity and dust on the sensor window."""
    rng = random.Random(seed)
    g = torch.Generator().manual_seed(seed)
    h, w = phys.window
    m0, pad = phys.margin, min(64, phys.margin)
    n = poisson(rng, phys.sensor_dust_density * h * w * (PIXEL * 1e3) ** 2)
    dust = make_dust(rng, n, (m0 - pad, m0 - pad, m0 + w + pad, m0 + h + pad), 0.0)
    return dict(prnu=torch.randn(h, w, generator=g, dtype=torch.float64), dust=dust)


def session(seed, phys):
    rng = random.Random(seed)
    return dict(z=phys.z0 * (1 + phys.session_z_std * rng.gauss(0.0, 1.0)),
                beam_waist=rng.uniform(*phys.beam_waist), beam_dx=phys.beam_offset_std * rng.gauss(0.0, 1.0),
                beam_dy=phys.beam_offset_std * rng.gauss(0.0, 1.0))
