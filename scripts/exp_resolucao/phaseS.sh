#!/bin/bash
# Phase S of the curve stage (docs/exp_resolucao/CADERNO_CURVA.md, Q3: C, D, L). One step at a time, resumable (what
# exists is skipped); log logs/exp_resolucao/S2_<step>[_<tag>].log:
#   bash scripts/exp_resolucao/phaseS.sh <physical GPU> <step>
# Q3-C, the 2 mm column on small_near_newrec (SMALL_FLOWS of pipeline.py:31, --no-aux, r1-r5):
#   caches       reconstruct --set small_near_newrec --methods af twin (the caches of rec_af and rec_twin; the pipeline
#                runs z0 af twin at once, pipeline.py:54; rec_z0.npy exists and is not rewritten; autofocus.csv,
#                written by the z0-only run, is rewritten with the autofocus distances, a copy of it kept first in
#                logs/exp_resolucao/S2_small_near_newrec_autofocus_z0only.csv)
#   queue        FLOWS="..." REPS="..." [SET=...]: for each repetition and flow, train (skipped when the model exists)
#                and evaluate (skipped when the json exists) -> results_exp_resolucao/eval/<SET>/<flow>_r<k>.json;
#                TAG names the log
#   converge_z0, native_z0   the small letters at 19.25 mm (the laws of small_z0): pairs (1, 2), (2, 4) on 4 scenes
#                without noise, then native against converged (S_CONV) -> oversampling_{convergence,native}_small_z0.csv
# Q3-D, two controls of small_near_newrec in r1 (s = 2, master 16, seed 17, 5000 images):
#   record_ctlN  small_near_ctlN: the font sizes of the base set times sqrt(2.0 / 19.25) (the law of the standard
#                family, FresnelLayout scale), border 6 and spacing 4 given as in small_near_newrec
#   record_ctlP  small_near_ctlP: small_near_newrec with the depth law of the family (depth_uniform = 25 um)
#   prep_ctlN, prep_ctlP   sanity against small_near_newrec (train split), effective diameter, reconstruct z0
#   (then queue with SET=small_near_ctlN|P FLOWS="raw prop rec_z0" REPS=1)
set -e
cd "$(dirname "$0")/../.."
source scripts/exp_resolucao/env.sh
export HOLO_THREADS=4 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENCV_FOR_THREADS_NUM=4 \
       NUMBA_NUM_THREADS=4 POLARS_MAX_THREADS=4 RAYON_NUM_THREADS=4
GPU=$1; STEP=$2
[ -n "$GPU" ] && [ -n "$STEP" ] || { sed -n '2,24p' "$0"; exit 1; }
WORKERS=${WORKERS:-6}
SET=${SET:-small_near_newrec}
LOG=logs/exp_resolucao/S2_${STEP}${TAG:+_$TAG}.log
mkdir -p logs/exp_resolucao
py() { echo "+ $(date '+%F %T') python -m holo_openset $*"; python -m holo_openset "$@"; }
python -c "from holo_openset import paths; assert paths.MODELS.name == 'models_exp_resolucao' and \
paths.RESULTS.name == 'results_exp_resolucao', 'paper folders'"
SMALL="font_min=16 font_max=48 border=6 margin=4"
COUNT="letters_mean=8 letters_std=3 letters_min=3 letters_max=18"
SCALE_2MM=0.3223291856101521   # sqrt(2.0e-3 / 19.25e-3)

{
echo "start $(date '+%F %T') gpu $GPU step $STEP set $SET code $(git rev-parse --short HEAD)"
t0=$(date +%s)
case "$STEP" in
  caches)
    [ -f data/small_near_newrec/rec_twin.npy ] && { echo "the caches exist"; exit 0; }
    cp -n data/small_near_newrec/autofocus.csv logs/exp_resolucao/S2_small_near_newrec_autofocus_z0only.csv
    py reconstruct --set small_near_newrec --methods af twin --device cuda:$GPU
    ;;
  queue)
    [ -n "$FLOWS" ] && [ -n "$REPS" ] || { echo "FLOWS and REPS required"; exit 1; }
    for R in $REPS; do
      for F in $FLOWS; do
        py train --set $SET --flow $F --rep $R --no-aux --device cuda:$GPU --threads 4
        [ -f $HOLO_RESULTS/eval/$SET/${F}_r$R.json ] && { echo "exists ${F}_r$R.json"; continue; }
        py evaluate --set $SET --flow $F --rep $R --device cuda:$GPU --threads 4
      done
    done
    ;;
  converge_z0)
    python scripts/exp_resolucao/oversampling_convergence.py converge --device cuda:$GPU --z 19.25 --depths 50um \
       --s 1 2 4 --margin 1728 --reach 1024 --n-scenes 4 --layout factor=16 scale=1 $SMALL $COUNT --tag _small_z0
    ;;
  native_z0)
    [ -n "$S_CONV" ] || { echo "S_CONV required"; exit 1; }
    python scripts/exp_resolucao/oversampling_convergence.py native --device cuda:$GPU --z 19.25 --depths 50um \
       --s $S_CONV --margin 1728 --reach 1024 --n-scenes 4 --layout factor=16 scale=1 $SMALL $COUNT --tag _small_z0
    ;;
  record_ctlN)
    [ -f data/small_near_ctlN/physics.json ] && { echo "exists"; exit 0; }
    py simulate fresnel --name small_near_ctlN --n-images 5000 --device cuda:$GPU --workers $WORKERS \
       --set-physics z0=2.0e-3 oversample=2 --layout factor=16 scale=$SCALE_2MM border=6 margin=4 $COUNT
    ;;
  record_ctlP)
    [ -f data/small_near_ctlP/physics.json ] && { echo "exists"; exit 0; }
    py simulate fresnel --name small_near_ctlP --n-images 5000 --device cuda:$GPU --workers $WORKERS \
       --set-physics z0=2.0e-3 oversample=2 depth_uniform=25e-6 --layout factor=16 scale=1 $SMALL $COUNT
    ;;
  prep_ctlN|prep_ctlP)
    S=small_near_${STEP#prep_}
    [ -f $HOLO_RESULTS/${S}_sanity.json ] || python scripts/exp_resolucao/bench_sanity.py --set $S --ref small_near_newrec \
                                                --device cuda:$GPU
    [ -f $HOLO_RESULTS/hologram_diameter_${S}_summary.json ] || \
      python scripts/exp_resolucao/hologram_diameter.py --set $S --device cuda:$GPU
    [ -f data/$S/autofocus.csv ] || py reconstruct --set $S --methods z0 --device cuda:$GPU
    ;;
  *) echo "unknown step $STEP"; exit 1 ;;
esac
echo "end $(date '+%F %T') wall_s $(( $(date +%s) - t0 ))"
} 2>&1 | tee -a $LOG
