#!/bin/bash
# The two controls of the pilot at 1.0 mm pre-registered in CADERNO_PILOTO_1MM.md, P2 (B and C), repetition 1 only,
# with the pipeline of scripts/exp_resolucao/pilot_1mm.sh (record, reconstruct --methods z0, train raw | prop |
# rec_z0 --no-aux, evaluate). One step at a time:
#   bash scripts/exp_resolucao/controls_1mm.sh <physical GPU> <step>
# Each step writes logs/exp_resolucao/controls_<step>.log (start, end, wall time in seconds) and skips what exists.
#
# Control C, the neighbours: data/bench_1mm_dense = the scenes of bench_1mm (same seeds, physics, recorder, s = 4)
# plus un-annotated filler letters up to 154 letters per 640 x 640 window on average, in the window and in the band
# of the reach (FresnelLayout fill_mean=154, sim/scene.py fill_letters)
#   dense_record       simulate fresnel --name bench_1mm_dense with the arguments of pilot_1mm.sh record and
#                      --layout ... fill_mean=154
#   dense_verify       controls_checks.py dense (annotations equal to bench_1mm, physics.json, recordings without the
#                      fillers equal to bench_1mm, letters per window and covered area) and bench_sanity.py (contact
#                      sheet docs/exp_resolucao/img/bench_1mm_dense_examples.png)
#   dense_reconstruct  reconstruct --methods z0 (the set's z0, 1.0 mm)
#   dense_train        raw, prop (--alpha-extend 12), rec_z0; r1, --no-aux
#   dense_evaluate     -> results_exp_resolucao/eval/bench_1mm_dense/<flow>_r1.json
# Control B, the code: data/base_newrec = the base geometry (FresnelLayout scale 1: fonts 70-118 px, border 12,
# spacing 6, 8 letters per window) and the physics of the base set (z0 19.25 mm, margin 1728, reach 1024, depth
# 50 / 150 um) through the oversampled recorder with s = 2
#   newrec_converge    the pair (2, 4) at 19.25 mm on 4 scenes, noise free (oversampling_convergence.py converge,
#                      -> results_exp_resolucao/oversampling_convergence_base_newrec.csv); MARGIN_CONV=<px> to measure
#                      with a smaller margin when 1728 does not fit at s = 4
#   newrec_master      cost of the master raster (factor 16 / 8 / 4) and its effect on the recording at s = 2
#                      (controls_checks.py master -> results_exp_resolucao/base_newrec_master.csv)
#   newrec_record      simulate fresnel --name base_newrec (MASTER=<factor> required: the choice of newrec_master)
#   newrec_verify      bench_sanity.py --ref realistic (box sides, Fresnel numbers, exposure, noise, contact sheet)
#   newrec_reconstruct, newrec_train (prop with the default grid of alpha), newrec_evaluate
#                      -> results_exp_resolucao/eval/base_newrec/<flow>_r1.json
# Both:
#   table              controls_checks.py table -> results_exp_resolucao/controls.csv (and the paired differences of
#                      bench_1mm_dense to bench_1mm r1)
set -e
cd "$(dirname "$0")/../.."
source scripts/exp_resolucao/env.sh
GPU=$1; STEP=$2
[ -n "$GPU" ] && [ -n "$STEP" ] || { sed -n '2,33p' "$0"; exit 1; }
WORKERS=3          # scene builders (PIL, one thread each)
DENSE=bench_1mm_dense
NEWREC=base_newrec
LOG=logs/exp_resolucao/controls_${STEP}.log
mkdir -p logs/exp_resolucao
py() { echo "+ $(date '+%F %T') python -m holo_openset $*"; python -m holo_openset "$@"; }
# the folders of the study, never the paper's
python -c "from holo_openset import paths; assert paths.MODELS.name == 'models_exp_resolucao' and \
paths.RESULTS.name == 'results_exp_resolucao', 'paper folders'"
LAYOUT_BASE="letters_mean=8 letters_std=3 letters_min=3 letters_max=18"
PHYS_1MM="z0=1.0e-3 oversample=4 margin=394 reach=233 depth_std=2.6e-6 depth_max=7.8e-6"   # = pilot_1mm.sh record
PHYS_BASE="oversample=2 margin=1728 reach=1024 depth_std=50e-6 depth_max=150e-6"           # z0: the default, 19.25 mm

train3() {   # set, extra arguments of prop
  for F in raw prop rec_z0; do
    X=""; [ $F = prop ] && X="$2"
    py train --set $1 --flow $F --rep 1 --no-aux $X --device cuda:$GPU --threads 4
  done
}
evaluate3() {
  for F in raw prop rec_z0; do
    [ -f $HOLO_RESULTS/eval/$1/${F}_r1.json ] && { echo "exists ${F}_r1.json"; continue; }
    py evaluate --set $1 --flow $F --rep 1 --device cuda:$GPU --threads 4
  done
}

{
echo "start $(date '+%F %T') gpu $GPU step $STEP"
python -c "from holo_openset import paths; print('data', paths.DATA, 'results', paths.RESULTS, 'models', paths.MODELS)"
t0=$(date +%s)
case "$STEP" in
  dense_record)
    [ -f data/$DENSE/physics.json ] && { echo "data/$DENSE exists"; exit 1; }
    py simulate fresnel --name $DENSE --n-images 5000 --device cuda:$GPU --workers $WORKERS \
       --set-physics $PHYS_1MM --layout $LAYOUT_BASE fill_mean=154
    ;;
  dense_verify)
    python scripts/exp_resolucao/controls_checks.py dense --set $DENSE --ref bench_1mm --device cuda:$GPU
    python scripts/exp_resolucao/bench_sanity.py --set $DENSE --device cuda:$GPU
    ;;
  dense_reconstruct)
    [ -f data/$DENSE/autofocus.csv ] || py reconstruct --set $DENSE --methods z0 --device cuda:$GPU
    ;;
  dense_train) train3 $DENSE "--alpha-extend 12" ;;
  dense_evaluate) evaluate3 $DENSE ;;
  newrec_converge)
    python scripts/exp_resolucao/oversampling_convergence.py converge --device cuda:$GPU --z 19.25 --depths 50um \
       --s 2 4 --margin ${MARGIN_CONV:-1728} --reach 1024 --n-scenes 4 \
       --layout scale=1 factor=${MASTER:-4} $LAYOUT_BASE --tag _base_newrec
    ;;
  newrec_master)
    python scripts/exp_resolucao/controls_checks.py master --device cuda:$GPU
    ;;
  newrec_record)
    [ -n "$MASTER" ] || { echo "MASTER=<factor of the master raster> (newrec_master)"; exit 1; }
    [ -f data/$NEWREC/physics.json ] && { echo "data/$NEWREC exists"; exit 1; }
    py simulate fresnel --name $NEWREC --n-images 5000 --device cuda:$GPU --workers $WORKERS \
       --set-physics $PHYS_BASE --layout scale=1 factor=$MASTER $LAYOUT_BASE
    ;;
  newrec_verify)
    python scripts/exp_resolucao/bench_sanity.py --set $NEWREC --ref realistic --device cuda:$GPU
    ;;
  newrec_reconstruct)
    [ -f data/$NEWREC/autofocus.csv ] || py reconstruct --set $NEWREC --methods z0 --device cuda:$GPU
    ;;
  newrec_train) train3 $NEWREC "" ;;
  newrec_evaluate) evaluate3 $NEWREC ;;
  table)
    python scripts/exp_resolucao/controls_checks.py table
    ;;
  *) echo "unknown step $STEP"; exit 1 ;;
esac
echo "end $(date '+%F %T') wall_s $(( $(date +%s) - t0 ))"
} 2>&1 | tee -a $LOG
