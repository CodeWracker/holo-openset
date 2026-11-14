"""The envelope of the source and the pixel for a list of set-ups (holo_openset.sim.envelope): blur of the source,
cut-offs at E < 0.1 and 0.05 (with and without the pixel aperture), b_max, the term that sets the cut-off, whether
the sensor under-samples the hologram, and the half-pitch the envelope allows.

    python scripts/exp_resolucao/envelope_table.py                      # the bench at z = 19.25, 5, 2 and 1 mm
    python scripts/exp_resolucao/envelope_table.py --configs my.csv --out results_exp_resolucao/my_envelope.csv

A configuration csv has one row per set-up and the columns (any missing column takes the value of the bench):
    name, wavelength_nm, bandwidth_nm (FWHM; 0 = monochromatic), pinhole_um (diameter; 0 = point source),
    source_distance_mm (pinhole to SAMPLE), z_mm (sample to sensor), pixel_um, and optionally object_um (default 50)
Other columns (a reference, a page) are carried to the output unchanged.
"""
import argparse
import dataclasses

import pandas as pd

from holo_openset import paths
from holo_openset.sim.envelope import Setup, summary

UNITS = {'wavelength_nm': ('wavelength', 1e-9), 'bandwidth_nm': ('bandwidth', 1e-9), 'pinhole_um': ('pinhole', 1e-6),
         'source_distance_mm': ('source_distance', 1e-3), 'z_mm': ('z', 1e-3), 'pixel_um': ('pixel', 1e-6)}
BENCH_Z = [19.25, 5.0, 2.0, 1.0]


def table(configs):
    rows = []
    for _, c in configs.iterrows():
        kw = {field: float(c[col]) * scale for col, (field, scale) in UNITS.items() if col in c and pd.notna(c[col])}
        s = Setup(**kw)
        r = summary(s, object_size=float(c['object_um']) * 1e-6 if 'object_um' in c and pd.notna(c['object_um'])
                    else 50e-6)
        for f in dataclasses.fields(Setup):   # the set-up in the units of the input
            r.pop(f.name)
        extra = {k: v for k, v in c.items() if k not in UNITS and k != 'object_um'}
        rows.append({**extra, **{col: getattr(s, field) / scale for col, (field, scale) in UNITS.items()}, **r})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--configs', help='csv of set-ups (default: the bench at z = 19.25, 5, 2, 1 mm)')
    ap.add_argument('--out', help='output csv (default: $HOLO_RESULTS/envelope_z.csv for the default set-ups)')
    a = ap.parse_args()
    if a.configs:
        configs = pd.read_csv(a.configs)
    else:
        configs = pd.DataFrame(dict(name=[f'bench, z = {z:g} mm' for z in BENCH_Z], z_mm=BENCH_Z))
    t = table(configs)
    out = a.out or paths.RESULTS / 'envelope_z.csv'
    t.to_csv(out, index=False, float_format='%.6g')
    pd.set_option('display.width', 250)
    pd.set_option('display.max_columns', 60)
    print(t.T.to_string(header=False))
    print('wrote', out)


if __name__ == '__main__':
    main()
