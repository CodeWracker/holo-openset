"""Figures of the paper (PDF + PNG in ../latex-openset-microscopy/figures/paper).

    python -m holo_openset paper figures            # all
    python -c "from holo_openset.paper.figures import fig_fresnel; fig_fresnel()"
"""
import json
import math
import os

import numpy as np
import pandas as pd
import torch
from PIL import Image

from holo_openset import paths
from holo_openset.paper.style import (COLORS, INK, KNOWN, LABELS, MUTED, ORDER, SHORT, UNKNOWN, panel, plt, save,
                                      setup, show)
from holo_openset.reconstruct import (COARSE, N_FINE, Holograms, backprop, channels, kernel, normalise, per_object,
                                      remove_twin, scan)
from holo_openset.sim.letters import FONTS, letter_mask
from holo_openset.sim.physics import IDEAL, PIXEL, WAVELENGTH, Z0, Physics, freq_sq, record, sensor_intensity
from holo_openset.sim.scene import camera, make_scene, session

DEV = torch.device(os.environ.get('HOLO_PAPER_DEVICE', 'cpu'))
BASE = paths.dataset(paths.BASE)
setup()


def _test_image(min_letters=8, k=0):
    meta = pd.read_csv(BASE / 'metadata.csv')
    t = meta[(meta.split == 'test') & (meta.n_letters >= min_letters)]
    return int(t.image_id.iloc[k])


def _single(letter_obj, phys, z=Z0):
    """Intensity hologram of a single object at the centre of the window (no dust, no noise)."""
    h, w = phys.window
    m = letter_obj['mask']
    o = dict(letter_obj, x=phys.margin + (w - m.shape[1]) // 2, y=phys.margin + (h - m.shape[0]) // 2, depth=0.0,
             kind='letter')
    return sensor_intensity(dict(objects=[o], dust=[], sensor_dust=[]), dict(z=z), phys, DEV).cpu().numpy()


def _note(key, value):
    """Numbers measured while drawing a figure, for the text (results/holo_openset/figure_numbers.json)."""
    f = paths.RESULTS / 'figure_numbers.json'
    d = json.load(open(f)) if f.exists() else {}
    d[key] = value
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    json.dump(d, open(f, 'w'), indent=1)


# ------------------------------------------------------------------------------------------------ formation
def fig_setup(frame=0, window=(1060, 1640)):
    """The bench (top left), what it records: a full frame of the sensor and a 640x640 window of it (top right), and
    the two routes from the recording to the decision (bottom). Blue: fixed by the equipment; orange: depends on the
    sample and changes between acquisitions."""
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
    EQ, SA = KNOWN, UNKNOWN
    fig = plt.figure(figsize=(7.16, 4.5))
    ax = fig.add_axes([0, 0.47, 0.70, 0.53])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 46)
    ax.axis('off')
    fs = 6.2

    def dist(x0, x1, y, label, color):
        ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle='<->', mutation_scale=6, lw=0.6, color=color))
        ax.text((x0 + x1) / 2, y - 1.0, label, ha='center', va='top', fontsize=fs, color=color)
    # light: from the pinhole, through the sample, to the sensor
    ax.add_patch(Polygon([[12, 22.6], [12, 23.4], [76, 39], [76, 7]], closed=True, fc='#eef4fc', ec='none', zorder=0))
    # source and pinhole
    ax.add_patch(FancyBboxPatch((1.2, 19.5), 6.5, 7, boxstyle='round,pad=0.3', fc='white', ec=MUTED, lw=0.7))
    ax.text(4.45, 23, 'LED', ha='center', va='center', fontsize=6.5)
    ax.text(4.45, 17.2, '$\\lambda$ = 385 nm\n10 nm band', ha='center', va='top', fontsize=fs, color=EQ,
            linespacing=1.2)
    ax.add_patch(Rectangle((11.7, 17.5), 0.6, 4.9, fc=MUTED, ec='none'))
    ax.add_patch(Rectangle((11.7, 23.6), 0.6, 4.9, fc=MUTED, ec='none'))
    ax.text(12, 30.2, 'pinhole\n$D$ = 100 µm', ha='center', va='bottom', fontsize=fs, color=EQ, linespacing=1.2)
    # sample: slide, sample layer, coverslip
    ax.add_patch(Rectangle((30, 7), 3.0, 32, fc='#dcdcd6', ec=MUTED, lw=0.5))
    ax.add_patch(Rectangle((33, 7), 2.4, 32, fc='#f7f3ea', ec=MUTED, lw=0.4))
    ax.add_patch(Rectangle((35.4, 7), 0.9, 32, fc='#dcdcd6', ec=MUTED, lw=0.5))
    rng = np.random.RandomState(3)
    for y, c in zip([11, 16.8, 22.6, 28.4, 34.2], 'AKRSE'):
        ax.text(34.2 + rng.uniform(-0.5, 0.5), y, c, ha='center', va='center', fontsize=7, color=INK,
                alpha=rng.uniform(0.35, 1.0), fontweight='bold')
    for y in [9.5, 20, 31.5]:
        ax.add_patch(plt.Circle((29.7, y), 0.4, color=MUTED))
    for y in [14, 26]:
        ax.add_patch(plt.Circle((36.6, y), 0.35, color=MUTED))
    ax.text(31.5, 40.2, 'slide', ha='center', va='bottom', fontsize=fs)
    ax.text(36.0, 40.2, 'coverslip', ha='left', va='bottom', fontsize=fs)
    ax.text(38.2, 34.5, 'letters: absorption $a$, phase $\\varphi$,\neach at its own depth $z+\\delta$',
            ha='left', va='center', fontsize=fs, color=SA, linespacing=1.25)
    ax.text(38.2, 11.5, 'dust on both glass surfaces', ha='left', va='center', fontsize=fs, color=SA)
    ax.text(56, 23, 'each object scatters light\nthat interferes with the\nunscattered wave', ha='center',
            va='center', fontsize=fs, color=MUTED, style='italic', linespacing=1.25)
    # sensor: window and pixels
    ax.add_patch(Rectangle((76, 6), 1.0, 34, fc='#dcdcd6', ec=MUTED, lw=0.5))
    ax.add_patch(Rectangle((77.5, 6), 1.8, 34, fc=MUTED, ec='none'))
    for y in np.arange(6.4, 40, 1.25):
        ax.plot([77.5, 79.3], [y, y], color='white', lw=0.3)
    ax.add_patch(plt.Circle((76.5, 19), 0.3, color='white', ec=MUTED, lw=0.4))
    ax.text(77.6, 41, 'sensor', ha='center', va='bottom', fontsize=6.5)
    ax.text(80.8, 36, 'pixel $\\Delta$ = 1.67 µm\n3840 × 2748 px\n(6.4 × 4.6 mm)', ha='left', va='top',
            fontsize=fs, color=EQ, linespacing=1.25)
    ax.text(80.8, 24, 'records intensity;\nshot and read noise,\n8 bits; dust on\nits window', ha='left',
            va='top', fontsize=fs, color=INK, linespacing=1.25)
    # distances (not to scale: L is eight times z)
    dist(12, 30, 3.6, '$L$ = 15 cm', EQ)
    ax.plot([19.8, 20.8], [2.6, 4.6], color=EQ, lw=0.7)
    ax.plot([21.2, 22.2], [2.6, 4.6], color=EQ, lw=0.7)
    dist(34.2, 77.5, 3.6, '$z \\approx 19.25$ mm, changes with every mount', SA)
    ax.text(1, 44.5, 'not to scale', ha='left', va='top', fontsize=5.6, color=MUTED, style='italic')

    # what it records: a full frame and a 640 x 640 window of it
    src = Holograms(paths.dataset('full_frames'))
    img = np.asarray(src.holo[src.row[frame]], np.float32)
    y0, x0 = window
    fa = fig.add_axes([0.705, 0.585, 0.185, 0.36])
    show(fa, img[::4, ::4], vmin=None)
    fa.add_patch(Rectangle((x0 / 4, y0 / 4), 160, 160, fill=False, ec=SA, lw=0.9))
    fa.set_title('hologram $I$: full frame\n29.4 mm$^2$', loc='center', fontsize=6.2, pad=2, linespacing=1.15)
    wa = fig.add_axes([0.9, 0.585, 0.098, 0.36])
    show(wa, img[y0:y0 + 640, x0:x0 + 640])
    for s in wa.spines.values():
        s.set_visible(True)
        s.set_color(SA)
        s.set_linewidth(0.9)
    wa.set_title('a 640$^2$ window\n1.07 × 1.07 mm', loc='center', fontsize=6.2, pad=2, linespacing=1.15)
    fig.text(0.85, 0.615, 'and a blank frame $B$ (no sample) per session', ha='center', va='center', fontsize=fs,
             color=INK)

    # the two routes; the localiser runs on the hologram for both
    bx = fig.add_axes([0, 0, 1, 0.47])
    bx.set_xlim(0, 100)
    bx.set_ylim(0, 38)
    bx.axis('off')
    hb = 7.0

    def box(x, y, w, text, color=MUTED, fc='white', lw=0.7):
        bx.add_patch(FancyBboxPatch((x, y - hb / 2), w, hb, boxstyle='round,pad=0.3', fc=fc, ec=color, lw=lw))
        bx.text(x + w / 2, y, text, ha='center', va='center', fontsize=5.9, linespacing=1.2)

    def arrow(p0, p1):
        bx.add_patch(FancyArrowPatch(p0, p1, arrowstyle='->', mutation_scale=7, lw=0.6, color=MUTED,
                                     shrinkA=0, shrinkB=0))
    yc, yd, yp = 29, 17.5, 6
    final = 'ResNet18 embedding\n→ gallery: known class\nor "unknown"'
    conv = [(1, 12, 'hologram $I$ and\nblank frame $B$:\n$\\sqrt{I/B}$', MUTED),
            (16, 14.5, 'autofocus: reconstruct\nat 114 candidate $z$,\nkeep the sharpest', SA),
            (34, 13, 'back-propagate to $z$\n(needs $\\lambda$, $\\Delta$):\n1 FFT pair', MUTED),
            (50.5, 13, 'twin-image removal\n(optional): 2 FFT\npairs per pass', MUTED),
            (67, 13, 'per-object focus\nin each box;\ncrop the box', MUTED),
            (84, 15, final, MUTED)]
    prop = [(1, 12, 'hologram $I$\n(as recorded)', MUTED),
            (16, 47.5, 'learned Fourier layer on the whole $I$: one weight per spatial-frequency radius,\n'
                       'learned from class labels; 1 FFT pair; no $\\lambda$, $z$, $\\Delta$ or blank frame', INK),
            (67, 13, 'crop each box', MUTED),
            (84, 15, final, MUTED)]
    for y, steps in [(yc, conv), (yp, prop)]:
        for k, (x, w, t, c) in enumerate(steps):
            box(x, y, w, t, color=c, lw=1.1 if c == INK else 0.7)
            if k:
                px, pw = steps[k - 1][0], steps[k - 1][1]
                arrow((px + pw + 0.5, y), (x - 0.5, y))
    bx.text(1, yc + hb / 2 + 1.2, 'conventional route', fontsize=6.5, fontweight='bold', va='bottom')
    bx.text(16 + 14.5 / 2, yc - hb / 2 - 1.0, 'or fixed $z = z_0$ (no search)', ha='center', va='top',
            fontsize=5.6, color=SA, style='italic')
    bx.text(1, yp + hb / 2 + 1.2, 'proposed route', fontsize=6.5, fontweight='bold', va='bottom')
    box(50.5, yd, 13, 'localiser (YOLO) on $I$,\nin 640$^2$ tiles:\none box per pattern', MUTED, fc='#f6f5f2')
    arrow((63.8, yd + 1.2), (66.8, yc - hb / 2 - 0.5))
    arrow((63.8, yd - 1.2), (66.8, yp + hb / 2 + 0.5))
    bx.text(99, 0.2, 'blue: fixed by the equipment     orange: depends on the sample and changes between '
            'acquisitions', ha='right', va='bottom', fontsize=5.8, color=MUTED)
    save(fig, 'fig_setup')


def _band(img, lo, hi):
    """The part of img made of spatial frequencies lo <= |f| < hi (cycles/mm)."""
    f = np.sqrt(freq_sq(img.shape, torch.device('cpu')).numpy()) / 1e3
    x = torch.fft.fft2(torch.from_numpy(img - img.mean()).to(torch.complex64)).numpy()
    return np.real(np.fft.ifft2(x * ((f >= lo) & (f < hi))))


def fig_spectrum(image_id=None):
    """A primer on the frequency domain. Top: an image is a sum of rings of frequencies; each band of rings holds
    details of one size. Bottom: free-space propagation is one filter of those rings; dividing by it undoes it."""
    from matplotlib.patches import Circle
    image_id = image_id if image_id is not None else _test_image(9)
    amp = np.asarray(Image.open(BASE / 'objects' / f'{image_id:06d}_amp.png'), np.float32) / 255
    f = np.sqrt(freq_sq((640, 640), torch.device('cpu')).numpy()) / 1e3        # cycles/mm, fft layout
    from scipy.ndimage import gaussian_filter
    spec = gaussian_filter(np.fft.fftshift(np.log10(np.abs(np.fft.fft2(amp - amp.mean())) + 1e-3)), 1.5)
    fmax = 1 / (2 * PIXEL) / 1e3
    ext = [-fmax, fmax, -fmax, fmax]
    bands = [(0, 4, 'below 4 cycles/mm:\nwhere the letters are'), (4, 20, '4 to 20 cycles/mm:\ntheir strokes'),
             (20, 300, 'above 20 cycles/mm:\ntheir sharp edges')]
    fig = plt.figure(figsize=(7.16, 3.35))
    gs = fig.add_gridspec(2, 5, hspace=0.42, wspace=0.08)
    framed = []
    framed.append(fig.add_subplot(gs[0, 0]))
    show(framed[-1], amp, '(a) an image (object)', vmin=0, vmax=1)
    ax = fig.add_subplot(gs[0, 1])
    ax.imshow(spec, extent=ext, cmap='Greys', vmin=np.percentile(spec, 20), vmax=np.percentile(spec, 99.95))
    for r in (4, 20):
        ax.add_patch(Circle((0, 0), r, fill=False, ec=UNKNOWN, lw=0.9, ls='--'))
        ax.text(r * 0.72, r * 0.72, str(r), color=UNKNOWN, fontsize=6, ha='left', va='bottom', fontweight='bold')
    ax.set_xlim(-30, 30)
    ax.set_ylim(-30, 30)
    ax.set_xticks([-25, 0, 25])
    ax.set_yticks([-25, 0, 25])
    ax.tick_params(labelsize=5.5, length=2, pad=1)
    ax.grid(False)
    ax.set_xlabel('$f_x$ (cycles/mm)', fontsize=5.8, labelpad=0)
    ax.set_title('(b) its spectrum (centre:\ncoarse; edge: fine)', loc='center', fontsize=6.5, pad=2)
    for k, (lo, hi, t) in enumerate(bands):
        show(fig.add_subplot(gs[0, 2 + k]), _band(amp, lo, hi), f'({"cde"[k]}) ' + t)
    # bottom: propagation as a filter, on one absorbing letter with a coherent source
    mask = np.asarray(letter_mask('F', FONTS[0], 110, 0), np.float32) / 255
    clean = Physics().replace(window=(640, 640), dust_density=0, sensor_dust_density=0, bandwidth=0, pinhole=0,
                              pixel_mtf=False)
    holo = _single(dict(mask=mask, absorption=0.5, phase=0.0), clean)
    obj = np.zeros((640, 640), np.float32)
    y0, x0 = (640 - mask.shape[0]) // 2, (640 - mask.shape[1]) // 2
    obj[y0:y0 + mask.shape[0], x0:x0 + mask.shape[1]] = 0.5 * mask
    chi = math.pi * WAVELENGTH * Z0 * (f * 1e3) ** 2
    pred = np.real(np.fft.ifft2(np.fft.fft2(obj) * (-2 * np.cos(chi))))
    wien = np.real(np.fft.ifft2(np.fft.fft2(holo - 1) * (-0.5) * np.cos(chi) / (np.cos(chi) ** 2 + 0.02)))
    c = slice(160, 480)
    framed.append(fig.add_subplot(gs[1, 0]))
    show(framed[-1], 1 - obj[c, c], '(f) one letter that\nabsorbs half the light', vmin=0, vmax=1)
    ax = fig.add_subplot(gs[1, 1])
    ax.imshow(np.fft.fftshift(np.cos(chi)), extent=ext, cmap='RdBu_r', vmin=-1, vmax=1)
    ax.set_xlim(-30, 30)
    ax.set_ylim(-30, 30)
    ax.set_xticks([-25, 0, 25])
    ax.set_yticks([-25, 0, 25])
    ax.tick_params(labelsize=5.5, length=2, pad=1)
    ax.grid(False)
    ax.set_xlabel('$f_x$ (cycles/mm)', fontsize=5.8, labelpad=0)
    ax.set_title('(g) the gains of 19.25 mm\nof free space, $\\cos\\chi$', loc='center', fontsize=6.5, pad=2)
    show(fig.add_subplot(gs[1, 2]), pred[c, c], '(h) the letter multiplied\nby (g) in frequency')
    show(fig.add_subplot(gs[1, 3]), holo[c, c], '(i) the hologram the\nsensor records')
    framed.append(fig.add_subplot(gs[1, 4]))
    show(framed[-1], 1 - wien[c, c], '(j) (i) divided by (g):\nthe letter again', lo=0.5, hi=99.5)
    for a in framed:
        for sp in a.spines.values():
            sp.set_visible(True)
            sp.set_color(GRIDC)
            sp.set_linewidth(0.6)
    save(fig, 'fig_spectrum')


def fig_fresnel():
    """Transfer functions of absorption and phase, the envelopes of the bench, one letter of each material and its
    spectrum, and how much of a pattern a crop keeps."""
    mask = np.asarray(letter_mask('F', FONTS[0], 100, 0), np.float32) / 255
    clean = Physics().replace(window=(640, 640), dust_density=0, sensor_dust_density=0, bandwidth=0, pinhole=0,
                              pixel_mtf=False)
    absorb = _single(dict(mask=mask, absorption=0.6, phase=0.0), clean)
    phase = _single(dict(mask=mask, absorption=0.0, phase=1.0), clean)
    bench = _single(dict(mask=mask, absorption=0.6, phase=0.0), Physics().replace(dust_density=0,
                                                                                    sensor_dust_density=0))
    fig = plt.figure(figsize=(7.16, 4.1))
    top = fig.add_gridspec(1, 3, wspace=0.42, left=0.07, right=0.99, top=0.94, bottom=0.6)
    gs = fig.add_gridspec(1, 4, wspace=0.08, left=0.01, right=0.99, top=0.44, bottom=0.0)
    ax = fig.add_subplot(top[0, 0])
    f = np.linspace(0, 45e3, 3000)            # cycles per metre
    chi = math.pi * WAVELENGTH * Z0 * f ** 2
    ax.plot(f / 1e3, np.cos(chi), color=COLORS['learned'], lw=0.9, label=r'absorption: $\cos\chi$')
    ax.plot(f / 1e3, np.sin(chi), color=COLORS['complex'], lw=0.9, label=r'phase: $\sin\chi$')
    ax.set_xlim(0, 45)
    ax.set_ylim(-1.05, 1.45)
    ax.set_xlabel('|f| (cycles/mm)')
    ax.set_ylabel('transfer function')
    ax.legend(loc='upper center', ncol=2, fontsize=6, handlelength=1.2, columnspacing=0.8)
    ax.set_title('(a) the two filters of free space', fontsize=7)
    ax = fig.add_subplot(top[0, 1])
    f = np.linspace(0, 1 / (2 * PIXEL), 3000)
    d = 100e-6 * Z0 / 0.15
    x = math.pi * d * f
    from scipy.special import j1
    airy = np.where(x > 1e-9, 2 * j1(x) / np.maximum(x, 1e-9), 1.0)
    pix = np.sinc(f * PIXEL)
    ax.plot(f / 1e3, pix, color=COLORS['rec_z0'], lw=0.9, label='pixel')
    ax.plot(f / 1e3, airy, color=COLORS['rec_af'], lw=0.9, label=f'pinhole image ({d * 1e6:.0f} µm)')
    sig = 10e-9 / (2 * math.sqrt(2 * math.log(2))) / WAVELENGTH
    band = np.exp(-0.5 * (math.pi * WAVELENGTH * Z0 * f ** 2 * sig) ** 2)
    ax.plot(f / 1e3, band, color=COLORS['complex'], lw=0.9, label='bandwidth (10 nm)')
    ax.plot(f / 1e3, airy * pix * band, color=INK, lw=1.4, label='all three')
    ax.axhline(0, color=MUTED, lw=0.5)
    ax.set_xlim(0, f[-1] / 1e3)
    ax.set_xlabel('|f| (cycles/mm)')
    ax.legend(loc='upper right', fontsize=6)
    ax.set_title('(b) what the bench keeps of them', fontsize=7)
    # P2: share of the energy of a pattern inside a crop around its object
    ax = fig.add_subplot(top[0, 2])
    big = Physics().replace(window=(2048, 2048), margin=1024, dust_density=0, sensor_dust_density=0, bandwidth=0,
                            pinhole=0, pixel_mtf=False)
    for name, ph, col in [('coherent source', big, COLORS['rec_z0']),
                          ('LED of the bench', big.replace(bandwidth=10e-9, pinhole=100e-6, pixel_mtf=True),
                           COLORS['rec_twin'])]:
        e = (_single(dict(mask=mask, absorption=0.6, phase=0.0), ph) - 1) ** 2
        c = 1024
        side = max(mask.shape)
        ms = np.linspace(0, 6, 61)
        frac = [e[int(c - side * (1 + m) / 2):int(c + side * (1 + m) / 2),
                  int(c - side * (1 + m) / 2):int(c + side * (1 + m) / 2)].sum() / e.sum() for m in ms]
        ax.plot(ms * 100, frac, color=col, label=name)
        k = int(np.argmin(np.abs(ms - 0.25)))
        _note('crop_energy_' + ('coherent' if 'coherent' in name else 'bench'), float(frac[k]))
        ax.plot([25], [frac[k]], 'o', color=col, ms=4)
        ax.annotate(f'{frac[k]:.0%}', (25, frac[k]), xytext=(-14 if 'coherent' in name else -14, 4 if 'LED' in name
                                                                  else -9), textcoords='offset points',
                    fontsize=6.5, color=col, fontweight='bold', ha='right')
    ax.axvline(25, color=MUTED, lw=0.6, ls=':')
    ax.set_xlabel('crop margin (% of object size)')
    ax.set_ylabel('share of the pattern in the crop')
    ax.set_ylim(0, 1)
    ax.legend(loc='lower right', fontsize=6)
    ax.set_title('(c) how much of a pattern a crop holds', fontsize=7)
    crop = slice(320 - 160, 320 + 160)
    obj = np.ones((640, 640), np.float32)
    y0, x0 = (640 - mask.shape[0]) // 2, (640 - mask.shape[1]) // 2
    obj[y0:y0 + mask.shape[0], x0:x0 + mask.shape[1]] -= 0.6 * mask
    for k, (img, title) in enumerate([(obj, '(d) object, 100 px letter'), (absorb, '(e) hologram: absorbing'),
                                      (phase, '(f) hologram: phase only'), (bench, '(g) absorbing, bench LED')]):
        ax = fig.add_subplot(gs[0, k])
        show(ax, img[crop, crop], title)
    save(fig, 'fig_fresnel')


def fig_acquisition(image_id=None):
    """One scene of the test split, recorded step by step from the idealised model to the dataset image."""
    image_id = image_id if image_id is not None else _test_image(9)
    cfg = json.load(open(BASE / 'physics.json'))
    meta = pd.read_csv(BASE / 'metadata.csv').set_index('image_id')
    seed = cfg['seed'] * 1_000_000 + image_id
    ses_seed = cfg['seed'] * 1000 + int(meta.loc[image_id, 'session'])
    quiet = dict(full_well=0.0, read_noise=0.0, bits=0, prnu=0.0, beam_waist=(1e9, 1e9), beam_offset_std=0.0)
    steps = [('(c) idealised model', {**IDEAL, 'bits': 0}),
             ('(d) + finite sensor', {**IDEAL, 'bits': 0, 'margin': 1728, 'reach': 1024}),
             ('(e) + intensity, material',
              dict(quiet, dust_density=0.0, sensor_dust_density=0.0, bandwidth=0.0, pinhole=0.0, pixel_mtf=False)),
             ('(f) + LED, pixel', dict(quiet, dust_density=0.0, sensor_dust_density=0.0)),
             ('(g) + dust, beam, noise', {})]
    out = []
    for title, over in steps:
        p = Physics().replace(**over)
        sc = make_scene(seed, p)
        cam = camera(7, p)
        sc['sensor_dust'] = cam['dust']
        ses = session(ses_seed, p)
        g = torch.Generator(device=DEV).manual_seed(seed + 700_000_000)
        out.append((title, record(sensor_intensity(sc, ses, p, DEV), ses, p, cam, g, DEV)))
    stored = np.load(BASE / 'holograms.npy', mmap_mode='r')[
        pd.read_csv(BASE / 'metadata.csv').image_id.tolist().index(image_id)]
    # the same up to floating-point rounding: another build of CUDA moves a few pixels (docs/REPRODUCIBILITY.md)
    assert np.mean(np.asarray(out[-1][1], float) != stored) < 0.01, 'not the dataset image'
    amp = np.asarray(Image.open(BASE / 'objects' / f'{image_id:06d}_amp.png'))
    ph = np.asarray(Image.open(BASE / 'objects' / f'{image_id:06d}_phase.png'))
    fig, axs = plt.subplots(2, 4, figsize=(7.16, 3.85), gridspec_kw=dict(wspace=0.04, hspace=0.14))
    show(axs[0, 0], amp, '(a) object: amplitude', vmin=0, vmax=255)
    show(axs[0, 1], ph, '(b) object: phase', vmin=0, vmax=255)
    for k, (title, img) in enumerate(out):
        a = axs.flat[2 + k]
        show(a, img, title)
    bg = np.load(BASE / 'backgrounds.npy', mmap_mode='r')[int(meta.loc[image_id, 'session'])]
    show(axs[1, 3], bg, '(h) blank frame')
    save(fig, 'fig_acquisition')
    return image_id


VARIANT_PANELS = [('laser', 'laser'), ('band_40', 'band 40 nm'), ('pinhole_200', 'pinhole 200 µm'),
                  ('source_5cm', 'source at 5 cm'), ('transparent', 'phase objects'), ('depth_300', 'depth ±300 µm'),
                  ('dust_20', 'dust 20/mm²'), ('beam_narrow', 'narrow beam'), ('fullwell_500', 'shot noise, 500 e⁻'),
                  ('bits_4', '4 bits'), ('session_5', 'distance ±5 %'), ('periodic', 'periodic window')]


def fig_variants(image_id=None):
    """The same test scene in the robustness sets (a 320 x 320 region)."""
    image_id = image_id if image_id is not None else _test_image(9)
    fig, axs = plt.subplots(2, 7, figsize=(7.16, 2.35), gridspec_kw=dict(wspace=0.04, hspace=0.18))
    crop = (slice(160, 480), slice(160, 480))

    def load(root):
        meta = pd.read_csv(root / 'metadata.csv')
        return np.load(root / 'holograms.npy', mmap_mode='r')[meta.image_id.tolist().index(image_id)][crop]
    show(axs[0, 0], load(BASE), 'base (bench)')
    for a, (v, t) in zip(axs.flat[1:], VARIANT_PANELS):
        root = paths.dataset(f'variants/{v}')
        if (root / 'holograms.npy').exists():
            show(a, load(root), t)
        else:
            show(a, np.zeros((2, 2)), t + ' (missing)')
    for a in axs.flat[1 + len(VARIANT_PANELS):]:
        a.axis('off')
    save(fig, 'fig_variants')


def fig_autofocus(image_id=None):
    """Blind autofocus of one hologram: sharpness of the reconstruction at every candidate distance."""
    image_id = image_id if image_id is not None else _test_image(9)
    src = Holograms(BASE)
    a = src.amplitude(image_id, DEV)
    zc = Z0 * COARSE
    sc = scan(a, zc).cpu().numpy()
    c = float(COARSE[int(sc.argmax())])
    step = COARSE[1] - COARSE[0]
    fine = np.linspace(c - step, c + step, N_FINE)
    sf = scan(a, Z0 * fine).cpu().numpy()
    z_af = Z0 * float(fine[int(sf.argmax())])
    fig = plt.figure(figsize=(7.16, 2.2))
    gs = fig.add_gridspec(1, 4, width_ratios=[2.2, 1, 1, 1], wspace=0.08)
    ax = fig.add_subplot(gs[0])
    ax.plot(zc * 1e3, sc, '-o', color=COLORS['learned'], ms=2.2, lw=0.9, label=f'{len(COARSE)} coarse candidates')
    ax.plot(Z0 * fine * 1e3, sf, '-o', color=COLORS['complex'], ms=2.2, lw=0.9, label=f'{N_FINE} around the best')
    ax.axvline(src.true_z[image_id] * 1e3, color=INK, lw=0.7, ls=':')
    ax.annotate('true distance', (src.true_z[image_id] * 1e3, sc.min()), xytext=(4, 0), textcoords='offset points',
                fontsize=6.5, color=INK)
    ax.set_xlabel('candidate distance z (mm)')
    ax.set_ylabel('sharpness (Tamura coef. of gradient)')
    ax.legend(loc='upper right')
    ax.set_title('(a) sharpness of the reconstruction', fontsize=7)
    crop = (slice(100, 540), slice(100, 540))
    for k, (z, t) in enumerate([(0.6 * Z0, f'(b) z = {0.6 * Z0 * 1e3:.1f} mm'),
                                (1.4 * Z0, f'(c) z = {1.4 * Z0 * 1e3:.1f} mm'), (z_af, f'(d) z = {z_af * 1e3:.2f} mm, chosen')]):
        axk = fig.add_subplot(gs[k + 1])
        show(axk, backprop(a, [z])[0].abs().cpu().numpy()[crop], t)
    save(fig, 'fig_autofocus')


# ------------------------------------------------------------------------------------------------ results
def _model(flow, rep=1, tag=''):
    from holo_openset.model import load_model
    w = paths.weights(flow, rep, paths.BASE, tag)
    return load_model(w, DEV)[0] if w.exists() else None


def _view(m, holo):
    """What the network receives for a hologram, as one image: the modulus channel at the central distance."""
    with torch.no_grad():
        y = m.filtered(torch.from_numpy(holo)[None])[0]
    if m.fourier.mode in ('prop', 'bank'):
        return y[3 * (m.fourier.alpha.numel() // 2) + 2].cpu().numpy()
    return y[-1].cpu().numpy()


def _evals():
    from holo_openset.paper.tables import evals
    return evals()


def fig_flows(image_id=None, rep=1):
    """One test hologram through every flow: what the network receives (a 320 x 320 region)."""
    from holo_openset.flows import dataset
    image_id = image_id if image_id is not None else _test_image(9)
    crop = (slice(160, 480), slice(160, 480))
    amp = np.asarray(Image.open(BASE / 'objects' / f'{image_id:06d}_amp.png'))
    ph = np.asarray(Image.open(BASE / 'objects' / f'{image_id:06d}_phase.png'))
    holo = dataset('raw').image(image_id)
    panels = [(amp, 'object: amplitude'), (ph, 'object: phase'), (holo, 'hologram')]
    for f, t in [('learned', 'learned layer'), ('complex', 'complex layer, |y|'), ('wiener', 'Wiener filter'),
                 ('prop', 'prop. layer, |y|'), ('bank_w3', 'stack, |y| centre')]:
        m = _model(f, rep)
        if m is not None:
            panels.append((_view(m, holo), t))
    for f, t in [('rec_z0', 'rec. at $z_0$, |q|'), ('rec_af', 'autofocus, |q|'), ('rec_edf', 'per object, |q|'),
                 ('rec_twin', 'twin rem., |q|')]:
        x = dataset(f).image(image_id).astype(np.float32)
        panels.append((x[2], t))
    x = dataset('rec_twin').image(image_id).astype(np.float32)
    panels.append((x[0], 'twin rem., Re q'))
    panels.append((x[1], 'twin rem., Im q'))
    n = len(panels)
    cols = 7
    rows = -(-n // cols)
    fig, axs = plt.subplots(rows, cols, figsize=(7.16, 1.3 * rows + 0.1), gridspec_kw=dict(wspace=0.04, hspace=0.16))
    for k, a in enumerate(axs.flat):
        if k < n:
            img, t = panels[k]
            show(a, img[crop], None, **({'vmin': 0, 'vmax': 255} if k < 2 else {}))
            a.set_title(f'({chr(97 + k)}) {t}', loc='center', fontsize=5.9, pad=2)
        else:
            a.axis('off')
    save(fig, 'fig_flows')


def fig_filter(rep=1):
    """What the Fourier layer learned, read as a gain per ring of frequencies (top), and what it does to the hologram
    of one letter, next to a back-propagation with the parameters (bottom)."""
    from holo_openset.sim.physics import PIXEL as P
    m, mc, ml = _model('learned', rep), _model('complex', rep), _model('learned', rep, '_lr3e-3')
    if m is None:
        print('fig_filter: no model')
        return
    q = m.fourier.q_values.cpu().numpy().astype(np.float64)
    f = np.sqrt(q) / (640 * P) / 1e3        # cycles/mm
    chi = math.pi * WAVELENGTH * Z0 * (f * 1e3) ** 2

    def binned(w, edges):
        idx = np.digitize(f, edges)
        return np.array([np.median(w[idx == i]) if (idx == i).any() else np.nan for i in range(1, len(edges))])
    fig = plt.figure(figsize=(7.16, 4.3))
    top = fig.add_gridspec(1, 2, width_ratios=[1.6, 1], wspace=0.3, left=0.07, right=0.99, top=0.95, bottom=0.55)
    gs = fig.add_gridspec(1, 5, wspace=0.08, left=0.01, right=0.99, top=0.4, bottom=0.0)
    # (a) the real layer: one gain per ring
    ax = fig.add_subplot(top[0, 0])
    lim = 45
    edges = np.linspace(0, lim, 181)
    mid = (edges[1:] + edges[:-1]) / 2
    w = m.fourier.weight.detach().cpu().numpy()
    ax.axhline(1, color=MUTED, lw=0.7, ls='--', label='start: 1 = leave the image as it is')
    ax.axhline(0, color=MUTED, lw=0.5)
    for k in range(0, 7):
        zk = math.sqrt((k + 0.5) / (WAVELENGTH * Z0)) / 1e3
        ax.axvline(zk, color=GRIDC, lw=0.6, ls=':')
    if ml is not None:
        ax.plot(mid, binned(ml.fourier.weight.detach().cpu().numpy(), edges), color=COLORS['raw'], lw=1.0,
                label='same layer, learning rate 100 times smaller')
    ax.plot(mid, binned(w, edges), color=COLORS['learned'], lw=1.1, label='learned real layer')
    ax.set_xlim(0, lim)
    ax.set_ylim(-6.5, 10.5)
    ax.set_xlabel('spatial frequency |f| (cycles/mm); 10 cycles/mm: fringes 100 µm apart')
    ax.set_ylabel('gain $W$ given to the ring')
    ax.set_title('(a) the real layer: the gain it gives to each ring of frequencies', fontsize=7)
    kw = dict(fontsize=5.8, color=INK, ha='center', va='center', linespacing=1.15)
    ax.text(13, 9.0, 'about ×6: the band of the\nletters and their first fringes', **kw)
    ax.text(23, -5.8, 'sign inverted', **kw)
    ax.text(3.6, 3.4, 'coarse:\nlittle\nchange', **kw)
    ax.text(38, -4.6, 'above 30: little signal left\nby the LED; the gains wander', **kw)
    ax.text(30.7, 9.6, 'dotted: zeros of cos χ,\nnot given to the network', fontsize=5.6, color=MUTED,
            ha='left', va='center', linespacing=1.15)
    ax.legend(loc='upper right', fontsize=5.8, handlelength=1.4, bbox_to_anchor=(1.0, 0.88))
    # (b) the complex layer: the phase of its weights
    ax = fig.add_subplot(top[0, 1])
    if mc is not None:
        wc = mc.fourier.weight.detach().cpu().numpy() + 1j * mc.fourier.weight_im.detach().cpu().numpy()
        sel = (f > 0) & (f <= 30)
        ph = np.angle(wc[sel])
        real_share = float(np.mean((np.abs(ph) < 0.2) | (np.abs(np.abs(ph) - np.pi) < 0.2)))
        _note('complex_real_share', real_share)
        ax.plot(f[sel], np.angle(np.exp(1j * chi[sel])), '.', color=GRIDC, ms=1.0,
                label='back-propagation $e^{+i\\chi}$')
        ax.plot(f[sel], ph, '.', color=COLORS['complex'], ms=1.2, alpha=0.6, label='learned complex layer')
        ax.set_yticks([-math.pi, -math.pi / 2, 0, math.pi / 2, math.pi])
        ax.set_yticklabels(['−π', '−π/2', '0', 'π/2', 'π'])
        ax.set_xlim(0, 30)
        ax.set_ylim(-3.6, 4.9)
        ax.set_xlabel('|f| (cycles/mm)')
        ax.set_ylabel('phase of the weight')
        ax.set_title('(b) the complex layer: phase of its weights', fontsize=7)
        ax.text(15, 4.25, f'learned: {real_share:.0%} at 0 or ±π, i.e. real\ngains with a sign; a back-propagation\n'
                          'turns the phase ever faster', fontsize=5.6, color=INK, ha='center', va='center',
                linespacing=1.15)
        ax.legend(loc='lower left', fontsize=5.6, markerscale=5, handletextpad=0.2)
    # bottom: one letter that absorbs and delays the light, with the LED of the bench
    mask = np.asarray(letter_mask('F', FONTS[0], 110, 0), np.float32) / 255
    bench = Physics().replace(dust_density=0, sensor_dust_density=0)
    holo = _single(dict(mask=mask, absorption=0.5, phase=1.0), bench)
    x = torch.from_numpy(holo - holo.mean())[None].to(DEV)
    c = slice(160, 480)
    with torch.no_grad():
        yl = m.fourier(x)[0, 0].cpu().numpy()
        yc = mc.fourier(x)[0, -1].cpu().numpy() if mc is not None else None
        u = backprop(torch.from_numpy(np.sqrt(holo)).to(DEV), [Z0])[0]
        rec = (u - 1).abs().cpu().numpy()
    obj = np.ones((640, 640), np.float32)
    y0, x0 = (640 - mask.shape[0]) // 2, (640 - mask.shape[1]) // 2
    obj[y0:y0 + mask.shape[0], x0:x0 + mask.shape[1]] -= 0.5 * mask
    a = fig.add_subplot(gs[0, 0])
    show(a, obj[c, c], '(c) a letter that absorbs\nand delays the light', vmin=0, vmax=1)
    for sp in a.spines.values():
        sp.set_visible(True)
        sp.set_color(GRIDC)
        sp.set_linewidth(0.6)
    show(fig.add_subplot(gs[0, 1]), holo[c, c], '(d) its hologram\n(LED of the bench)')
    show(fig.add_subplot(gs[0, 2]), yl[c, c], '(e) after the learned\nreal layer (a)')
    if yc is not None:
        show(fig.add_subplot(gs[0, 3]), yc[c, c], '(f) after the learned\ncomplex layer, modulus')
    show(fig.add_subplot(gs[0, 4]), rec[c, c], '(g) back-propagated to $z_0$\nwith λ, Δ, $z_0$ (modulus)')
    save(fig, 'fig_filter')


GRIDC = '#b9b8b2'


def fig_scores(rep=1):
    """Score of each test pattern against the gallery, seen versus never-seen classes, for three flows."""
    from holo_openset.data import embed_annotations
    from holo_openset.evaluate import IDX, calibrate, nn_scores
    from holo_openset.flows import dataset
    fig, axs = plt.subplots(1, 4, figsize=(7.16, 1.9), sharey=False, gridspec_kw=dict(wspace=0.12))
    for k, (ax, f) in enumerate(zip(axs, ['raw', 'learned', 'prop', 'rec_z0'])):
        m = _model(f, rep)
        if m is None:
            continue
        ds = dataset(f)
        ann = ds.ann
        seen = ds.classes(rep)[0]
        lab = ann.classe.map(IDX).to_numpy()
        vs = np.where((ann.split == 'val').to_numpy() & ann.classe.isin(seen).to_numpy())[0]
        te = np.where((ann.split == 'test').to_numpy())[0]
        emb = np.zeros((len(ann), 128), np.float32)
        emb[vs] = embed_annotations(m, ds, ann.iloc[vs])
        emb[te] = embed_annotations(m, ds, ann.iloc[te])
        t, _ = calibrate(emb, lab, vs, ann.filename.to_numpy(), [IDX[c] for c in seen])
        _, s = nn_scores(emb[te], emb[vs], lab[vs])
        known = ann.iloc[te].classe.isin(seen).to_numpy()
        bins = np.linspace(min(s.min(), 0.2), 1, 60)
        ax.hist(s[known], bins, color=KNOWN, alpha=0.75, density=True, label='seen classes')
        ax.hist(s[~known], bins, color=UNKNOWN, alpha=0.75, density=True, label='never seen')
        ax.axvline(t, color=INK, lw=0.8, ls='--')
        ax.set_title(f'({"abcd"[k]}) {LABELS[f]}', fontsize=7)
        ax.set_xlabel('score: similarity to the\nnearest gallery example')
        ax.set_yticks([])
    axs[0].set_ylabel('share of the patterns')
    h, l = axs[0].get_legend_handles_labels()
    h.append(plt.Line2D([], [], color=INK, lw=0.8, ls='--'))
    axs[3].legend(h, l + ['threshold'], loc='upper left', fontsize=6)
    save(fig, 'fig_scores')


def fig_enroll():
    """Accepted and correct share of the patterns of newly enrolled classes, against the number of examples."""
    e = _evals()
    if not len(e):
        return
    fig, ax = plt.subplots(figsize=(3.4, 2.1))
    xs = [5, 20, 230]
    for f in ORDER:
        d = e[e.flow == f]
        if not len(d):
            continue
        y = [d[f'world{k}_new_class_acc'].mean() for k in ['5', '20', 'all']]
        ax.plot(xs, y, '-o', color=COLORS[f], ms=3, lw=1.1, label=SHORT[f])
    ax.set_xscale('log')
    ax.set_xticks(xs)
    ax.set_xticklabels(['5', '20', 'all (~230)'])
    ax.set_xlabel('examples enrolled per new class')
    ax.set_ylabel('accepted and correct')
    ax.set_ylim(0, 1)
    ax.legend(ncol=2, fontsize=5.8, loc='lower right')
    save(fig, 'fig_enroll')


def fig_cost(rep=None):
    """The answer to the size question: time of each stage against image size, and cost against return on full
    frames."""
    from holo_openset.paper.tables import load_csv
    c, g, acc, t = load_csv('timing_cpu'), load_csv('timing_gpu'), load_csv('full_frames'), load_csv('full_frames_time')
    fig, axs = plt.subplots(1, 3, figsize=(7.16, 2.6), gridspec_kw=dict(wspace=0.34))
    stages = [('layer_real', 'real layer', COLORS['learned']), ('layer_prop', 'propagation layer', COLORS['prop']),
              ('layer_bank_w3', 'focal stack (7)', COLORS['bank_w3']), ('backprop', 'one reconstruction', COLORS['rec_z0']),
              ('autofocus', 'autofocus', COLORS['rec_af']), ('twin', 'twin removal', COLORS['rec_twin']),
              ('yolo_tiled', 'YOLO (tiles)', COLORS['raw'])]
    for ax, df, title, key in [(axs[0], c, '(a) one CPU core', 'median_s'), (axs[1], g, '(b) one GPU', 'min_s')]:
        if not len(df):
            continue
        for st, lab, col in stages:
            x = df[df.stage == st].sort_values('megapixels')
            ax.plot(x.megapixels, x[key], '-o', color=col, ms=3, lw=1.1, label=lab)
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel('image size (megapixels)')
        ax.set_ylabel('time (s)')
        ax.set_title(title, fontsize=7)
        ax.set_xticks([0.41, 1.6, 4.2, 10.6])
        ax.set_xticklabels(['0.41\n640²', '1.6', '4.2', '10.6\nfull'])
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', bbox_to_anchor=(0.36, -0.2), ncol=4, fontsize=6, handlelength=1.4,
               columnspacing=1.0)
    ax = axs[2]
    if len(acc) and len(t):
        det = t[t.stage == 'detect'].seconds.median()
        per = t[t.flow != 'all'].groupby(['flow', 'frame', 'rep']).seconds.sum().groupby('flow').median()
        for f in ORDER:
            if f not in per.index:
                continue
            a = acc[(acc.flow == f) & (acc.boxes == 'det')].novel_open_macro_f1.mean()
            ax.plot(per[f] + det, a, 'o', color=COLORS[f], ms=5)
            off = {'complex': (14, 9), 'learned': (16, 0), 'wiener': (14, -10), 'rec_af': (-8, -12),
                   'rec_edf': (-6, 7), 'rec_twin': (-14, -12), 'rec_z0': (8, 2), 'raw': (6, -2), 'prop': (-8, 7),
                   'bank_w3': (6, -8)}[f]
            ax.annotate(SHORT[f], (per[f] + det, a), xytext=off, textcoords='offset points', fontsize=6, color=INK,
                        va='center', arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.4, shrinkA=0, shrinkB=3)
                        if f in ('complex', 'learned', 'wiener') else None)
        ax.text(0.97, 0.06, 'better: up and left', transform=ax.transAxes, ha='right', fontsize=6, color=MUTED)
        ax.set_xlabel('time per full frame, one GPU (s)')
        ax.set_ylabel('open-set F1, end to end')
    ax.set_title('(c) cost and return on a full frame', fontsize=7)
    save(fig, 'fig_cost')


def fig_full_frame(rep=1, frame=0, flow='learned'):
    """A full frame of the sensor with the decisions of the proposed flow, and two zoomed regions."""
    from holo_openset.detect import YoloDetector
    from holo_openset.experiments.full_frames import embed_boxes, gallery
    from holo_openset.flows import dataset
    import matplotlib.patches as mp
    src = Holograms(paths.dataset('full_frames'))
    img = np.array(src.holo[src.row[frame]])
    m = _model(flow, rep)
    if m is None or not paths.yolo_weights(rep).exists():
        return
    boxes, _ = YoloDetector(paths.yolo_weights(rep), device=DEV)(img)
    gal, gal_lab, t, seen_idx = gallery(m, flow, rep, dataset('raw'))
    with torch.no_grad():
        filt = m.filtered(torch.from_numpy(img).to(DEV)[None])
        e = embed_boxes(m, filt, boxes)
    s = e @ gal.T
    score, pred = s.max(1), gal_lab[s.argmax(1)]
    from holo_openset.sim.letters import CLASSES
    fig = plt.figure(figsize=(7.16, 3.2))
    gs = fig.add_gridspec(2, 3, width_ratios=[2.1, 1, 1], wspace=0.05, hspace=0.12)
    ax = fig.add_subplot(gs[:, 0])
    show(ax, img[::2, ::2], f'(a) full frame, 3840 × 2748 px, {len(boxes)} detections')
    for b, sc, p in zip(boxes, score, pred):
        col = KNOWN if sc >= t else UNKNOWN
        ax.add_patch(mp.Rectangle((b[0] / 2, b[1] / 2), (b[2] - b[0]) / 2, (b[3] - b[1]) / 2, fill=False, ec=col, lw=0.5))
    regions = [(600, 1400), (1800, 600)]
    view = filt[0, -1].cpu().numpy()
    for k, (y0, x0) in enumerate(regions):
        for j, (im, name) in enumerate([(img, 'hologram'), (view, 'learned layer')]):
            a = fig.add_subplot(gs[j, 1 + k])
            show(a, im[y0:y0 + 500, x0:x0 + 500], f'({"bcde"[2 * k + j]}) {("upper", "lower")[k]}: {name}')
            if j == 0:
                ax.add_patch(mp.Rectangle((x0 / 2, y0 / 2), 250, 250, fill=False, ec=INK, lw=0.8))
            for b, sc, p in zip(boxes, score, pred):
                if x0 <= b[0] and b[2] <= x0 + 500 and y0 <= b[1] and b[3] <= y0 + 500:
                    col = KNOWN if sc >= t else UNKNOWN
                    a.add_patch(mp.Rectangle((b[0] - x0, b[1] - y0), b[2] - b[0], b[3] - b[1], fill=False, ec=col, lw=0.7))
                    a.text(b[0] - x0, b[1] - y0 - 3, CLASSES[p] if sc >= t else '?', color='white', fontsize=5,
                           bbox=dict(fc=col, ec='none', pad=0.5))
    save(fig, 'fig_full_frame')


def fig_prop(rep=1):
    """The phase of the propagation found without labels: the sharpness of the back-propagated training holograms
    against alpha, the alpha of every repetition, and what the layer does to one letter."""
    import math
    from holo_openset.train import alpha_sharpness
    from holo_openset.sim.physics import PIXEL as P
    m = _model('prop', rep)
    if m is None:
        print('fig_prop: no model')
        return
    cfg = json.load(open(BASE / 'physics.json'))
    meta = pd.read_csv(BASE / 'metadata.csv')
    rng = np.random.RandomState(0)
    ids = rng.choice(meta[meta.split == 'train'].image_id.to_numpy(), 32, replace=False)
    from holo_openset.flows import dataset
    imgs = dataset('raw').images(ids)
    alphas = np.geomspace(0.001, 0.08, 160)
    s = alpha_sharpness(imgs, DEV, alphas)
    a_phys = math.pi * WAVELENGTH * Z0 / (640 * P) ** 2
    trained = [float(_model('prop', r).fourier.alpha.item()) for r in range(1, 6) if _model('prop', r) is not None]
    fig = plt.figure(figsize=(7.16, 3.6))
    top = fig.add_gridspec(1, 2, width_ratios=[1.25, 1], wspace=0.3, left=0.07, right=0.99, top=0.93, bottom=0.6)
    bot = fig.add_gridspec(1, 4, wspace=0.08, left=0.01, right=0.99, top=0.42, bottom=0.0)
    ax = fig.add_subplot(top[0, 0])
    z = alphas / a_phys * Z0 * 1e3                      # the distance that each alpha would mean on the bench
    ax.plot(z, s, color=INK, lw=1.0)
    ax.axvline(Z0 * 1e3, color=UNKNOWN, lw=0.8, ls='--')
    ax.text(Z0 * 1e3 * 1.08, max(s), 'distance of the bench,\nnever given', color=UNKNOWN, fontsize=6, va='top')
    for t in trained:
        ax.axvline(t / a_phys * Z0 * 1e3, color=COLORS['prop'], lw=0.6, alpha=0.7)
    ax.plot([], [], color=COLORS['prop'], lw=0.6, label=f'$\\alpha$ after training, {len(trained)} repetitions')
    ax.set_xscale('log')
    ax.set_xlabel('candidate $\\alpha$, as the distance it would mean (mm, log scale)')
    ax.set_ylabel('sharpness of the\nback-propagated holograms')
    ax.set_title('(a) calibration of $\\alpha$ on 32 training holograms, no label', fontsize=7)
    ax.legend(loc='lower left', fontsize=6)
    _note('alpha_trained_over_physical', [t / a_phys for t in trained])
    # (b) the gain next to the envelope of the bench
    ax = fig.add_subplot(top[0, 1])
    q = m.fourier.q_values.cpu().numpy().astype(np.float64)
    f = np.sqrt(q) / (640 * P) / 1e3
    edges = np.linspace(0, 100, 201)
    mid = (edges[1:] + edges[:-1]) / 2
    idx = np.digitize(f, edges)
    g = m.fourier.weight.detach().cpu().numpy()
    med = np.array([np.median(g[idx == i]) if (idx == i).any() else np.nan for i in range(1, len(edges))])
    ax.plot(mid, med, color=COLORS['prop'], lw=1.1, label='gain of the layer (median per ring)')
    ax.axhline(1, color=MUTED, lw=0.7, ls='--')
    ff = np.linspace(0, 100e3, 400)
    from scipy.special import j1
    d = 100e-6 * Z0 / 0.15
    x = math.pi * d * ff
    airy = np.where(x > 1e-9, 2 * j1(x) / np.maximum(x, 1e-9), 1.0)
    sig = 10e-9 / (2 * math.sqrt(2 * math.log(2))) / WAVELENGTH
    band = np.exp(-0.5 * (math.pi * WAVELENGTH * Z0 * ff ** 2 * sig) ** 2)
    ax2 = ax.twinx()
    ax2.plot(ff / 1e3, airy * band * np.sinc(ff * P), color=MUTED, lw=0.9, ls=':', label='contrast the bench keeps')
    ax2.set_ylim(0, 1.05)
    ax2.set_yticks([])
    ax2.grid(False)
    ax.set_xlim(0, 100)
    ax.set_xlabel('|f| (cycles/mm)')
    ax.set_ylabel('gain')
    ax.set_title('(b) what it learned once the phase is right', fontsize=7)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc='lower left', fontsize=6)
    # bottom: one letter that absorbs and delays the light, with the LED of the bench
    mask = np.asarray(letter_mask('F', FONTS[0], 110, 0), np.float32) / 255
    bench = Physics().replace(dust_density=0, sensor_dust_density=0)
    holo = _single(dict(mask=mask, absorption=0.5, phase=1.0), bench)
    h8 = np.clip(holo * 128, 0, 255).astype(np.uint8)
    c = slice(160, 480)
    show(fig.add_subplot(bot[0, 0]), holo[c, c], '(c) hologram of a letter that\nabsorbs and delays the light')
    show(fig.add_subplot(bot[0, 1]), _view(m, h8)[c, c], '(d) after the propagation\nlayer, |y|')
    mb = _model('bank_w3', rep)
    if mb is not None:
        show(fig.add_subplot(bot[0, 2]), _view(mb, h8)[c, c], '(e) after the focal stack,\n|y| at the central distance')
    with torch.no_grad():
        u = backprop(torch.from_numpy(np.sqrt(holo)).to(DEV), [Z0])[0]
    show(fig.add_subplot(bot[0, 3]), (u - 1).abs().cpu().numpy()[c, c], '(f) back-propagation with\n$\\lambda$, $\\Delta$, $z_0$ (modulus)')
    save(fig, 'fig_prop')


def fig_stack():
    """The focal stack: accuracy on the calibrated bench against accuracy when the distance drifts by 5 %, one point
    per configuration (distances, width, training jitter), with the baselines."""
    from holo_openset.paper.tables import STACKS, evals, load_csv
    e, r = evals(), load_csv('robustness')
    if not len(e) or not len(r):
        return
    fig, ax = plt.subplots(figsize=(3.5, 2.9))
    pts = []
    for f, n, width, jitter in STACKS:
        d = e[e.flow == f]
        rr = r[(r.flow == f) & (r.variant == 'session_5')]
        if not len(d) or not len(rr):
            continue
        label = f'{n} dist.' + (f', $\\pm${width} %' if width else '') + (f', jitter {jitter} %' if jitter else '')
        pts.append((d.novel_open_macro_f1.mean(), rr.novel_open_macro_f1.mean(), label, jitter, n))
    off = {'prop': (-30, 7), 'prop_jit': (5, 3), 'bank': (5, 5), 'bank_jit': (5, 3), 'bank_w3': (5, 3),
           'bank_w1': (5, 3), 'bank_wide': (-104, 7), 'bank_w2': (-24, -13)}
    for (x, y, label, jitter, n), (f, *_) in zip(pts, [s for s in STACKS if len(e[e.flow == s[0]])
                                                      and len(r[(r.flow == s[0]) & (r.variant == 'session_5')])]):
        ax.plot(x, y, 'o', color=COLORS['bank_w3'] if n > 1 else COLORS['prop'], ms=4 + jitter / 3, alpha=0.85)
        ax.annotate(label, (x, y), xytext=off.get(f, (5, 3)), textcoords='offset points', fontsize=5.4, color=INK)
    offb = {'learned': (5, -3), 'rec_z0': (5, -9), 'rec_af': (-36, 5), 'rec_twin': (5, -9)}
    for f in ['learned', 'rec_z0', 'rec_af', 'rec_twin']:
        d, rr = e[e.flow == f], r[(r.flow == f) & (r.variant == 'session_5')]
        if len(d) and len(rr):
            ax.plot(d.novel_open_macro_f1.mean(), rr.novel_open_macro_f1.mean(), 's', color=COLORS[f], ms=5)
            ax.annotate(SHORT[f], (d.novel_open_macro_f1.mean(), rr.novel_open_macro_f1.mean()), xytext=offb[f],
                        textcoords='offset points', fontsize=6, color=INK)
    x0, x1 = ax.get_xlim()
    ax.set_xlim(x0, x1 + 0.25 * (x1 - x0))
    ax.set_xlabel('open-set F1 on the calibrated bench')
    ax.set_ylabel('open-set F1, distance drifting by 5 %')
    ax.text(0.03, 0.97, 'circles: the propagation layer and its stacks\n(size: training jitter); squares: the other flows',
            transform=ax.transAxes, fontsize=5.6, color=MUTED, va='top')
    save(fig, 'fig_stack')


def fig_robustness():
    """Open-set F1 of every flow in every robustness set (models and galleries of the base set)."""
    from holo_openset.paper.tables import load_csv
    from holo_openset.sim.variants import VARIANTS
    d = load_csv('robustness')
    if not len(d):
        return
    piv = d.groupby(['variant', 'flow']).novel_open_macro_f1.mean().unstack()
    rows = [v for v in ['base'] + list(VARIANTS) if v in piv.index]
    cols = [f for f in ORDER if f in piv.columns]
    M_ = piv.loc[rows, cols].to_numpy()
    fig, ax = plt.subplots(figsize=(3.5, 5.6))
    im = ax.imshow(M_, cmap='Blues', vmin=0, vmax=1, aspect='auto')
    for i in range(len(rows)):
        for j in range(len(cols)):
            v = M_[i, j]
            if np.isfinite(v):
                ax.text(j, i, f'{v:.2f}'[1:] if v < 1 else '1.0', ha='center', va='center', fontsize=5,
                        color='white' if v > 0.6 else INK)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([SHORT[c] for c in cols], rotation=60, ha='right', fontsize=6)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(['base (bench)' if r == 'base' else f'{VARIANTS[r][0].split(" (")[0]}: {VARIANTS[r][1]}'
                        for r in rows], fontsize=5.5)
    ax.grid(False)
    save(fig, 'fig_robustness')


ALL = ['fig_setup', 'fig_spectrum', 'fig_fresnel', 'fig_acquisition', 'fig_variants', 'fig_autofocus', 'fig_flows', 'fig_filter', 'fig_prop', 'fig_stack', 'fig_scores',
       'fig_enroll', 'fig_cost', 'fig_full_frame', 'fig_robustness']


def main():
    for name in ALL:
        try:
            globals()[name]()
        except Exception as e:  # one missing result must not stop the others
            print('FAILED', name, repr(e))
