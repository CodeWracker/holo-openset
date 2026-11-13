#!/bin/bash
# Stage 0 of docs/exp_distancia: reproduce the row "distance between sessions 5 %" of the robustness table for four
# flows, with the code of the paper untouched. Usage: bash scripts/exp_distancia/etapa0_sanity.sh cuda:N
set -e
source scripts/exp_distancia/env.sh
DEV=${1:-cuda:0}
mkdir -p $HOLO_LOGS
date; uptime; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
[ -f data/variants/session_5/physics.json ] || python -m holo_openset simulate variant session_5 --device $DEV
[ -f data/variants/session_5/autofocus.csv ] || python -m holo_openset reconstruct --set variants/session_5 --methods z0 af --device $DEV
[ -f data/realistic/autofocus.csv ] || python -m holo_openset reconstruct --set realistic --methods z0 af --device $DEV
python -m holo_openset experiment robustness --device $DEV --variants base session_5 --flows prop bank_jit rec_z0 rec_af
date; uptime
