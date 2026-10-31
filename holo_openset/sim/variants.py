"""Robustness sets: the test scenes of the base set recorded again with ONE effect of the acquisition changed. The
models, galleries and thresholds stay those of the base set: a system calibrated on one acquisition meets another.

name -> (effect, value shown in the tables, overrides of holo_openset.sim.physics.Physics). The base value of each
effect is in BASE.
"""
from holo_openset.sim.physics import Physics

B = Physics()
VARIANTS = {
    # sensor noise: electrons per pixel (shot noise), read noise, bit depth
    'fullwell_500': ('shot noise (full well, e-)', 500, dict(full_well=500.0)),
    'fullwell_1500': ('shot noise (full well, e-)', 1500, dict(full_well=1500.0)),
    'fullwell_24000': ('shot noise (full well, e-)', 24000, dict(full_well=24000.0)),
    'read_10': ('read noise (e-)', 10, dict(read_noise=10.0)),
    'read_30': ('read noise (e-)', 30, dict(read_noise=30.0)),
    'read_60': ('read noise (e-)', 60, dict(read_noise=60.0)),
    'bits_6': ('bit depth', 6, dict(bits=6)),
    'bits_4': ('bit depth', 4, dict(bits=4)),
    # illumination
    'beam_narrow': ('beam waist (half diagonals)', '0.9-1.3', dict(beam_waist=(0.9, 1.3), beam_offset_std=0.33)),
    'beam_flat': ('beam waist (half diagonals)', 'uniform', dict(beam_waist=(1e9, 1e9), beam_offset_std=0.0)),
    # source: a laser (coherent), and the LED of the bench with another bandwidth, pinhole or distance
    'laser': ('source', 'laser (coherent)', dict(bandwidth=0.0, pinhole=0.0)),
    'band_0': ('bandwidth (nm)', 0, dict(bandwidth=0.0)),
    'band_20': ('bandwidth (nm)', 20, dict(bandwidth=20e-9, n_wavelengths=9)),
    'band_40': ('bandwidth (nm)', 40, dict(bandwidth=40e-9, n_wavelengths=11)),
    'pinhole_20': ('pinhole (um)', 20, dict(pinhole=20e-6)),
    'pinhole_50': ('pinhole (um)', 50, dict(pinhole=50e-6)),
    'pinhole_200': ('pinhole (um)', 200, dict(pinhole=200e-6)),
    'source_5cm': ('source distance (cm)', 5, dict(source_distance=0.05)),
    # dust
    'dust_0': ('dust (per mm2)', 0, dict(dust_density=0.0, sensor_dust_density=0.0)),
    'dust_8': ('dust (per mm2)', 8, dict(dust_density=8.0)),
    'dust_20': ('dust (per mm2)', 20, dict(dust_density=20.0)),
    # material of the objects
    'opaque': ('objects', 'opaque, no phase', dict(absorption_mean=1.0, absorption_std=0.0, phase_mean=0.0,
                                                 phase_std=0.0)),
    'absorbing': ('objects', 'absorbing only', dict(phase_mean=0.0, phase_std=0.0)),
    'transparent': ('objects', 'transparent (phase only)', dict(absorption_mean=0.05, absorption_std=0.03,
                                                               absorption_min=0.0)),
    # depth inside the sample, and distance between acquisitions
    'depth_0': ('depth spread (um)', 0, dict(depth_std=0.0)),
    'depth_150': ('depth spread (um)', 150, dict(depth_std=150e-6, depth_max=450e-6)),
    'depth_300': ('depth spread (um)', 300, dict(depth_std=300e-6, depth_max=900e-6)),
    'session_0': ('distance between sessions (%)', 0, dict(session_z_std=0.0)),
    'session_2': ('distance between sessions (%)', 2, dict(session_z_std=0.02)),
    'session_5': ('distance between sessions (%)', 5, dict(session_z_std=0.05)),
    # objects outside the sensor
    'no_outside': ('outside the sensor', 'no objects outside', dict(reach=0)),
    'periodic': ('outside the sensor', 'periodic window', dict(margin=0, reach=0, dust_density=0.0,
                                                              sensor_dust_density=0.0)),
}

BASE = {'shot noise (full well, e-)': int(B.full_well), 'read noise (e-)': int(B.read_noise), 'bit depth': B.bits,
        'beam waist (half diagonals)': f'{B.beam_waist[0]:g}-{B.beam_waist[1]:g}', 'source': 'LED of the bench',
        'bandwidth (nm)': round(B.bandwidth * 1e9), 'pinhole (um)': round(B.pinhole * 1e6),
        'source distance (cm)': round(B.source_distance * 100), 'dust (per mm2)': B.dust_density,
        'objects': 'absorb and delay', 'depth spread (um)': round(B.depth_std * 1e6),
        'distance between sessions (%)': B.session_z_std * 100, 'outside the sensor': 'letters and dust around it'}
