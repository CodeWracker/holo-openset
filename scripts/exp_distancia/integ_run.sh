#!/bin/bash
# Integration of the distance study into the paper (docs/exp_distancia/CADERNO_INTEGRACAO.md): one command of the
# package with results/ as output (HOLO_RESULTS unset unless RESULTS=<dir> is given) and the state of the server
# before and after.
#   bash scripts/exp_distancia/integ_run.sh <python -m holo_openset arguments>      (repository root, in tmux)
set -e
source scripts/exp_distancia/env.sh
if [ -n "$RESULTS" ]; then export HOLO_RESULTS=$RESULTS; else unset HOLO_RESULTS; fi
export HOLO_LOGS=$PWD/logs/integracao
state() {
  echo "== $1 $(date '+%F %T') | $(uptime | sed 's/.*load/load/') | ready threads $(ps -eLo stat= | grep -c '^R')"
  nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr '\n' ' '; echo
}
python -c "from holo_openset import paths; print('results ->', paths.RESULTS)"
state before
echo "python -m holo_openset $*"
python -m holo_openset "$@"
state after
