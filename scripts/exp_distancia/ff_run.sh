#!/bin/bash
# One full-frame accuracy run of docs/exp_distancia (stage 3, E1/E2/E4): a set of full frames, one device, the flows
# given; uptime and nvidia-smi before and after. Stage times of these runs are taken on shared GPUs (not E5).
#   bash scripts/exp_distancia/ff_run.sh cuda:N <frames set> <flow> ...      (from the root of the repository, in tmux)
set -e
source scripts/exp_distancia/env.sh
DEV=$1; SET=$2; shift 2
state() { echo "== $1 $(date '+%F %T')"; uptime; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr '\n' ' '; echo; }
state before
python -m holo_openset experiment full_frames --device $DEV --frames-set $SET --flows "$@"
state after
