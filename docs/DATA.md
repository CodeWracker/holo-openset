# Data

Nothing here is needed to run level 1 of [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Where each thing lives

| place | what | size |
|---|---|---|
| this repository | code, fonts, class splits, csv and json results, expected tables, checksums | about 10 MB |
| Zenodo | 245 trained models (embedding networks and localisers); holograms, blank frames and annotations of the base, idealised and small-object sets; 40 full sensor frames | about 20 GB |
| rebuilt by the pipeline | reconstruction caches, auxiliary training scenes, the 35 robustness sets, PNG copies, YOLO working files | about 315 GB |

The Zenodo record has one tar per set. `python -m holo_openset reproduce download` fetches them, checks them against
`checksums/zenodo.sha256` and unpacks them into `data/` and `models/`.

## Sets

| set (`data/`) | content |
|---|---|
| `realistic/` | base set: 5000 windows of 640 x 640 px, 50 sessions of 100 images, split by session (35/7/8) |
| `realistic/aux/` | auxiliary training scenes (seen letters in 25 extra fonts), and those of the calibration twins |
| `ideal/` | the same scenes under the idealised model (real part, opaque letters, periodic window) |
| `variants/<name>/` | the test scenes with one effect changed (noise, source, dust, material, distance between sessions, and `frame_2`, `frame_5`, `walk_05`: the distance drawn for every image, 2 or 5 %, or drifting 0.5 % per image within a session) |
| `full_frames/` | 40 full frames of the sensor, 3840 x 2748 px, 29.4 mm2, in the test sessions |
| `small_z0/`, `small_near/` | letters of 20-60 um at 19.25 mm and at 2 mm |

Each set has `holograms.npy` (uint8), `backgrounds.npy` (blank frame of each session), `annotations.csv`,
`metadata.csv`, `sessions.csv`, `dust.csv`, `physics.json` and, after `reconstruct`, `rec_<method>.npy`.

## Checksums

`checksums/data.sha256` holds the SHA-256 of the holograms and blank frames of every set, in the format of `sha256sum`
(`sha256sum -c` reads it; it has no comment lines). `python -m holo_openset reproduce verify-data` compares the files on
disk with it. The lines of the base, idealised, small-object and full-frame sets and of the 32 older robustness sets are
those of the published build. The last six lines, `variants/frame_2`, `frame_5` and `walk_05`, were added on
2026-11-14 for the files recorded on the server of the distance study (`docs/exp_distancia/`): Python 3.11.18,
PyTorch 2.5.1+cu121, CUDA 12.1, NumPy 1.26.4, NVIDIA H100 80GB HBM3 (driver 580.178.04). On that disk the 32 older
robustness sets were re-simulated with the same code on this build, and their files no longer match the published
checksums (rounding moves a few pixels: [REPRODUCIBILITY.md](REPRODUCIBILITY.md), level 3); their lines were not
rewritten. The narrow-autofocus column of the robustness table was computed on these re-simulated sets (within 0.0023
of F1 of the published ones where both were evaluated).

The narrow autofocus adds 41 GB of reconstruction caches (`rec_afc.npy` of the base set and of the 35 robustness sets)
and the three sets of the distance per image 13 GB more (holograms, blank frames and their other four caches).

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
