"""P1 / R2 of the pilot at 1.0 mm: the oversampled recorder of the simulator (sim/physics.py, oversample = 4) against
the independent implementation of one letter that was validated before (sim_sampling.py::fine_recording), fed with
the SAME fine mask: one absorbing letter (a = 0.6, no phase, depth 0) at the centre of a 640 x 640 window, margin 256,
no dust, no sensor dust, no beam (the intensity before the camera), no noise; the LED band (7 wavelengths) and the
pinhole as in the set. The fine mask is the letter of the pilot layout (median font size, 21.4 px) drawn on the
master grid and averaged onto the 4x grid; it is given to fine_recording as an array and to the recorder as an object
whose master raster IS that mask (factor 4), at the same integer pixel position.
Result: rms(recorder - fine_recording) / rms(fine_recording - 1), and the max difference, on the window.

    python scripts/exp_resolucao/crosscheck_recorder.py --device cuda:N [--z 1.0]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sim_sampling import MARGIN, WINDOW, fine_recording   # noqa: E402

from holo_openset import paths   # noqa: E402
from holo_openset.model import pick_device   # noqa: E402
from holo_openset.sim.letters import FONTS, letter_master   # noqa: E402
from holo_openset.sim.physics import Physics, sample_mask, sensor_intensity   # noqa: E402
from holo_openset.sim.scene import FresnelLayout, physical_object   # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--z', type=float, default=1.0, help='mm')
    a = ap.parse_args()
    torch.set_num_threads(4)
    dev = pick_device(a.device)
    s, f = 4, FresnelLayout.factor
    z = a.z * 1e-3
    lay = FresnelLayout()
    fs = (lay.font_min + lay.font_max) / 2
    master = letter_master('F', FONTS[0], fs * f, 0.0)
    m4, _, _ = sample_mask(dict(master=master, mx=0, my=0, factor=f), s)   # the 4x mask (corner at a pixel corner)
    y, x = MARGIN + (WINDOW - m4.shape[0] // s) // 2, MARGIN + (WINDOW - m4.shape[1] // s) // 2   # canvas pixel
    phys = Physics().replace(window=(WINDOW, WINDOW), margin=MARGIN, reach=0, z0=z, dust_density=0.0,
                             sensor_dust_density=0.0, oversample=s)
    o = physical_object(m4.astype(np.float32), x * s, y * s, s, absorption=0.6, phase=0.0, depth=0.0, kind='letter')
    assert np.array_equal(sample_mask(o, s)[0], m4)
    mine = sensor_intensity(dict(objects=[o], dust=[], sensor_dust=[]), dict(z=z), phys, dev)
    _, ref = fine_recording(m4, s, z, phys, dev, (y, x))
    d = mine - ref
    out = dict(z_mm=a.z, s=s, font_size_px=fs, fine_mask_shape=list(m4.shape), rel_rms=float(d.std() / (ref - 1).std()),
               max_abs=float(d.abs().max()), pattern_rms=float((ref - 1).std()))
    print(out)
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(paths.RESULTS / 'crosscheck_recorder.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
