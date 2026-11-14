#!/bin/bash
# Integration of the distance study into the paper (docs/exp_distancia/CADERNO_INTEGRACAO.md, step 1): the test split
# of the robustness sets of the paper that are not on disk, one after the other, with the command of the paper queue
# (pipeline.jobs(): `simulate variants`), restricted to the names given. A set whose physics.json exists is skipped
# (physics.json is written last), so the script can be restarted after a crash.
#   bash scripts/exp_distancia/integ_sim.sh cuda:N WORKERS name ...      (from the root of the repository, in tmux)
set -e
source scripts/exp_distancia/env.sh
unset HOLO_RESULTS
export HOLO_LOGS=$PWD/logs/integracao
DEV=$1; WORKERS=$2; shift 2
mkdir -p $HOLO_LOGS
stamp() { echo "== $(date '+%F %T') | $(uptime | sed 's/.*load/load/') | ready threads $(ps -eLo stat= | grep -c '^R')"; }
for v in "$@"; do
  if [ -f data/variants/$v/physics.json ]; then echo "exists data/variants/$v"; continue; fi
  stamp; echo "simulate variant $v"
  python -m holo_openset simulate variant $v --device $DEV --workers $WORKERS
done
stamp; echo "all done"
