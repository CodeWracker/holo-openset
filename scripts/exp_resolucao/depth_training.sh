#!/bin/bash
# P2 / D of the pilot at 1.0 mm: training with the depth spread of the base set (50 / 150 um), r1, one step at a time.
#   bash scripts/exp_resolucao/depth_training.sh <physical GPU> <step>
#   record       data/bench_1mm_depth50: bench_1mm recorded again in ALL splits with depth_std 50 um, depth_max 150 um
#                (generate(like=bench_1mm, split=None): same seeds, sessions, camera, recorder s = 4; images, labels,
#                objects)
#   reconstruct  its rec_z0.npy at its nominal z0 (1.0 mm)
#   train        raw, prop (--alpha-extend 12), rec_z0, r1, --no-aux (models_exp_resolucao/bench_1mm_depth50/)
#   evaluate     the three, r1, on its own test split
#   cross        the models trained with 50 um on the test split of bench_1mm (2.6 um), with the gallery and threshold of
#                their own set -> results_exp_resolucao/robustness_bench_1mm_depth50.csv (variant bench_1mm)
#   table        results_exp_resolucao/depth_training.csv (scripts/exp_resolucao/depth_training.py)
# Nothing that exists is redone. Log: logs/exp_resolucao/depth_<step>.log
set -e
cd "$(dirname "$0")/../.."
source scripts/exp_resolucao/env.sh
GPU=$1; STEP=$2
[ -n "$GPU" ] && [ -n "$STEP" ] || { sed -n '2,13p' "$0"; exit 1; }
SET=bench_1mm_depth50
LOG=logs/exp_resolucao/depth_${STEP}.log
py() { echo "+ $(date '+%F %T') python -m holo_openset $*"; python -m holo_openset "$@"; }
{
echo "start $(date '+%F %T') gpu $GPU step $STEP"
t0=$(date +%s)
case "$STEP" in
  record)
    [ -f data/$SET/physics.json ] && { echo "data/$SET exists"; exit 1; }
    # generate() itself: `simulate like` always passes a split (its --split defaults to test), and every split is wanted
    echo "+ $(date '+%F %T') generate(data/$SET, like=data/bench_1mm, split=None, depth 50 / 150 um)"
    python - <<PY
from holo_openset import paths
from holo_openset.model import pick_device
from holo_openset.sim.generate import generate
generate(paths.dataset('$SET'), phys=dict(depth_std=50e-6, depth_max=150e-6), like=paths.dataset('bench_1mm'),
         split=None, workers=3, dev=pick_device('cuda:$GPU'))
PY
    ;;
  reconstruct)
    [ -f data/$SET/autofocus.csv ] || py reconstruct --set $SET --methods z0 --device cuda:$GPU
    ;;
  train)
    py train --set $SET --flow raw --rep 1 --no-aux --device cuda:$GPU --threads 4
    py train --set $SET --flow prop --rep 1 --no-aux --alpha-extend 12 --device cuda:$GPU --threads 4
    py train --set $SET --flow rec_z0 --rep 1 --no-aux --device cuda:$GPU --threads 4
    ;;
  evaluate)
    for F in raw prop rec_z0; do
      [ -f $HOLO_RESULTS/eval/$SET/${F}_r1.json ] && { echo "exists ${F}_r1.json"; continue; }
      py evaluate --set $SET --flow $F --rep 1 --device cuda:$GPU --threads 4
    done
    ;;
  cross)
    [ -f $HOLO_RESULTS/robustness_bench_1mm_depth50.csv ] && { echo "exists"; exit 0; }
    python -m holo_openset experiment robustness --set $SET --variants-root . --variants bench_1mm \
           --flows raw prop rec_z0 --rep 1 --out robustness_bench_1mm_depth50 --device cuda:$GPU --threads 4
    ;;
  table)
    python scripts/exp_resolucao/depth_training.py
    ;;
  *) echo "unknown step $STEP"; exit 1 ;;
esac
echo "end $(date '+%F %T') wall_s $(( $(date +%s) - t0 ))"
} 2>&1 | tee -a $LOG
