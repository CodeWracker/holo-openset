#!/bin/bash
# The pilot at 1.0 mm (docs/exp_resolucao/PROTOCOLO_PILOTO_1MM.md, CADERNO_PILOTO_1MM.md P0 and S3), one step at a time:
#   bash scripts/exp_resolucao/pilot_1mm.sh <physical GPU> <step>
# Steps, in order (each one skips what exists; each writes logs/exp_resolucao/pilot_<step>.log with start, end and
# wall time in seconds):
#   record          data/bench_1mm: 5000 images, 50 sessions of 100 (35 / 7 / 8 by session), the layout of the pilot
#                   (FresnelLayout: letters x 0.22792, the same Fresnel number as the base set), z0 = 1.0 mm,
#                   oversampled 4x (S2: oversampling_convergence.csv), margin 394 px, reach 233 px (S2:
#                   oversampling_margin.csv, oversampling_reach.csv), everything else as the base set
#   reconstruct     data/bench_1mm/rec_z0.npy: back-propagation at the set's own nominal z0 (1.0 mm, physics.json)
#   train           raw, prop, rec_z0 on bench_1mm, repetition 1, without the auxiliary font scenes; prop with the
#                   calibration grid of alpha extended 12 steps below 0.944 mm (train --alpha-extend 12)
#   evaluate        the three flows, repetition 1 -> results_exp_resolucao/eval/bench_1mm/<flow>_r1.json
#   record_07       the test and validation splits of bench_1mm recorded again at z0 = 0.7 mm (same scenes, seeds,
#                   sessions, camera and recorder): data/bench_1mm_robust/z07 (test), data/bench_1mm_robust/z07_val
#   robust_a        (a) as is: rec_z0 of the 0.7 mm test split back-propagated at 1.0 mm (the distance the system was
#                   set up for), models, gallery and threshold of bench_1mm
#                   -> results_exp_resolucao/robustness_bench_1mm.csv (rows base and z07)
#   robust_b        (b) recalibrated without labels: alpha (and from it the distance of rec_z0) from
#                   train.calibrate_alpha on 32 holograms of the 0.7 mm validation split, weights untouched
#                   -> results_exp_resolucao/recal_bench_1mm_z07.json, rec_z0_recal.npy of z07, and the rows
#                   prop+recal and rec_z0+recal of robustness_bench_1mm.csv
#
# THE TWO OPEN CHOICES OF THE ADVISOR (P1) MUST BE GIVEN; the script does not choose them:
#   DEPTH=50     depth spread of the letters of the base set (depth_std 50 um, depth_max 150 um)
#   DEPTH=2.6    the same scaled by 0.22792^2 (2.6 um, 7.8 um)
#   DENSITY=base     8 letters per 640 x 640 window as the base set (Layout: 8 +- 3, 3-18)
#   DENSITY=scaled   the number per window scaled by 1 / 0.22792^2 (154 +- 57.75, 58-346): the same coverage
#   e.g.  DEPTH=50 DENSITY=base bash scripts/exp_resolucao/pilot_1mm.sh 5 record
# record_07 records the 0.7 mm splits with the physics of data/bench_1mm (only z0 changes), whatever the choices.
set -e
cd "$(dirname "$0")/../.."
source scripts/exp_resolucao/env.sh
GPU=$1; STEP=$2
[ -n "$GPU" ] && [ -n "$STEP" ] || { sed -n '2,34p' "$0"; exit 1; }
SET=bench_1mm
ROBUST=bench_1mm_robust
WORKERS=3          # scene builders (PIL, one thread each): with the recorder, about 4 ready threads
LOG=logs/exp_resolucao/pilot_${STEP}.log
mkdir -p logs/exp_resolucao
py() { echo "+ $(date '+%F %T') python -m holo_openset $*"; python -m holo_openset "$@"; }

choices() {
  case "$DEPTH" in
    50) DEPTH_SET="depth_std=50e-6 depth_max=150e-6" ;;
    2.6) DEPTH_SET="depth_std=2.6e-6 depth_max=7.8e-6" ;;
    *) echo "DEPTH must be 50 or 2.6 (the advisor's choice, P1)"; exit 1 ;;
  esac
  case "$DENSITY" in
    base) LAYOUT="letters_mean=8 letters_std=3 letters_min=3 letters_max=18" ;;
    scaled) LAYOUT="letters_mean=154 letters_std=57.75 letters_min=58 letters_max=346" ;;
    *) echo "DENSITY must be base or scaled (the advisor's choice, P1)"; exit 1 ;;
  esac
}

{
echo "start $(date '+%F %T') gpu $GPU step $STEP"
python -c "from holo_openset import paths; print('data', paths.DATA, 'results', paths.RESULTS, 'models', paths.MODELS)"
t0=$(date +%s)
case "$STEP" in
  record)
    choices
    [ -f data/$SET/physics.json ] && { echo "data/$SET exists"; exit 1; }
    py simulate fresnel --name $SET --n-images 5000 --device cuda:$GPU --workers $WORKERS \
       --set-physics z0=1.0e-3 oversample=4 margin=394 reach=233 $DEPTH_SET --layout $LAYOUT
    ;;
  reconstruct)
    [ -f data/$SET/autofocus.csv ] || py reconstruct --set $SET --methods z0 --device cuda:$GPU
    ;;
  train)
    py train --set $SET --flow raw --rep 1 --no-aux --device cuda:$GPU --threads 4
    py train --set $SET --flow prop --rep 1 --no-aux --alpha-extend 12 --device cuda:$GPU --threads 4
    py train --set $SET --flow rec_z0 --rep 1 --no-aux --device cuda:$GPU --threads 4
    ;;
  evaluate)
    for F in raw prop rec_z0; do py evaluate --set $SET --flow $F --rep 1 --device cuda:$GPU --threads 4; done
    ;;
  record_07)
    for SP in test val; do
      OUT=$ROBUST/z07$([ $SP = val ] && echo _val)
      [ -f data/$OUT/physics.json ] || py simulate like --like $SET --name $OUT --split $SP --set-physics z0=0.7e-3 \
                                          --device cuda:$GPU --workers $WORKERS
    done
    ;;
  robust_a)
    Z_SET=$(python -c "import json; print(json.load(open('data/$SET/physics.json'))['physics']['z0'])")
    [ -f data/$ROBUST/z07/autofocus.csv ] || py reconstruct --set $ROBUST/z07 --methods z0 --z0 $Z_SET --device cuda:$GPU
    python -m holo_openset experiment robustness --set $SET --variants-root $ROBUST --variants base z07 \
           --flows raw prop rec_z0 --rep 1 --out robustness_bench_1mm --device cuda:$GPU --threads 4
    ;;
  robust_b)
    J=$HOLO_RESULTS/recal_bench_1mm_z07.json
    [ -f $J ] || python scripts/exp_resolucao/recalibrate_distance.py --set $ROBUST/z07_val --ref $SET --n 32 \
                   --extend 12 --out $J --device cuda:$GPU
    Z=$(python scripts/exp_resolucao/recalibrate_distance.py --read $J z)
    [ -f data/$ROBUST/z07/autofocus_recal.csv ] || \
      py reconstruct --set $ROBUST/z07 --methods z0 --z0 $Z --tag _recal --device cuda:$GPU
    python -m holo_openset experiment robustness --set $SET --variants-root $ROBUST --variants z07 \
           --flows prop rec_z0 --rep 1 --out robustness_bench_1mm --alpha-json $J --rec-tag _recal \
           --device cuda:$GPU --threads 4
    ;;
  *) echo "unknown step $STEP"; exit 1 ;;
esac
echo "end $(date '+%F %T') wall_s $(( $(date +%s) - t0 ))"
} 2>&1 | tee -a $LOG
