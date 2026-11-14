"""Writes tests/fixtures/native_reference.npz: the output of the simulator at the pixel of the sensor (oversample = 1)
on a small scene with every effect on, computed with the code of commit bed038c (before the oversampled recording existed).
tests/test_oversample.py checks that the simulator still gives exactly these arrays.

    python tests/fixtures/make_native_reference.py   (from the root of the repository; CPU)
"""
import hashlib
import sys
from pathlib import Path

import numpy as np
import torch

from holo_openset.sim.generate import CAMERA_SEED, blank, generate
from holo_openset.sim.physics import Physics, record, sensor_intensity
from holo_openset.sim.scene import camera, make_scene, session

DEV = torch.device('cpu')
SMALL = dict(window=(192, 192), margin=128, reach=96, dust_density=40.0, sensor_dust_density=60.0)


def arrays(tmp):
    p = Physics().replace(**SMALL)
    cam = camera(CAMERA_SEED, p)
    sc = make_scene(5, p)
    sc['sensor_dust'] = cam['dust']
    ses = session(1, p)
    inten = sensor_intensity(sc, ses, p, DEV)
    g = torch.Generator(device=DEV).manual_seed(123)
    rec = record(inten, ses, p, cam, g, DEV)
    bg = blank(ses, p, cam, DEV, 77)
    out = Path(tmp) / 'set'
    generate(out, phys=dict(SMALL), n_images=4, per_session=2, workers=1, dev=DEV, log=lambda *a: None)
    holo = np.load(out / 'holograms.npy')
    ann = hashlib.sha256((out / 'annotations.csv').read_bytes()).hexdigest()
    return dict(inten=inten.numpy(), rec=rec, bg=bg, holo=holo, n_objects=len(sc['objects']), n_dust=len(sc['dust']),
                n_sensor_dust=len(cam['dust'])), ann


if __name__ == '__main__':
    import tempfile
    with tempfile.TemporaryDirectory(dir=sys.argv[1] if len(sys.argv) > 1 else None) as tmp:
        a, ann = arrays(tmp)
    np.savez_compressed(Path(__file__).with_name('native_reference.npz'), annotations_sha256=ann, **a)
    print({k: (v.shape if hasattr(v, 'shape') else v) for k, v in a.items()}, ann)
