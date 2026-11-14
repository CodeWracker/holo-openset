#!/bin/bash
# Test-split data of the distance study that involve no choice (docs/exp_distancia, stage 2): the window sets recorded
# from the test scenes of the base set, their caches z0 and af, and the sets of 40 full frames with a distance per frame
# and with a tilted slide. Everything that already exists is skipped, so the script can be restarted after a crash.
#   bash scripts/exp_distancia/dados_teste.sh cuda:N        (from the root of the repository, in tmux)
set -e
source scripts/exp_distancia/env.sh
DEV=${1:-cuda:0}
WORKERS=${WORKERS:-6}
mkdir -p $HOLO_LOGS
stamp() { echo "== $(date) | $(uptime | sed 's/.*load/load/')"; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr '\n' ' '; echo; }

SETS="session_2 fullwell_500 beam_narrow frame_2 frame_5 walk_05"
for v in $SETS; do
  if [ -f data/variants/$v/physics.json ]; then echo "exists data/variants/$v"; continue; fi
  stamp; echo "simulate variant $v"
  python -m holo_openset simulate variant $v --device $DEV --workers $WORKERS
done
for v in $SETS; do
  # always z0 and af together: z0 alone rewrites autofocus.csv with z_af = z0. autofocus.csv is written last.
  if [ -f data/variants/$v/autofocus.csv ]; then echo "exists data/variants/$v/autofocus.csv"; continue; fi
  stamp; echo "reconstruct variants/$v z0 af"
  python -m holo_openset reconstruct --set variants/$v --methods z0 af --device $DEV
done
full() {   # name, physics override; physics.json is written last
  if [ -f data/full_frames_$1/physics.json ]; then echo "exists data/full_frames_$1"; return; fi
  stamp; echo "simulate full --name $1 --set-physics $2"
  python -m holo_openset simulate full --name $1 --n-images 40 --set-physics $2 --device $DEV --workers 4
}
full frame5 frame_z_std=0.05
for t in 0 1 2 5 10 15; do full tilt$t tilt_deg=$t; done
stamp; echo "all done"
