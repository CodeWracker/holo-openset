#!/bin/bash
# One training of the pilot (docs/exp_resolucao, T4): flow F on the set reduced b x b, repetition 1, the recipe of the
# paper (python -m holo_openset train: 3000 steps, auxiliary scenes of r1 reduced the same way). Skips a model that
# exists. Log: logs/exp_resolucao/train_<F>_b<b>.log (start, end and wall time in seconds on the last lines).
#   bash scripts/exp_resolucao/train_pilot.sh <physical GPU> <flow> <b>
set -e
cd "$(dirname "$0")/../.."
source scripts/exp_resolucao/env.sh
GPU=$1; F=$2; B=$3
LOG=logs/exp_resolucao/train_${F}_b${B}.log
{
  echo "start $(date '+%F %T') gpu $GPU"
  python -c "from holo_openset import paths; print('results', paths.RESULTS, 'models', paths.MODELS)"
  t0=$(date +%s)
  python -m holo_openset train --flow $F --rep 1 --set realistic_b$B --device cuda:$GPU --threads 4
  echo "end $(date '+%F %T') wall_s $(( $(date +%s) - t0 ))"
} 2>&1 | tee -a $LOG
