#!/bin/bash
# The density curve of CADERNO_CURVA.md, Q0 b: sets at 1.0 mm with the annotated letters of the pilot (same seeds,
# 8 per window) and un-annotated filler letters (FresnelLayout fill_mean, K1 of CADERNO_PILOTO_1MM.md) up to LEVEL
# letters per 640 x 640 window, with the depth law of the standard family (LAW). The recorder (s = 4), the physics
# and the recipe of the pilot. One step at a time:
#   LAW=<law> LEVEL=<level> [REP=<1-5>] [WORKERS=<n>] bash scripts/exp_resolucao/density_curve.sh <physical GPU> <step>
# LEVEL   8 (no fillers: the sparse level of the family), 15, 69, 154, 343, 514 (letters per window; 7, 13, 60, 135, 300, 450
#         per mm^2)
# LAW     d50   depth_std 50 um, depth_max 150 um (as bench_1mm_depth50); its sparse level IS bench_1mm_depth50
#               (recorded by the other executor; never re-recorded here)
#         u50   uniform over the 50 um of the channel, +-25 um (Physics.depth_uniform; the law of the standard family,
#               Q1); its sparse level is data/curve_u50_L008 (bench_1mm with the uniform depths), recorded here
# Sets: data/curve_<LAW>_L<LEVEL, 3 digits> (the sparse level of d50: bench_1mm_depth50).
# Steps (each skips what exists; log logs/exp_resolucao/curve_<step>_<LAW>_L<LEVEL>[_r<REP>].log):
#   record       simulate fresnel with the arguments of pilot_1mm.sh record, the depth law and fill_mean=LEVEL;
#                WORKERS scene builders (default 8; the images do not depend on it, CADERNO_CURVA_DENSIDADE.md)
#   verify       LEVEL > 8: controls_checks.py dense against the sparse level of the family (annotations, labels, maps,
#                dust, sessions, blank frames identical; recordings without the fillers identical to the sparse set;
#                letters per window, skipped fillers, covered area); LEVEL 8 of u50: controls_checks.py sparse
#                against bench_1mm (equal up to the depths, the depth law, 2 images rebuilt from their seeds); both
#                with bench_sanity.py (contact sheet)
#                -> $HOLO_RESULTS/<set>_checks.json, <set>_sanity.json
#   reconstruct  reconstruct --methods z0 (the set's z0, 1.0 mm)
#   train        raw, prop (--alpha-extend 12), rec_z0; repetition REP (default 1), --no-aux
#   evaluate     -> $HOLO_RESULTS/eval/<set>/<flow>_r<REP>.json
#   table        density_curve_table.py -> $HOLO_RESULTS/density_curve.csv, _reps.csv, _reading.json (u50; other laws
#                with the suffix _<LAW>) (the rules
#                of Q0: obtained density, overlap ratio, "fell", "the curves separate")
set -e
cd "$(dirname "$0")/../.."
source scripts/exp_resolucao/env.sh
GPU=$1; STEP=$2
[ -n "$GPU" ] && [ -n "$STEP" ] || { sed -n '2,27p' "$0"; exit 1; }
REP=${REP:-1}
WORKERS=${WORKERS:-8}
case "$REP" in 1|2|3|4|5) ;; *) echo "REP must be 1-5"; exit 1 ;; esac
case "$LAW" in
  d50) DEPTH="depth_std=50e-6 depth_max=150e-6"; SPARSE=bench_1mm_depth50 ;;
  u50) DEPTH="depth_std=2.6e-6 depth_max=7.8e-6 depth_uniform=25e-6"; SPARSE=curve_u50_L008 ;;   # std, max unused
  *) echo "LAW must be d50 or u50 (the depth law of the standard family, Q1)"; exit 1 ;;
esac
case "$LEVEL" in 8|15|69|154|343|514) ;; *) [ "$STEP" = table ] || { echo "LEVEL must be 8, 15, 69, 154, 343 or 514"; exit 1; } ;; esac
SET=curve_${LAW}_L$(printf %03d "${LEVEL:-0}"); [ "$LEVEL" = 8 ] && SET=$SPARSE
FILL="fill_mean=$LEVEL"; [ "$LEVEL" = 8 ] && FILL=""   # the sparse level has no fillers
LOG=logs/exp_resolucao/curve_${STEP}_${LAW}$([ "$STEP" != table ] && echo _L$LEVEL || true)$([ "$REP" != 1 ] && echo _r$REP || true).log
mkdir -p logs/exp_resolucao
py() { echo "+ $(date '+%F %T') python -m holo_openset $*"; python -m holo_openset "$@"; }
python -c "from holo_openset import paths; assert paths.MODELS.name == 'models_exp_resolucao' and \
paths.RESULTS.name == 'results_exp_resolucao', 'paper folders'"
LAYOUT_BASE="letters_mean=8 letters_std=3 letters_min=3 letters_max=18"
PHYS_1MM="z0=1.0e-3 oversample=4 margin=394 reach=233 $DEPTH"   # = pilot_1mm.sh record, with the depth law

{
echo "start $(date '+%F %T') gpu $GPU step $STEP law $LAW level $LEVEL set $SET rep $REP workers $WORKERS"
python -c "from holo_openset import paths; print('data', paths.DATA, 'results', paths.RESULTS, 'models', paths.MODELS)"
t0=$(date +%s)
case "$STEP" in
  record)
    [ "$LEVEL" = 8 ] && [ "$LAW" = d50 ] && { echo "the sparse level of LAW=d50 is $SPARSE: not recorded here"; exit 1; }
    [ -f data/$SET/physics.json ] && { echo "data/$SET exists"; exit 1; }
    py simulate fresnel --name $SET --n-images 5000 --device cuda:$GPU --workers $WORKERS \
       --set-physics $PHYS_1MM --layout $LAYOUT_BASE $FILL
    ;;
  verify)
    if [ "$LEVEL" = 8 ]; then
      [ "$LAW" = d50 ] && { echo "the sparse level of d50 is not verified here"; exit 1; }
      python scripts/exp_resolucao/controls_checks.py sparse --set $SET --ref bench_1mm --device cuda:$GPU
    else
      python scripts/exp_resolucao/controls_checks.py dense --set $SET --ref $SPARSE --device cuda:$GPU
    fi
    python scripts/exp_resolucao/bench_sanity.py --set $SET --device cuda:$GPU
    ;;
  reconstruct)
    [ -f data/$SET/autofocus.csv ] || py reconstruct --set $SET --methods z0 --device cuda:$GPU
    ;;
  train)
    py train --set $SET --flow raw --rep $REP --no-aux --device cuda:$GPU --threads 4
    py train --set $SET --flow prop --rep $REP --no-aux --alpha-extend 12 --device cuda:$GPU --threads 4
    py train --set $SET --flow rec_z0 --rep $REP --no-aux --device cuda:$GPU --threads 4
    ;;
  evaluate)
    for F in raw prop rec_z0; do
      [ -f $HOLO_RESULTS/eval/$SET/${F}_r$REP.json ] && { echo "exists ${F}_r$REP.json"; continue; }
      py evaluate --set $SET --flow $F --rep $REP --device cuda:$GPU --threads 4
    done
    ;;
  table)
    python scripts/exp_resolucao/density_curve_table.py --law $LAW --sparse $SPARSE --prefix density_curve$([ "$LAW" != u50 ] && echo _$LAW || true)
    ;;
  *) echo "unknown step $STEP"; exit 1 ;;
esac
echo "end $(date '+%F %T') wall_s $(( $(date +%s) - t0 ))"
} 2>&1 | tee -a $LOG
