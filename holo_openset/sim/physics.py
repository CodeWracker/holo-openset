"""Forward model of a lensless digital in-line holographic acquisition.

The default parameters are those of the bench of Sobieranski et al. (Light Sci. Appl. 4, e346, 2015): a UV LED of
385 nm behind a 100 um pinhole 15 cm away, a monochrome CMOS sensor with 1.67 um pixels read at 8 bits, the sample
about 19 mm from the sensor (50 000 wavelengths, the distance of the reconstruction routine of that set-up). A full
frame of that sensor is 3840 x 2748 px (29.4 mm^2); the dataset is made of 640 x 640 windows of it (1.14 mm^2), and
`window` can be set to the full frame. See docs/pesquisa_equipamento_e_protocolo.md for what is confirmed and what is
not about the bench.

Every step of an acquisition is simulated and can be switched off (`IDEAL` switches them all off):

  scene     letters (and dust) are placed on a field larger than the sensor; the sensor is its central window.
            Objects outside the window are never annotated, but their fringes enter it, and the fringes of objects
            inside leave it -- as on a real sensor. (On a periodic field the size of the sensor, light that leaves one
            side comes back on the other, and the inversion becomes exact.)
  objects   each letter has its own absorption a and phase delay phi (transmission (1 - a) e^{i phi}) and its own
            depth z_s + d: a sample of finite thickness.
  session   images are acquired in sessions (one sample mounted on the microscope): the sample-to-sensor distance
            z_s ~ z0 (1 + N(0, session_z_std)) and the illumination profile change from session to session.
  dust      particles on the two glass surfaces around the sample (other depths, per image) and on the window of
            the sensor (fixed for the camera, 0.5 mm from the pixels).
  source    partial temporal coherence (a Gaussian spectrum of FWHM `bandwidth`, as a sum of intensity holograms
            over wavelengths) and partial spatial coherence (a pinhole of diameter `pinhole` at `source_distance`
            from the sample: the hologram is blurred by its image, of diameter pinhole * z / source_distance).
  light     Gaussian beam, brighter at the centre; waist and centre change per session (in units of the half
            diagonal of the window, so a full frame and a window are lit alike).
  sensor    the sensor records intensity |U|^2, integrated over each pixel (box MTF), with photo-response
            non-uniformity (fixed for the camera), shot noise (Poisson, `full_well` electrons) and read noise
            (Gaussian), quantised to `bits` and clipped (saturation).

Field propagation: angular spectrum in the Fresnel approximation, H_z(f) = exp(-i pi lambda z |f|^2) (the constant
phase exp(ikz) is common to the reference and the scattered wave and cancels). Objects at different depths are
superposed to first order (their scattered fields are propagated separately and added), which holds for
non-overlapping objects; the sensor dust multiplies the field that reaches it.
"""
import dataclasses
import math

import numpy as np
import torch

PIXEL = 1.67e-6               # pixel pitch (m)
WAVELENGTH = 385e-9           # central wavelength (m)
Z0 = 385e-9 * 50000           # nominal sample-to-sensor distance, 19.25 mm
WINDOW = (640, 640)           # (height, width) of the dataset images (px)
FULL_FRAME = (2748, 3840)     # (height, width) of the full sensor of the bench (px)


@dataclasses.dataclass
class Physics:
    # field
    window: tuple = WINDOW        # (height, width) of the recorded image
    margin: int = 1728            # simulated field around the window on each side (px); 0 = periodic window
    reach: int = 1024             # objects are placed up to this far outside the window (px)
    intensity: bool = True        # record |U|^2 (False: 2 Re(U) - 1, linear in the object, as the idealised model)
    z0: float = Z0                # nominal sample-to-sensor distance (m)
    # objects
    absorption_mean: float = 0.5
    absorption_std: float = 0.25
    absorption_min: float = 0.02
    phase_mean: float = 1.0       # rad
    phase_std: float = 0.5
    phase_max: float = 2.5
    depth_std: float = 50e-6      # m, per object, around the distance of the session
    depth_max: float = 150e-6
    session_z_std: float = 0.005  # relative
    # dust
    dust_density: float = 2.0     # particles per mm^2 of each glass surface around the sample
    dust_depths: tuple = (1.0e-3, -0.2e-3)   # m from the sample plane: far side of the slide, top of the coverslip
    sensor_dust_density: float = 7.0         # particles per mm^2 of the sensor window, fixed for the camera
    sensor_dust_z: float = 0.5e-3
    # source: the LED of the bench
    bandwidth: float = 10e-9      # FWHM (m); 0 = monochromatic
    n_wavelengths: int = 7
    pinhole: float = 100e-6       # m; 0 = point source
    source_distance: float = 0.15  # m
    # illumination (Gaussian beam, intensity exp(-2 r^2 / w^2)), in half diagonals of the window
    beam_waist: tuple = (2.0, 3.5)       # uniform per session
    beam_offset_std: float = 0.18
    # sensor
    pixel_mtf: bool = True
    prnu: float = 0.01
    full_well: float = 6000.0     # electrons; 0 = no shot noise
    exposure: float = 0.45        # background at the beam centre, as a fraction of full scale
    read_noise: float = 3.0       # electrons rms
    bits: int = 8                 # 0 = no quantisation (float output)

    def replace(self, **kw):
        return dataclasses.replace(self, **kw)

    @property
    def canvas(self):
        return self.window[0] + 2 * self.margin, self.window[1] + 2 * self.margin

    @property
    def half_diagonal(self):
        return math.hypot(*self.window) / 2


# The idealised model used by earlier work: the real part of the Fresnel propagation of opaque letters in one plane,
# on a periodic field the size of the sensor, with nothing else.
IDEAL = dict(margin=0, reach=0, intensity=False, absorption_mean=1.0, absorption_std=0.0, phase_mean=0.0,
             phase_std=0.0, depth_std=0.0, session_z_std=0.0, dust_density=0.0, sensor_dust_density=0.0,
             bandwidth=0.0, pinhole=0.0, beam_waist=(1e9, 1e9), beam_offset_std=0.0, pixel_mtf=False, prnu=0.0,
             full_well=0.0, read_noise=0.0)


def physics_from_dict(d):
    return Physics(**{k: tuple(v) if isinstance(v, list) else v for k, v in d.items()})


def freq_sq(shape, dev):
    """|f|^2 (1/m^2) on the FFT grid of a field of shape (height, width)."""
    fy = torch.fft.fftfreq(shape[0], d=PIXEL, device=dev, dtype=torch.float64)
    fx = torch.fft.fftfreq(shape[1], d=PIXEL, device=dev, dtype=torch.float64)
    return fx[None, :] ** 2 + fy[:, None] ** 2


def propagate(u, z, wavelength=WAVELENGTH, q=None):
    """Fresnel propagation of a complex field u [..., h, w] by z (m; negative = back-propagation)."""
    if q is None:
        q = freq_sq(u.shape[-2:], u.device)
    h = torch.exp(-1j * (math.pi * wavelength * z) * q).to(u.dtype)
    return torch.fft.ifft2(torch.fft.fft2(u) * h)


def spread_px(dz, wavelength=WAVELENGTH):
    """How far (px) the finest fringe a pixel can record travels over a distance dz: lambda |dz| / (2 pixel^2)."""
    return wavelength * abs(dz) / (2 * PIXEL ** 2)


def coherence_mtf(shape, z, phys, dev):
    """Transfer function applied to the recorded intensity: spatial coherence (image of the pinhole, a disc of
    diameter pinhole * z / source_distance) and pixel integration (box of one pixel)."""
    fy = torch.fft.fftfreq(shape[0], d=PIXEL, device=dev, dtype=torch.float64)
    fx = torch.fft.fftfreq(shape[1], d=PIXEL, device=dev, dtype=torch.float64)
    out = torch.ones(shape, dtype=torch.float64, device=dev)
    if phys.pinhole > 0:
        d = phys.pinhole * z / phys.source_distance
        x = math.pi * d * torch.sqrt(fx[None, :] ** 2 + fy[:, None] ** 2)
        out = out * torch.where(x > 1e-9, 2 * torch.special.bessel_j1(x) / x.clamp(min=1e-9), torch.ones_like(x))
    if phys.pixel_mtf:
        out = out * torch.sinc(fx * PIXEL)[None, :] * torch.sinc(fy * PIXEL)[:, None]
    return out


def wavelengths(phys):
    """Gauss-Hermite nodes and weights of the source spectrum."""
    if phys.bandwidth <= 0 or phys.n_wavelengths <= 1:
        return [(WAVELENGTH, 1.0)]
    x, w = np.polynomial.hermite_e.hermegauss(phys.n_wavelengths)
    sigma = phys.bandwidth / (2 * math.sqrt(2 * math.log(2)))
    return [(WAVELENGTH + sigma * xi, wi / w.sum()) for xi, wi in zip(x, w)]


def scattered_field(objects, shape, dev):
    """Sum of the fields scattered by every object, in the sample plane (each pre-propagated by its own depth
    offset). objects: dicts with mask (float [h, w] in [0, 1]), x, y (canvas position), absorption, phase, depth
    (offset from the sample plane, m). Patches of the same padded size are propagated as one batch."""
    s = torch.zeros(shape, dtype=torch.complex64, device=dev)
    groups = {}
    for o in objects:
        h, w = o['mask'].shape
        if o['depth'] != 0:
            pad = int(math.ceil(spread_px(o['depth']))) + 16
            H, W = -(-(h + 2 * pad) // 64) * 64, -(-(w + 2 * pad) // 64) * 64  # few distinct sizes: FFT plans reused
        else:
            H, W = h, w
        groups.setdefault((H, W, o['depth'] != 0), []).append(o)
    for (H, W, moved), objs in groups.items():
        for c in range(0, len(objs), 256):  # bounded memory on a full frame
            chunk = objs[c:c + 256]
            batch = torch.zeros(len(chunk), H, W, dtype=torch.complex64, device=dev)
            offs = []
            for k, o in enumerate(chunk):
                h, w = o['mask'].shape
                py, px = (H - h) // 2, (W - w) // 2
                t = (1 - o['absorption']) * np.exp(1j * o['phase'])
                batch[k, py:py + h, px:px + w] = torch.as_tensor(o['mask'], device=dev).to(torch.complex64) * complex(t - 1)
                offs.append((o['x'] - px, o['y'] - py))
            if moved:
                dz = torch.tensor([o['depth'] for o in chunk], dtype=torch.float64, device=dev)[:, None, None]
                hz = torch.exp(-1j * (math.pi * WAVELENGTH) * dz * freq_sq((H, W), dev)[None]).to(torch.complex64)
                batch = torch.fft.ifft2(torch.fft.fft2(batch) * hz)
            for k, (x, y) in enumerate(offs):
                x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + W, shape[1]), min(y + H, shape[0])
                if x1 > x0 and y1 > y0:
                    s[y0:y1, x0:x1] += batch[k, y0 - y:y1 - y, x0 - x:x1 - x]
    return s


def sensor_intensity(scene, session, phys, dev, sample=True):
    """Noise-free intensity on the sensor window (float64 [h, w], background ~1 before the beam profile).
    sample=False: the blank frame of the session (no sample in the beam, sensor dust still there)."""
    shape = phys.canvas
    q = freq_sq(shape, dev)
    z = session['z']
    s = scattered_field(scene['objects'] + scene['dust'], shape, dev) if sample else \
        torch.zeros(shape, dtype=torch.complex64, device=dev)
    td = None
    if scene['sensor_dust']:
        td = torch.ones(shape, dtype=torch.complex64, device=dev)
        for o in scene['sensor_dust']:
            m = torch.as_tensor(o['mask'], dtype=torch.float32, device=dev)
            h, w = m.shape
            t = (1 - o['absorption']) * np.exp(1j * o['phase'])
            td[o['y']:o['y'] + h, o['x']:o['x'] + w] *= (1 + m * complex(t - 1)).to(torch.complex64)
    inten = torch.zeros(shape, dtype=torch.float64, device=dev)
    for lam, wgt in wavelengths(phys):
        if td is None:
            u = 1 + propagate(s, z, lam, q)
        else:
            u = propagate((1 + propagate(s, z - phys.sensor_dust_z, lam, q)) * td, phys.sensor_dust_z, lam, q)
        inten += wgt * ((u.abs() ** 2).double() if phys.intensity else (2 * u.real.double() - 1))
        del u
    mtf = coherence_mtf(shape, z, phys, dev)
    if (mtf != 1).any():
        inten = torch.fft.ifft2(torch.fft.fft2(inten) * mtf).real
    m = phys.margin
    return inten[m:m + phys.window[0], m:m + phys.window[1]]


def beam(session, phys, dev):
    """Intensity profile of the Gaussian beam on the window (1 at its centre)."""
    h, w = phys.window
    y, x = torch.meshgrid(torch.arange(h, device=dev, dtype=torch.float64),
                          torch.arange(w, device=dev, dtype=torch.float64), indexing='ij')
    r = phys.half_diagonal
    r2 = (x - (w - 1) / 2 - session['beam_dx'] * r) ** 2 + (y - (h - 1) / 2 - session['beam_dy'] * r) ** 2
    return torch.exp(-2 * r2 / (session['beam_waist'] * r) ** 2)


def record(inten, session, phys, camera, gen, dev):
    """Intensity on the window -> what the camera stores (uint8 when bits = 8, else float in [0, 2^bits - 1]).
    The idealised model (intensity=False, no noise) is stretched to the full 8-bit range, image by image."""
    if not phys.intensity:
        i = inten.clone()
        lo, hi = i.min(), i.max()
        levels = 2 ** phys.bits - 1 if phys.bits > 0 else 255
        dn = (i - lo) / (hi - lo).clamp(min=1e-12) * levels
    else:
        i = inten * beam(session, phys, dev)
        if phys.prnu > 0:
            i = i * (1 + phys.prnu * camera['prnu'].to(dev))
        levels = 2 ** phys.bits - 1 if phys.bits > 0 else 255
        if phys.full_well > 0:   # the exposure is set on the background at the centre of the beam
            e = torch.poisson((i * (phys.exposure * phys.full_well)).clamp(min=0), generator=gen)
            if phys.read_noise > 0:
                e = e + phys.read_noise * torch.randn(e.shape, generator=gen, device=dev, dtype=e.dtype)
            dn = e * levels / phys.full_well
        else:
            dn = i * (phys.exposure * levels)
    if phys.bits > 0:
        dn = dn.round().clamp(0, levels)
        if phys.bits == 8:
            return dn.to(torch.uint8).cpu().numpy()
    return dn.float().cpu().numpy()
