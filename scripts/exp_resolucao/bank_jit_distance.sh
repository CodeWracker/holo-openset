#!/bin/bash
# Test J of the curve stage (docs/exp_resolucao/CADERNO_CURVA.md, Q2 section J; executor notebook
# CADERNO_CURVA_DISTANCIA.md, D3): the focal stack of the paper (`bank_jit`: five propagations over +-5 % of alpha,
# a 5 % distance jitter in training; flows.FLOWS, no hyperparameter changed) trained on the sparse level of the
# standard family, r1 only, and tested AS IS (model, gallery and threshold of 1.0 mm; no recalibration) at 1.0 mm
# and on the d2 recordings at 0.9 and 1.1 mm (0.7 mm apart, as stress, outside the rule):
#   bash scripts/exp_resolucao/bank_jit_distance.sh <physical GPU> <step>
#   train      python -m holo_openset train --set curve_u50_L008 --flow bank_jit --rep 1 --no-aux --alpha-extend 12
#              (the paper: `train --flow bank_jit --rep r`, pipeline.py; --no-aux as every 1 mm set; the calibration
#              grid extended 12 steps as the layer `prop` of the family, density_curve.sh) -> models_exp_resolucao/
#              curve_u50_L008/bank_jit_r1.pt (skipped when it exists: the resume)
#   evaluate   evaluate --set curve_u50_L008 --flow bank_jit --rep 1 -> results_exp_resolucao/eval/curve_u50_L008/
#              bank_jit_r1.json (the 1.0 mm row; skipped when it exists)
#   shifted    experiment robustness --set curve_u50_L008 --variants-root curve_u50_robust --variants z09 z11
#              --flows bank_jit --rep 1 (the procedure of the as-is rows of d2, robust_a of distance_tests.sh; the
#              test patterns of the holograms recorded at 0.9 / 1.1 mm) -> robustness_curve_u50_L008_bank_jit.csv
#   stress     the same for z07 (0.7 mm, outside the rule) -> the same csv
#   table      scripts/exp_resolucao/bank_jit_distance.py -> bank_jit_distance.csv (no GPU)
# Each test is read once: a step whose rows exist does nothing. Log logs/exp_resolucao/bankjit_<step>.log.
set -e
cd "$(dirname "$0")/../.."
source scripts/exp_resolucao/env.sh
GPU=$1; STEP=$2
[ -n "$GPU" ] && [ -n "$STEP" ] || { sed -n '2,23p' "$0"; exit 1; }
SET=curve_u50_L008
ROBUST=curve_u50_robust
OUTCSV=robustness_curve_u50_L008_bank_jit
LOG=logs/exp_resolucao/bankjit_${STEP}.log
mkdir -p logs/exp_resolucao
py() { echo "+ $(date '+%F %T') python -m holo_openset $*"; python -m holo_openset "$@"; }
have_rows() {
  python -c "import sys, pandas as pd, pathlib; p = pathlib.Path('$HOLO_RESULTS/$OUTCSV.csv')
t = pd.read_csv(p) if p.exists() else None
need = {(v, 'bank_jit') for v in sys.argv[1:]}
sys.exit(0 if t is not None and need <= set(zip(t[t.rep == 1].variant, t[t.rep == 1].flow)) else 1)" "$@"
}
shifted() {
  have_rows "$@" && { echo "rows exist ($*)"; return 0; }
  echo "+ $(date '+%F %T') experiment robustness --set $SET --variants-root $ROBUST --variants $* --flows bank_jit"
  python -m holo_openset experiment robustness --set $SET --variants-root $ROBUST --variants "$@" \
         --flows bank_jit --rep 1 --out $OUTCSV --device cuda:$GPU --threads 4
}

{
echo "start $(date '+%F %T') gpu $GPU step $STEP"
t0=$(date +%s)
case "$STEP" in
  train) py train --set $SET --flow bank_jit --rep 1 --no-aux --alpha-extend 12 --device cuda:$GPU --threads 4 ;;
  evaluate)
    if [ -f $HOLO_RESULTS/eval/$SET/bank_jit_r1.json ]; then echo "exists bank_jit_r1.json"
    else py evaluate --set $SET --flow bank_jit --rep 1 --device cuda:$GPU --threads 4; fi ;;
  shifted) shifted z09 z11 ;;
  stress) shifted z07 ;;
  table) python scripts/exp_resolucao/bank_jit_distance.py ;;
  *) echo "unknown step $STEP"; exit 1 ;;
esac
echo "end $(date '+%F %T') wall_s $(( $(date +%s) - t0 ))"
} 2>&1 | tee -a $LOG
