# Reproducibility

Every table, figure and number of the paper comes from this repository, at one of three levels. Pick the one that
matches the time and hardware you have.

| level | what it does | needs | result |
|---|---|---|---|
| **1. Check** | rebuilds every table and number from `results/` and compares with the paper | CPU, 1 minute, no data | byte-identical |
| **2. Evaluate** | downloads the models and holograms, reconstructs, evaluates every model and reruns the end-to-end, discovery, full-frame and fidelity experiments | GPU, about 1 hour on two GPUs, 90 GB of disk | the same numbers, within 0.01 |
| **3. Rebuild** | everything from the seeds: simulation, reconstruction, 240 models, all experiments | several GPUs, 280 GB of disk | within the spread of the five repetitions |

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

Measured in a clean clone, on two H100 GPUs, with the archives of the data record unpacked by hand: 7 minutes of
reconstruction and 46 minutes of evaluation and experiments, 178 jobs, none failed. Of the 137 numbers of the paper
that this level computes again, 135 came out identical and 2 differed within the tolerance:

| number | paper | clean run |
|---|---|---|
| discovery, B-cubed F1 of the learned layer | 0.61 | 0.60 |
| enrollment with k = 5, learned layer | 0.350 | 0.349 |

That run covered the flows of the first draft; the propagation layer and the focal stacks were added afterwards,
with their models in the same data record and their evaluations in the same level. The full-frame experiment was
repeated after full frames moved to fast FFT sizes: two independent runs gave identical
accuracy files. GPU times need a GPU that nothing else is using: on a saturated GPU every call takes the same few
milliseconds, whatever the size of the image.

## Level 3: rebuild

```bash
python -m holo_openset reproduce full --gpus 0 1 2 3
python -m holo_openset paper figures
```

This runs the 555 jobs of `holo_openset/pipeline.py`, one GPU per job. A job that finished leaves `logs/done/<job>.ok`
and is not repeated, so the queue can be stopped and restarted.

What to expect:

* **Simulation.** The scenes, annotations and dust are always the same. The images repeat bit by bit on one build of
  the software (tested: 200 of 200 identical). With another build of PyTorch and CUDA, rounding moves a few pixels:
  rebuilding the base set with `requirements-lock.txt` left 0.02 % of the pixels different from the published set, with
  an rms difference of 0.05 grey levels against an image contrast of 17. `checksums/data.sha256` holds the checksums of
  the published files. To measure a rebuilt set, keep the published one in `data/` and run
  `python -m holo_openset reproduce compare-data path/to/rebuilt/data`.
* **Training.** Seeds are fixed, but GPU training is not fully deterministic. Numbers come out close to the paper, not
  identical. Compare them with the standard deviation over the five repetitions in the tables.
* **Times.** They depend on the machine and on its load. Compare the growth with image size and the ratios between
  stages, not the absolute values. The CPU times of the paper were measured in one run with the server at a load of
  about 230 on 224 cores; GPU times on a GPU that nothing else was using.
* **The propagation phase.** `calibrate_alpha` finds the phase of the propagation on 32 training holograms. The
  models of the base set were calibrated with a linear grid of candidates (0.002 to 0.08, step 0.001); the code now
  uses a geometric grid with the same relative step at every distance, which the small-object set at 2 mm needs. Both
  find alpha within 0.1 % of each other on the base set; a rebuilt model starts from a slightly different alpha and
  ends within the spread of the repetitions.

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
| Figs. bench, spectrum, formation, acquisition, variants, autofocus, flows, filter | none | `python -m holo_openset paper figures` | 2 |

Tables, numbers and figures are written to `output/paper/`. Figures need the data of level 2 and take a few minutes
on one GPU (`HOLO_PAPER_DEVICE=cuda:0`).

## Hardware of the paper

NVIDIA DGX H100 (H100 80 GB), one GPU per job, one CPU core for the CPU timings; Python 3.11, PyTorch 2.5.1 with
CUDA 12.1. See `requirements-lock.txt`.
