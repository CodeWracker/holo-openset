#!/bin/bash
# Integration runs (docs/exp_distancia/CADERNO_INTEGRACAO.md, step 6): ONE full-frame run of every flow of the paper
# plus the narrow autofocus, five repetitions, on the frames of the paper, into results/ (accuracy and time of the
# full-frame table come from this single run). The state of the server and 20 one-second samples of the GPU of the run
# are logged before and after.
#   bash scripts/exp_distancia/integ_ff.sh cuda:N      (repository root, in tmux, with no other job of ours running)
set -e
source scripts/exp_distancia/env.sh
unset HOLO_RESULTS
export HOLO_LOGS=$PWD/logs/integracao
DEV=${1:?device cuda:N}
IDX=${DEV#cuda:}
state() {
  echo "== $1 $(date '+%F %T')"; uptime; echo "ready threads $(ps -eLo stat= | grep -c '^R')"
  nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
}
sample() {
  echo "-- GPU $IDX, 20 samples at 1 s ($1): utilization.gpu, memory.used"
  for i in $(seq 20); do nvidia-smi -i $IDX --query-gpu=utilization.gpu,memory.used --format=csv,noheader | tr '\n' ' '; sleep 1; done
  echo
}
python -c "from holo_openset import paths; print('results ->', paths.RESULTS)"
state before
sample before
echo "== full_frames start $(date '+%F %T')"
python -m holo_openset experiment full_frames --device $DEV --rep 1 2 3 4 5 \
  --flows raw learned complex wiener prop bank_jit rec_z0 rec_af rec_afc rec_edf rec_twin
echo "== full_frames end $(date '+%F %T')"
sample after
state after
