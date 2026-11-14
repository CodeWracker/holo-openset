#!/bin/bash
# Integration runs (docs/exp_distancia/CADERNO_INTEGRACAO.md, step 2): the rec_afc cache of every robustness set of
# the paper, each as soon as its simulation is finished (physics.json present), until all of them have one.
#   bash scripts/exp_distancia/integ_afc_follow.sh cuda:N      (repository root, in tmux)
source scripts/exp_distancia/env.sh
DEV=$1
NAMES=$(python -c "from holo_openset.sim.variants import VARIANTS; print(' '.join(VARIANTS))")
while true; do
  left=0
  for v in $NAMES; do
    [ -e data/variants/$v/rec_afc.npy ] && continue
    left=$((left + 1))
    [ -e data/variants/$v/physics.json ] || continue
    bash scripts/exp_distancia/integ_caches.sh $DEV variants/$v afc || exit 1
  done
  [ $left -eq 0 ] && { echo "all $(echo $NAMES | wc -w) sets have rec_afc.npy"; exit 0; }
  sleep 30
done
