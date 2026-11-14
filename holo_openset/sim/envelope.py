"""What an in-line lensless set-up with a partially coherent source keeps of a hologram: the envelope E(f) of the paper
(eq. envelope, Section 3, P4) for any configuration, its cut-off and what follows from it.

    E(f) = exp(-1/2 (chi sigma_lambda / lambda)^2)  x  2 J1(pi d f) / (pi d f)  x  sinc(pixel f)
           bandwidth                                   pinhole image              pixel aperture

with chi = pi lambda z f^2, sigma_lambda = FWHM / (2 sqrt(2 ln 2)) (a Gaussian spectrum), d = D z / L the diameter of
the image of the pinhole (diameter D at a distance L from the SAMPLE) on the sensor, and f the radial frequency taken
along an axis of the sensor (f_y = 0, so the pixel term is one sinc). These are the numbers of fig_fresnel (b) and of
the simulator (sim.physics.coherence_mtf and the sum over wavelengths).

The cut-off f_c at a threshold t is the lowest frequency at which |E| < t (searched up to `f_max`, beyond the Nyquist
frequency of the sensor, so a set-up whose contrast survives above Nyquist shows it). From it:
  b_max          floor(1 / (2 pixel f_c)), at least 1: how many pixels can be averaged without losing what the
                 envelope keeps (1 when f_c is at or above Nyquist: nothing to gain)
  undersampled   f_c > 1 / (2 pixel): the hologram carries contrast the sensor cannot sample (pixel super-resolution
                 can recover it, a single frame cannot)
  half_pitch     1 / (2 f_c): the half period of the finest grating whose fringes keep a contrast of at least t (the
                 convention of the USAF chart: line width = half period); for one frame of the sensor it cannot go
                 below the pixel, half_pitch_single_frame = max(half_pitch, pixel)
The same cut-off without the pixel term is also given (f_c_no_pixel), the convention of a calculation of the source
alone.
"""
import dataclasses
import math

import numpy as np
from scipy.special import j1

FWHM_TO_SIGMA = 1 / (2 * math.sqrt(2 * math.log(2)))
TERMS = ('bandwidth', 'pinhole', 'pixel')


@dataclasses.dataclass(frozen=True)
class Setup:
    """All lengths in metres. Defaults: the bench simulated in the paper."""
    wavelength: float = 385e-9
    bandwidth: float = 10e-9      # FWHM of the spectrum (0: monochromatic)
    pinhole: float = 100e-6       # diameter D of the aperture (0: a point source)
    source_distance: float = 0.15  # L, aperture to sample
    z: float = 385e-9 * 50000     # sample to sensor
    pixel: float = 1.67e-6        # pixel pitch (0: no pixel aperture)

    @property
    def blur(self):
        """Diameter of the image of the pinhole on the sensor, D z / L (m)."""
        return self.pinhole * self.z / self.source_distance

    @property
    def nyquist(self):
        return 1 / (2 * self.pixel) if self.pixel > 0 else math.inf


def terms(s, f):
    """The three factors of E at radial frequencies f (1/m) -> dict of arrays."""
    f = np.asarray(f, dtype=np.float64)
    band = np.exp(-0.5 * (math.pi * s.wavelength * s.z * f ** 2 * s.bandwidth * FWHM_TO_SIGMA / s.wavelength) ** 2)
    x = math.pi * s.blur * f
    pin = np.where(x > 1e-12, 2 * j1(x) / np.maximum(x, 1e-12), 1.0)
    pix = np.sinc(f * s.pixel)
    return dict(bandwidth=band, pinhole=pin, pixel=pix)


def envelope(s, f, pixel=True):
    t = terms(s, f)
    return t['bandwidth'] * t['pinhole'] * (t['pixel'] if pixel else 1.0)


def cutoff(s, threshold=0.1, pixel=True, f_max=2e6, n=2_000_001):
    """Lowest f (1/m) at which |E| < threshold, searched on [0, f_max] (nan when it never falls below)."""
    f = np.linspace(0, f_max, n)
    below = np.abs(envelope(s, f, pixel)) < threshold
    return float(f[int(np.argmax(below))]) if below.any() else math.nan


def summary(s, thresholds=(0.1, 0.05), object_size=50e-6):
    """One row of numbers for a set-up (frequencies in cycles/mm, lengths in um unless named otherwise)."""
    out = dict(**dataclasses.asdict(s), blur_um=s.blur * 1e6, nyquist_cyc_per_mm=s.nyquist / 1e3,
               fresnel_number=(object_size / 2) ** 2 / (s.wavelength * s.z), object_um=object_size * 1e6)
    for t in thresholds:
        fc = cutoff(s, t)
        tag = f'{t:g}'
        v = {k: float(a) for k, a in zip(TERMS, [terms(s, [fc])[k][0] for k in TERMS])}
        logs = {k: -math.log(max(abs(x), 1e-300)) for k, x in v.items()}
        out.update({f'f_c_{tag}': fc / 1e3, f'f_c_no_pixel_{tag}': cutoff(s, t, pixel=False) / 1e3,
                    f'undersampled_{tag}': bool(fc > s.nyquist),
                    f'b_max_{tag}': max(1, math.floor(1 / (2 * s.pixel * fc))) if s.pixel > 0 else 1,
                    f'half_pitch_um_{tag}': 1e6 / (2 * fc),
                    f'half_pitch_single_frame_um_{tag}': max(1e6 / (2 * fc), s.pixel * 1e6),
                    f'dominant_{tag}': min(v, key=v.get),
                    **{f'{k}_at_f_c_{tag}': v[k] for k in TERMS},
                    **{f'{k}_share_{tag}': logs[k] / sum(logs.values()) for k in TERMS},
                    # how far from the object its recorded fringes reach (eq. spread: r = lambda z f), with f up to the
                    # cut-off or the Nyquist frequency, whichever is lower
                    f'pattern_radius_um_{tag}': (object_size / 2 + s.wavelength * s.z * min(fc, s.nyquist)) * 1e6})
    return out


__all__ = ['Setup', 'terms', 'envelope', 'cutoff', 'summary']
