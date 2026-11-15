#!/bin/bash
# Test J2 of the curve stage (docs/exp_resolucao/CADERNO_CURVA.md, Q3 section J2; executor notebook
# CADERNO_CURVA_DISTANCIA.md, D4 on): the focal stacks of the package, recipe unchanged (flows.FLOWS), trained on
# the sparse level of the standard family and tested as test J (bank_jit_distance.sh), with the repetition and the
# bank as parameters, plus the recalibration of the bank without labels by ratio:
#   BANK=bank_jit|bank_wide|bank_w2|bank_w3 REP=1..5 bash scripts/exp_resolucao/banks_distance.sh <physical GPU> <step>
#   train         python -m holo_openset train --set curve_u50_L008 --flow $BANK --rep $REP --no-aux --alpha-extend 12
#                 (skipped when the model exists: bank_jit r1 is that of test J)
#   evaluate      evaluate --set curve_u50_L008 --flow $BANK --rep $REP -> eval/curve_u50_L008/<bank>_r<rep>.json
#                 (the 1.0 mm row; skipped when it exists)
#   shifted       as is at 0.9 and 1.1 mm: experiment robustness --set curve_u50_L008 --variants-root curve_u50_robust
#                 --variants z09 z11 --flows $BANK --rep $REP (bank_jit r1: the rows of test J exist and are not read
#                 again)
#   stress        the same at 0.7 mm (z07), outside the rule
#   recal         recalibrated by ratio at 0.9 and 1.1 mm: the same with --alpha-json recal_curve_u50_L008_z<ZZ>.json
#                 --alpha-mode ratio --suffix +recal_ratio: every plane of the trained bank times alpha / alpha_ref of
#                 the file (the alpha found on the 32 unlabelled validation holograms at the new distance over the one
#                 found on the same ids at 1.0 mm, d2), gallery and threshold of 1.0 mm, as the recalibrated row of the
#                 layer `prop` (one call per distance: each has its own json)
#   recal_stress  the same at 0.7 mm
#   rep           the six steps of repetition REP, in order
#   table         scripts/exp_resolucao/banks_distance.py -> banks_distance.csv, banks_distance_rows.csv (no GPU)
# Rows go to results_exp_resolucao/robustness_curve_u50_L008_banks_<bank>.csv (one file per bank, so that the queues
# of two banks never write the same file; robustness_curve_u50_L008_bank_jit.csv of test J is never rewritten).
# Each test is read once per model: a step whose rows exist does nothing. Log logs/exp_resolucao/J2_<bank>_<step>_r<rep>.log.
set -e -o pipefail
cd "$(dirname "$0")/../.."
source scripts/exp_resolucao/env.sh
GPU=$1; STEP=$2
[ -n "$GPU" ] && [ -n "$STEP" ] || { sed -n '2,29p' "$0"; exit 1; }
SET=curve_u50_L008
ROBUST=curve_u50_robust
BANK=${BANK:-}
case "$BANK" in bank_jit|bank_wide|bank_w2|bank_w3) ;; *) [ "$STEP" = table ] || { echo "BANK?"; exit 1; } ;; esac
REP=${REP:-1}
case "$REP" in 1|2|3|4|5) ;; *) echo "REP must be 1-5"; exit 1 ;; esac
OUTCSV=robustness_curve_u50_L008_banks_$BANK
LOG=logs/exp_resolucao/J2_${BANK:-all}_${STEP}_r$REP.log
mkdir -p logs/exp_resolucao
py() { echo "+ $(date '+%F %T') python -m holo_openset $*"; python -m holo_openset "$@"; }
# rows (variant, flow name) of this repetition in this bank's csv, or, for bank_jit r1 as is, in the csv of test J
have_rows() {
  python -c "import sys, pandas as pd, pathlib
R = pathlib.Path('$HOLO_RESULTS'); flow = sys.argv[1]
files = [R / '$OUTCSV.csv'] + ([R / 'robustness_curve_u50_L008_bank_jit.csv'] if '$BANK' == 'bank_jit' and flow == 'bank_jit' else [])
have = set()
for p in files:
    if p.exists():
        t = pd.read_csv(p); t = t[t.rep == $REP]; have |= set(zip(t.variant, t.flow))
sys.exit(0 if {(v, flow) for v in sys.argv[2:]} <= have else 1)" "$@"
}
asis() {
  have_rows $BANK "$@" && { echo "rows exist ($BANK r$REP as is: $*)"; return 0; }
  echo "+ $(date '+%F %T') experiment robustness --variants $* --flows $BANK --rep $REP (as is)"
  python -m holo_openset experiment robustness --set $SET --variants-root $ROBUST --variants "$@" \
         --flows $BANK --rep $REP --out $OUTCSV --device cuda:$GPU --threads 4
}
recal() {
  for V in "$@"; do
    have_rows $BANK+recal_ratio $V && { echo "rows exist ($BANK r$REP recal_ratio: $V)"; continue; }
    J=$HOLO_RESULTS/recal_${SET}_$V.json
    echo "+ $(date '+%F %T') experiment robustness --variants $V --flows $BANK --rep $REP --alpha-json $J (ratio)"
    python -m holo_openset experiment robustness --set $SET --variants-root $ROBUST --variants $V \
           --flows $BANK --rep $REP --out $OUTCSV --alpha-json $J --alpha-mode ratio --suffix +recal_ratio \
           --device cuda:$GPU --threads 4
  done
}

{
echo "start $(date '+%F %T') gpu $GPU bank $BANK step $STEP rep $REP"
t0=$(date +%s)
case "$STEP" in
  train) py train --set $SET --flow $BANK --rep $REP --no-aux --alpha-extend 12 --device cuda:$GPU --threads 4 ;;
  evaluate)
    if [ -f $HOLO_RESULTS/eval/$SET/${BANK}_r$REP.json ]; then echo "exists ${BANK}_r$REP.json"
    else py evaluate --set $SET --flow $BANK --rep $REP --device cuda:$GPU --threads 4; fi ;;
  shifted) asis z09 z11 ;;
  stress) asis z07 ;;
  recal) recal z09 z11 ;;
  recal_stress) recal z07 ;;
  rep) for S in train evaluate shifted stress recal recal_stress; do
         BANK=$BANK REP=$REP bash "$0" $GPU $S > /dev/null || exit 1; done ;;
  table) python scripts/exp_resolucao/banks_distance.py ;;
  *) echo "unknown step $STEP"; exit 1 ;;
esac
echo "end $(date '+%F %T') wall_s $(( $(date +%s) - t0 ))"
} 2>&1 | tee -a $LOG
