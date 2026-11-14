#!/bin/bash
# E5 of docs/exp_distancia: the timing session of the study on ONE GPU, in one go: the timing of every stage at every
# size up to the full frame, then the full frames end to end (five repetitions) for every flow of the study, with the
# state of the server and of that GPU logged before and after.
#   bash scripts/exp_distancia/e5_gpu.sh cuda:N results_exp_distancia/e5_aN     (from the root of the repository, in tmux)
# Validity (rule 8.1 of the protocol) is judged afterwards from <outdir>/timing_gpu.csv.
set -e
source scripts/exp_distancia/env.sh
DEV=${1:?device cuda:N}
OUT=$(realpath -m ${2:?output directory})
IDX=${DEV#cuda:}
mkdir -p $OUT $HOLO_LOGS
state() {
  echo "== $1 $(date '+%F %T')"; uptime
  nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
}
sample() {   # utilisation of the GPU of the run, once per second for 20 s
  echo "-- utilisation of GPU $IDX, 20 samples at 1 s ($1)"
  for i in $(seq 20); do nvidia-smi -i $IDX --query-gpu=utilization.gpu,memory.used --format=csv,noheader | tr '\n' ' '; sleep 1; done
  echo
}
state "before"
sample "before"
echo "== timing start $(date '+%F %T')"
HOLO_RESULTS=$OUT python -m holo_openset experiment timing --device $DEV --rep 1
echo "== timing end / full_frames start $(date '+%F %T')"; uptime
HOLO_RESULTS=$OUT python -m holo_openset experiment full_frames --device $DEV --rep 1 2 3 4 5 \
  --flows rec_z0 rec_af rec_afs rec_afsc rec_afc rec_afr rec_edfw prop bank_jit bank_wide bank_w2
echo "== full_frames end $(date '+%F %T')"
sample "after"
state "after"
