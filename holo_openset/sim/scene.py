"""Scenes: letters on a field larger than the sensor, dust on the glass around them, and the fixed defects of the
camera. Everything is drawn from a seeded generator, so a scene can be rebuilt exactly to record it again with other
physics (the robustness sets are the test scenes recorded again with one effect changed)."""
import math
import random

import numpy as np
import torch
from PIL import Image, ImageDraw

from holo_openset.sim.letters import CLASS_TO_IDX, CLASSES, FONTS, clipped_normal_int, letter_mask, letter_master
from holo_openset.sim.physics import PIXEL, Z0, sample_mask

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


class FresnelLayout(Layout):
    """The letters of Layout at another distance with the same Fresnel number: every length times `scale`
    (sqrt(z / 19.25 mm): 0.22792 for 1.0 mm), so font sizes 15.95-26.89 px drawn from a continuous uniform (boxes of
    about 13-23.5 px, 22-39 um), border and spacing scaled. The scene is defined in physical units: the font size,
    rotation and position of each letter (to 1/factor of a pixel, never snapped to the pixels) and the raster of every
    object (letters, dust) on a master grid `factor` times finer than the pixel, which the simulator averages onto the
    grid it records on (physics.sample_mask), so that the same scene is recorded at every oversampling.
    The number of letters per 640 x 640 window keeps the values of Layout unless given (an open question of the
    pilot). An instance carries its parameters: FresnelLayout(letters_mean=...).
    fill_mean > 0 (default 0, off): un-annotated filler letters bring the mean number of letters per 640 x 640 window,
    inside the window and in the band around it, to fill_mean (`fill_letters`); the rest of the scene does not move."""
    physical = True
    factor = 16                         # the master grid: 1/16 of a pixel (0.10 um)
    scale = math.sqrt(1.0e-3 / Z0)      # 0.22792: the lengths of Layout for a sample at 1.0 mm
    fill_mean = 0.0                     # letters per 640 x 640 window with the fillers (0: no fillers)
    PARAMS = ('scale', 'factor', 'letters_mean', 'letters_std', 'letters_min', 'letters_max', 'unique_fraction_mean',
              'unique_std', 'rotation', 'max_attempts_per_letter', 'fill_mean')

    def __init__(self, **kw):
        for k, v in kw.items():
            if k not in self.PARAMS:
                raise ValueError(f'{k} is not a parameter of {type(self).__name__} ({", ".join(self.PARAMS)})')
            setattr(self, k, type(getattr(type(self), k))(v))

    font_min = property(lambda self: Layout.font_min * self.scale)
    font_max = property(lambda self: Layout.font_max * self.scale)
    border = property(lambda self: Layout.border * self.scale)
    margin = property(lambda self: Layout.margin * self.scale)

    def params(self):
        """What physics.json keeps: the parameters, and the lengths they give (for the record). fill_mean only when
        on, so that a set recorded before it existed keeps its physics.json byte for byte."""
        return {**{k: getattr(self, k) for k in self.PARAMS if k != 'fill_mean' or self.fill_mean > 0},
                **{k: getattr(self, k) for k in ('font_min', 'font_max', 'border', 'margin')}}


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
    """Absorption, phase and depth of an object: three normal draws, in this order. The depth is the clipped normal
    of depth_std / depth_max, or, with phys.depth_uniform > 0, the same normal draw g mapped to a uniform law on
    +-depth_uniform by erf(g / sqrt(2)) (= 2 Phi(g) - 1): the draws of the scene do not move."""
    a = clipped_normal(rng, phys.absorption_mean, phys.absorption_std, phys.absorption_min, 1.0)
    p = clipped_normal(rng, phys.phase_mean, phys.phase_std, 0.0, phys.phase_max)
    if getattr(phys, 'depth_uniform', 0.0) > 0:
        d = phys.depth_uniform * math.erf(rng.gauss(0.0, 1.0) / math.sqrt(2))
    else:
        d = clipped_normal(rng, 0.0, phys.depth_std, -phys.depth_max, phys.depth_max)
    return dict(absorption=a, phase=p, depth=d)


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
    the window are drawn from outside_classes (default: all), in the same fonts. A physical layout (FresnelLayout)
    draws the scene in physical units (`physical_scene`)."""
    if getattr(lay, 'physical', False):
        return physical_scene(seed, phys, classes, fonts, lay, outside_classes)
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


# ------------------------------------------------------------------------------- scenes in physical units
# Canvas coordinates of edges: pixel j covers [j, j + 1), master cell k covers [k / f, (k + 1) / f) (f = lay.factor).
# Every object keeps its master raster (uint8, cropped to the ink) and the master cell of its top-left corner, plus
# `mask`, `x`, `y`: its area mean over the pixels and the first pixel it touches (what the native path, the depth of a
# tilted slide, the ground-truth maps and the dust table read).

def physical_object(master, mx, my, f, **kw):
    o = dict(master=master, mx=int(mx), my=int(my), factor=f, **kw)
    o['mask'], o['x'], o['y'] = sample_mask(o, 1)
    return o


def dust_master(rng, f):
    """`dust_mask` drawn on the master grid (f times finer than the pixel): the same draws, the polygon filled at f x
    the pixel, cropped to the ink."""
    a = min(25.0, max(1.0, math.exp(rng.gauss(math.log(3.0), 0.6))))
    b = a * rng.uniform(0.5, 1.0)
    size = int(math.ceil((2 * a + 6) * f))
    im = Image.new('L', (size, size), 0)
    pts = []
    rot = rng.uniform(0, math.pi)
    for k in range(24):
        t = 2 * math.pi * k / 24
        r = 1 + 0.15 * rng.uniform(-1, 1)
        x, y = a * r * math.cos(t), b * r * math.sin(t)
        pts.append((size / 2 + (x * math.cos(rot) - y * math.sin(rot)) * f,
                    size / 2 + (x * math.sin(rot) + y * math.cos(rot)) * f))
    ImageDraw.Draw(im).polygon(pts, fill=255)
    return np.asarray(im.crop(im.getbbox()), np.uint8)


def make_physical_dust(rng, n, region, depth, f):
    """`make_dust` in physical units: each particle anywhere in the region, to 1/f of a pixel."""
    x0, y0, x1, y1 = region
    out = []
    for _ in range(n):
        m = dust_master(rng, f)
        u, v = rng.uniform(x0, x1 - m.shape[1] / f), rng.uniform(y0, y1 - m.shape[0] / f)
        out.append(physical_object(m, round(u * f), round(v * f), f, absorption=rng.uniform(0.3, 1.0),
                                   phase=rng.uniform(0.0, 1.5), depth=depth, kind='dust'))
    return out


def physical_scene(seed, phys, classes=CLASSES, fonts=FONTS, lay=None, outside_classes=None):
    """`make_scene` for a physical layout: the same steps (letters in the window, the same density around it, dust on
    the two glass surfaces), with continuous font sizes and positions. The scene depends on the window, margin, reach,
    material and dust of `phys`, never on the distance or on the oversampling. The annotation keeps the integer box
    of the pixels the letter touches (x0, y0, x1, y1, what the pipeline reads) and the box of its ink in pixels
    (bx0, by0, bx1, by1, floats)."""
    lay = lay or FresnelLayout()
    f = lay.factor
    rng = random.Random(seed)
    H, W = phys.canvas
    h, w = phys.window
    m0 = phys.margin
    lo_y, hi_y = max(0, m0 - phys.reach), min(H, m0 + h + phys.reach)
    lo_x, hi_x = max(0, m0 - phys.reach), min(W, m0 + w + phys.reach)
    g = max(1, round(lay.margin))   # spacing between the boxes of two letters (px of the occupancy grid)
    occ = np.zeros((H, W), bool)
    objects, rows = [], []

    def draw(letter):
        size, font = rng.uniform(lay.font_min, lay.font_max), rng.choice(fonts)
        angle = rng.uniform(-lay.rotation, lay.rotation)
        return letter_master(letter, font, size * f, angle), size, font, angle

    def box(o):
        mh, mw = o['mask'].shape
        return o['x'], o['y'], o['x'] + mw, o['y'] + mh

    for det_idx, letter in enumerate(letter_list(rng, classes, h * w / TILE, lay)):
        for _ in range(lay.max_attempts_per_letter):
            master, size, font, angle = draw(letter)
            fh, fw = master.shape[0] / f, master.shape[1] / f
            u = m0 + rng.uniform(lay.border, w - fw - lay.border)
            v = m0 + rng.uniform(lay.border, h - fh - lay.border)
            o = physical_object(master, round(u * f), round(v * f), f, kind='letter', classe=letter)
            x0, y0, x1, y1 = box(o)
            if occ[y0 - g:y1 + g, x0 - g:x1 + g].any():
                continue
            occ[y0 - g:y1 + g, x0 - g:x1 + g] = True
            mat = material(rng, phys)
            o.update(mat)
            objects.append(o)
            rows.append(dict(det_idx=det_idx, classe=letter, class_id=CLASS_TO_IDX[letter], x0=x0 - m0, y0=y0 - m0,
                             x1=x1 - m0, y1=y1 - m0, font_size=size, font_name=font.stem, rotation=angle,
                             absorption=mat['absorption'], phase=mat['phase'], depth=mat['depth'],
                             bx0=o['mx'] / f - m0, by0=o['my'] / f - m0, bx1=(o['mx'] + master.shape[1]) / f - m0,
                             by1=(o['my'] + master.shape[0]) / f - m0))
            break
        else:
            return None
    if phys.reach > 0:
        density = lay.letters_mean / TILE
        target = poisson(rng, density * ((hi_y - lo_y) * (hi_x - lo_x) - h * w))
        placed = 0
        for _ in range(target * 20):
            if placed == target:
                break
            letter = rng.choice(sorted(outside_classes or CLASSES))
            master, size, font, angle = draw(letter)
            fh, fw = master.shape[0] / f, master.shape[1] / f
            u, v = rng.uniform(lo_x, hi_x - fw), rng.uniform(lo_y, hi_y - fh)
            o = physical_object(master, round(u * f), round(v * f), f, kind='outside', classe=letter)
            x0, y0, x1, y1 = box(o)
            if x1 + g > m0 and x0 - g < m0 + w and y1 + g > m0 and y0 - g < m0 + h:
                continue
            if occ[max(0, y0 - g):y1 + g, max(0, x0 - g):x1 + g].any():
                continue
            occ[max(0, y0 - g):y1 + g, max(0, x0 - g):x1 + g] = True
            o.update(material(rng, phys))
            objects.append(o)
            placed += 1
    fill = None
    if getattr(lay, 'fill_mean', 0) > 0:   # its own generator: nothing above or below moves
        fillers, fill = fill_letters(seed, phys, lay, occ, len(rows), sum(o['kind'] == 'outside' for o in objects),
                                     fonts, outside_classes)
        objects += fillers
    dust = []
    area_mm2 = (hi_y - lo_y) * (hi_x - lo_x) * (PIXEL * 1e3) ** 2
    for depth in phys.dust_depths:
        dust += make_physical_dust(rng, poisson(rng, phys.dust_density * area_mm2), (lo_x, lo_y, hi_x, hi_y), depth, f)
    out = dict(objects=objects, dust=dust, rows=rows, margin=m0, seed=seed)
    if fill is not None:
        out['fill'] = fill
    return out


FILL_SEED = 900_000_000   # the generator of the fillers of a scene: random.Random(scene seed + FILL_SEED)


def fill_letters(seed, phys, lay, occ, n_window, n_band, fonts=FONTS, classes=None):
    """Un-annotated filler letters (kind 'filler': never in the annotations, the ground-truth maps or the YOLO labels,
    like the letters around the window) that bring the mean number of letters per 640 x 640 window to lay.fill_mean,
    counting the letters the scene already has: in the window, Poisson(fill_mean x window / TILE) minus its
    n_window annotated letters; in the band of the reach around it, Poisson(fill_mean x band area / TILE) minus its
    n_band letters (never below 0). Each filler as the letters of the scene (class from `classes`, default all, font,
    continuous size, rotation, material and depth with the same laws), placed uniformly where those letters go (in the
    window with its border; in the band without touching the window), never overlapping another letter (the spacing
    of the layout, on the occupancy grid `occ`, which is updated). Drawn by a generator of its own seeded from the
    scene seed, so that the letters, the dust and every other draw of the scene stay as they are. A filler that finds
    no place in max_attempts_per_letter positions is skipped (counted in the returned dict).
    -> (objects, dict(target_window, target_band, placed_window, placed_band))"""
    frng = random.Random(seed + FILL_SEED)
    f = lay.factor
    H, W = phys.canvas
    h, w = phys.window
    m0 = phys.margin
    lo_y, hi_y = max(0, m0 - phys.reach), min(H, m0 + h + phys.reach)
    lo_x, hi_x = max(0, m0 - phys.reach), min(W, m0 + w + phys.reach)
    g = max(1, round(lay.margin))
    density = lay.fill_mean / TILE
    want = dict(window=max(0, poisson(frng, density * h * w) - n_window),
                band=max(0, poisson(frng, density * ((hi_y - lo_y) * (hi_x - lo_x) - h * w)) - n_band)
                if phys.reach > 0 else 0)
    out, placed = [], dict(window=0, band=0)
    for where in ('window', 'band'):
        for _ in range(want[where]):
            letter = frng.choice(sorted(classes or CLASSES))
            size, font = frng.uniform(lay.font_min, lay.font_max), frng.choice(fonts)
            angle = frng.uniform(-lay.rotation, lay.rotation)
            master = letter_master(letter, font, size * f, angle)
            fh, fw = master.shape[0] / f, master.shape[1] / f
            for _ in range(lay.max_attempts_per_letter):
                if where == 'window':
                    u = m0 + frng.uniform(lay.border, w - fw - lay.border)
                    v = m0 + frng.uniform(lay.border, h - fh - lay.border)
                else:
                    u, v = frng.uniform(lo_x, hi_x - fw), frng.uniform(lo_y, hi_y - fh)
                mx, my = round(u * f), round(v * f)
                # the pixels it touches (the box of sample_mask at s = 1), without sampling it
                x0, y0 = mx // f, my // f
                x1, y1 = x0 - (-(mx % f + master.shape[1]) // f), y0 - (-(my % f + master.shape[0]) // f)
                if where == 'band' and x1 + g > m0 and x0 - g < m0 + w and y1 + g > m0 and y0 - g < m0 + h:
                    continue
                if occ[max(0, y0 - g):y1 + g, max(0, x0 - g):x1 + g].any():
                    continue
                occ[max(0, y0 - g):y1 + g, max(0, x0 - g):x1 + g] = True
                o = physical_object(master, mx, my, f, kind='filler', classe=letter)
                o.update(material(frng, phys))
                out.append(o)
                placed[where] += 1
                break
    return out, dict(target_window=want['window'], target_band=want['band'], placed_window=placed['window'],
                     placed_band=placed['band'])


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


def camera(seed, phys, lay=Layout):
    """Defects fixed for the camera: photo-response non-uniformity and dust on the sensor window (in physical units
    with a physical layout)."""
    rng = random.Random(seed)
    g = torch.Generator().manual_seed(seed)
    h, w = phys.window
    m0, pad = phys.margin, min(64, phys.margin)
    n = poisson(rng, phys.sensor_dust_density * h * w * (PIXEL * 1e3) ** 2)
    region = (m0 - pad, m0 - pad, m0 + w + pad, m0 + h + pad)
    dust = make_physical_dust(rng, n, region, 0.0, lay.factor) if getattr(lay, 'physical', False) else \
        make_dust(rng, n, region, 0.0)
    return dict(prnu=torch.randn(h, w, generator=g, dtype=torch.float64), dust=dust)


def session(seed, phys):
    rng = random.Random(seed)
    return dict(z=phys.z0 * (1 + phys.session_z_std * rng.gauss(0.0, 1.0)),
                beam_waist=rng.uniform(*phys.beam_waist), beam_dx=phys.beam_offset_std * rng.gauss(0.0, 1.0),
                beam_dy=phys.beam_offset_std * rng.gauss(0.0, 1.0))
