#!/bin/bash
# Control S of Q2 (docs/exp_resolucao/CADERNO_CURVA.md): the small letters at 2 mm (small_near) re-recorded by the
# oversampled path (small_near_newrec), r1. One step at a time (each writes logs/exp_resolucao/S_<step>.log):
#   bash scripts/exp_resolucao/small_near_control.sh <physical GPU> <step>
# The laws of small_near in physical units: SmallLayout's lengths given to FresnelLayout (scale 1; fonts 16-48 px,
# border 6, spacing 4; 8 +- 3 letters per window, 3-18), the physics of small_near (the default with z0 = 2.0 mm),
# 5000 images, 50 sessions of 100, seed 17 (the splits of generate).
#   ref_cache      the rec_z0 cache of small_near, with the pipeline's command (reconstruct --set small_near --methods
#                  z0); the folder listed (size, date) and the sources hashed before and after
#                  -> logs/exp_resolucao/S_small_near_{before,after}.txt
#   ref_train      small_near as on disk, r1, raw, prop, rec_z0, --no-aux (the pipeline's recipe, pipeline.py:105-110:
#                  the default calibration grid of alpha); models_exp_resolucao/small_near
#   ref_evaluate   -> results_exp_resolucao/eval/small_near/<flow>_r1.json
#   converge       the pairs (1, 2), (2, 4) at 2.0 mm on 4 scenes, noise free (oversampling_convergence.py converge)
#                  -> results_exp_resolucao/oversampling_convergence_small_near.csv
#   native         native (s = 1, mask on the pixels) against converged (S_CONV), split in propagation and drawing
#                  (oversampling_convergence.py native) -> results_exp_resolucao/oversampling_native_small_near.csv
#   record         simulate fresnel --name small_near_newrec (S_CONV, MASTER required)
#   verify         bench_sanity.py --ref small_near (train split only; contact sheet)
#   diameter       hologram_diameter.py --set small_near_newrec
#   reconstruct, train, evaluate   the reference's recipe on small_near_newrec
#   table          small_near_control.py -> results_exp_resolucao/small_near_control.csv
set -e
cd "$(dirname "$0")/../.."
source scripts/exp_resolucao/env.sh
export HOLO_THREADS=4
GPU=$1; STEP=$2
[ -n "$GPU" ] && [ -n "$STEP" ] || { sed -n '2,27p' "$0"; exit 1; }
WORKERS=${WORKERS:-6}
SET=small_near_newrec
LOG=logs/exp_resolucao/S_${STEP}.log
mkdir -p logs/exp_resolucao
py() { echo "+ $(date '+%F %T') python -m holo_openset $*"; python -m holo_openset "$@"; }
python -c "from holo_openset import paths; assert paths.MODELS.name == 'models_exp_resolucao' and \
paths.RESULTS.name == 'results_exp_resolucao', 'paper folders'"
LAYOUT_SMALL="scale=1 font_min=16 font_max=48 border=6 margin=4 letters_mean=8 letters_std=3 letters_min=3 letters_max=18"
PHYS_SMALL="z0=2.0e-3"   # the rest is the default, as small_near (physics.json checked field by field)
snap() {
  ls -l --full-time data/small_near | grep -v '^total'
  for f in holograms.npy backgrounds.npy annotations.csv metadata.csv physics.json sessions.csv dust.csv; do
    sha256sum data/small_near/$f; done
  echo "labels $(ls data/small_near/labels | wc -l) objects $(ls data/small_near/objects | wc -l)"
}
train3() {   # set
  for F in raw prop rec_z0; do py train --set $1 --flow $F --rep 1 --no-aux --device cuda:$GPU --threads 4; done
}
evaluate3() {
  for F in raw prop rec_z0; do
    [ -f $HOLO_RESULTS/eval/$1/${F}_r1.json ] && { echo "exists ${F}_r1.json"; continue; }
    py evaluate --set $1 --flow $F --rep 1 --device cuda:$GPU --threads 4
  done
}

{
echo "start $(date '+%F %T') gpu $GPU step $STEP code $(git rev-parse --short HEAD)"
t0=$(date +%s)
case "$STEP" in
  ref_cache)
    [ -f data/small_near/rec_z0.npy ] && { echo "the cache exists"; exit 1; }
    df -h data | tail -1
    snap > logs/exp_resolucao/S_small_near_before.txt
    py reconstruct --set small_near --methods z0 --device cuda:$GPU
    snap > logs/exp_resolucao/S_small_near_after.txt
    diff logs/exp_resolucao/S_small_near_before.txt logs/exp_resolucao/S_small_near_after.txt || true
    ;;
  ref_train) train3 small_near ;;
  ref_evaluate) evaluate3 small_near ;;
  converge)
    python scripts/exp_resolucao/oversampling_convergence.py converge --device cuda:$GPU --z 2.0 --depths 50um \
       --s ${S_LIST:-1 2 4} --margin 1728 --reach 1024 --n-scenes 4 \
       --layout factor=${MASTER:-16} $LAYOUT_SMALL --tag _small_near
    ;;
  native)
    [ -n "$S_CONV" ] || { echo "S_CONV=<the converged factor> (converge)"; exit 1; }
    python scripts/exp_resolucao/oversampling_convergence.py native --device cuda:$GPU --z 2.0 --depths 50um \
       --s $S_CONV --margin 1728 --reach 1024 --n-scenes 4 \
       --layout factor=${MASTER:-16} $LAYOUT_SMALL --tag _small_near
    ;;
  record)
    [ -n "$S_CONV" ] && [ -n "$MASTER" ] || { echo "S_CONV and MASTER required (converge)"; exit 1; }
    [ -f data/$SET/physics.json ] && { echo "data/$SET exists"; exit 1; }
    py simulate fresnel --name $SET --n-images 5000 --device cuda:$GPU --workers $WORKERS \
       --set-physics $PHYS_SMALL oversample=$S_CONV --layout factor=$MASTER $LAYOUT_SMALL
    ;;
  verify) python scripts/exp_resolucao/bench_sanity.py --set $SET --ref small_near --device cuda:$GPU ;;
  diameter) python scripts/exp_resolucao/hologram_diameter.py --set $SET --device cuda:$GPU ;;
  reconstruct) [ -f data/$SET/autofocus.csv ] || py reconstruct --set $SET --methods z0 --device cuda:$GPU ;;
  train) train3 $SET ;;
  evaluate) evaluate3 $SET ;;
  table) python scripts/exp_resolucao/small_near_control.py ;;
  *) echo "unknown step $STEP"; exit 1 ;;
esac
echo "end $(date '+%F %T') wall_s $(( $(date +%s) - t0 ))"
} 2>&1 | tee -a $LOG
