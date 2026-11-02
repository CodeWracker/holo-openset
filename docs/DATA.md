# Data

Nothing here is needed to run level 1 of [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Where each thing lives

| place | what | size |
|---|---|---|
| this repository | code, fonts, class splits, csv and json results, expected tables, checksums | about 10 MB |
| Zenodo | 245 trained models (embedding networks and localisers); holograms, blank frames and annotations of the base, idealised and small-object sets; 40 full sensor frames | about 20 GB |
| rebuilt by the pipeline | reconstruction caches, auxiliary training scenes, the 32 robustness sets, PNG copies, YOLO working files | about 260 GB |

The Zenodo record has one tar per set. `python -m holo_openset reproduce download` fetches them, checks them against
`checksums/zenodo.sha256` and unpacks them into `data/` and `models/`.

## Sets

| set (`data/`) | content |
|---|---|
| `realistic/` | base set: 5000 windows of 640 x 640 px, 50 sessions of 100 images, split by session (35/7/8) |
| `realistic/aux/` | auxiliary training scenes (seen letters in 25 extra fonts), and those of the calibration twins |
| `ideal/` | the same scenes under the idealised model (real part, opaque letters, periodic window) |
| `variants/<name>/` | the test scenes with one effect changed (noise, source, dust, material, distance) |
| `full_frames/` | 40 full frames of the sensor, 3840 x 2748 px, 29.4 mm2, in the test sessions |
| `small_z0/`, `small_near/` | letters of 20-60 um at 19.25 mm and at 2 mm |

Each set has `holograms.npy` (uint8), `backgrounds.npy` (blank frame of each session), `annotations.csv`,
`metadata.csv`, `sessions.csv`, `dust.csv`, `physics.json` and, after `reconstruct`, `rec_<method>.npy`.

## Physics

`holo_openset/sim/physics.py` simulates the portable lensless microscope of Sobieranski et al. (2015): a 385 nm UV LED
(10 nm band) behind a 100 um pinhole at 15 cm, the sample at 19.25 mm from the sensor, and a sensor of 1.67 um pixels
read at 8 bits. Each effect can be switched off; `IDEAL` switches off all of them. The evidence for these values, and
what remains unconfirmed, is in [EQUIPMENT.md](EQUIPMENT.md).

## Other paths

`HOLO_DATA`, `HOLO_MODELS`, `HOLO_RESULTS`, `HOLO_LOGS` and `HOLO_PAPER` move the directories above.

## Licences

Code: AGPL-3.0. Data and models on Zenodo: CC-BY-4.0. The YOLO localisers derive from Ultralytics YOLO12s weights,
which are distributed under AGPL-3.0.
