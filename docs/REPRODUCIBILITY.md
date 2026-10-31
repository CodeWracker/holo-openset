# Reproducibility

Every table, figure and number of the paper comes from this repository, at one of three levels. Pick the one that
matches the time and hardware you have.

| level | what it does | needs | result |
|---|---|---|---|
| **1. Check** | rebuilds every table and number from `results/` and compares with the paper | CPU, 1 minute, no data | byte-identical |
| **2. Evaluate** | downloads the models and holograms, reconstructs, evaluates every model and reruns the end-to-end, discovery, full-frame and fidelity experiments | 1 GPU, @@L2_TIME@@, @@L2_DISK@@ of disk | @@L2_RESULT@@ |
| **3. Rebuild** | everything from the seeds: simulation, reconstruction, 160 models, all experiments | several GPUs, 280 GB of disk | within the spread of the five repetitions |

Set up the environment first: see *Installation* in the [README](../README.md). `requirements-lock.txt` is the exact
environment of the paper.

## Level 1: check

```bash
python -m holo_openset reproduce check
```

It rebuilds `numbers.tex` and the ten tables into a temporary folder and compares them byte by byte with `expected/`,
the snapshot used in the paper. Expected output: `11/11 files identical to expected/`.

## Level 2: evaluate

```bash
python -m holo_openset reproduce download
python -m holo_openset reproduce evaluate --gpus 0        # several GPUs: --gpus 0 1 2
```

Results go to `output/level2/results`, and the run ends by comparing them with the paper: every number must be within
0.01 or 1 %. Stage times are not compared, because they measure the machine. The robustness and oracle experiments
need the robustness sets, so they belong to level 3; level 2 reuses their results from `results/`.

## Level 3: rebuild

```bash
python -m holo_openset reproduce full --gpus 0 1 2 3
python -m holo_openset paper figures
```

This runs the 404 jobs of `holo_openset/pipeline.py`, one GPU per job. A job that finished leaves `logs/done/<job>.ok`
and is not repeated, so the queue can be stopped and restarted.

What to expect:

* **Simulation.** The scenes, annotations and dust are always the same. The images repeat bit by bit on one build of
  the software (tested: 200 of 200 identical). With another build of PyTorch and CUDA, rounding moves a few pixels:
  rebuilding the base set with `requirements-lock.txt` left 0.03 % of the pixels different from the published set, with
  an rms difference of 0.07 grey levels against an image contrast of 17. `checksums/data.sha256` holds the checksums of
  the published files. To measure a rebuilt set, keep the published one in `data/` and run
  `python -m holo_openset reproduce compare-data path/to/rebuilt/data`.
* **Training.** Seeds are fixed, but GPU training is not fully deterministic. Numbers come out close to the paper, not
  identical. Compare them with the standard deviation over the five repetitions in the tables.
* **Times.** They depend on the machine and on the load of the GPU. Compare the growth with image size and the ratios
  between stages, not the absolute values.

## From the paper to the code

| in the paper | results file | experiment | level |
|---|---|---|---|
| main results, ablation, enrollment tables; Figs. scores, enrollment | `results/eval/` | `train`, `evaluate` | 2 |
| end-to-end table | `results/e2e.csv` | `experiment e2e` | 2 |
| discovery table | `results/discovery*.csv` | `experiment discovery` | 2 |
| full-frame table; Figs. cost, full frame | `results/full_frames*.csv` | `experiment full_frames` | 2 |
| stage times table | `results/timing_*.csv` | `experiment timing` | 3 (machine-dependent) |
| robustness table and figure | `results/robustness.csv`, `results/oracle.csv` | `experiment robustness`, `experiment oracle` | 3 |
| idealised and small-object tables | `results/eval/ideal`, `results/eval/small_*` | `evaluate --set` | 2 |
| fidelity numbers | `results/fidelity.json` | `experiment fidelity` | 2 |
| gaps of the idealised model | `results/gaps.json` | `experiment gaps` | 3 |
| Figs. spectrum, formation, acquisition, autofocus, flows, filter | none | `python -m holo_openset paper figures` | 2 |
| Fig. variants | none | `paper figures`, after `simulate variants` | 3 |

Tables and numbers are written to `output/paper/`. Figures need the data of level 2.

## Hardware of the paper

NVIDIA DGX H100 (H100 80 GB), one GPU per job, one CPU core for the CPU timings; Python 3.11, PyTorch 2.5.1 with
CUDA 12.1. See `requirements-lock.txt`.
