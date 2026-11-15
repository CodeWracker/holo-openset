#!/bin/bash
# Depth rows of the curve stage, phase 2 (docs/exp_resolucao/CADERNO_CURVA.md Q1, "d2 e as linhas de profundidade";
# executor notebook CADERNO_CURVA_DISTANCIA.md), no criterion, r1-r5 each, models, gallery and threshold of the set
# the models were trained on, nothing retrained:
#   REP=1..5 bash scripts/exp_resolucao/depth_tests.sh <physical GPU> <step>
#   flat_on_u50    (i)   the five models of the pilot (bench_1mm, flat sample: 2.6 um) on the test split of
#                        curve_u50_L008 (the standard law: uniform over the 50 um channel)
#                        -> results_exp_resolucao/robustness_depth_from_bench_1mm.csv (variant curve_u50_L008)
#   u50_on_flat    (ii)  the five models of curve_u50_L008 on the test split of bench_1mm
#                        -> results_exp_resolucao/robustness_depth_from_curve_u50_L008.csv (variant bench_1mm)
#   u50_on_wide    (iii) the five models of curve_u50_L008 on the test split of the wide law (normal 50 um, cut at
#                        150 um): bench_1mm_robust/depth50 (the same 800 holograms as the test split of
#                        bench_1mm_depth50, checked) -> the same csv (variant depth50)
#   rep            the three of repetition REP
#   table          scripts/exp_resolucao/depth_tests.py -> depth_tests.csv, depth_tests_rows.csv (no GPU)
# The test sets are read where they are (their rec_z0.npy at the nominal 1.0 mm); nothing is written in data/.
# Rows that exist are not redone. Logs logs/exp_resolucao/depth_u50_<step>[_r<REP>].log.
set -e
cd "$(dirname "$0")/../.."
source scripts/exp_resolucao/env.sh
GPU=$1; STEP=$2
[ -n "$GPU" ] && [ -n "$STEP" ] || { sed -n '2,20p' "$0"; exit 1; }
FLAT=bench_1mm
U50=curve_u50_L008
REP=${REP:-1}
case "$REP" in 1|2|3|4|5) ;; *) echo "REP must be 1-5"; exit 1 ;; esac
LOG=logs/exp_resolucao/depth_u50_${STEP}$([ "$REP" != 1 ] && echo _r$REP || true).log
mkdir -p logs/exp_resolucao
# rows of <csv> for this repetition and variant (raw, prop, rec_z0) exist already?
have_rows() {
  python -c "import sys, pandas as pd, pathlib; p = pathlib.Path('$HOLO_RESULTS/$1.csv')
t = pd.read_csv(p) if p.exists() else None
need = {('$2', f) for f in ('raw', 'prop', 'rec_z0')}
sys.exit(0 if t is not None and need <= set(zip(t[t.rep == $REP].variant, t[t.rep == $REP].flow)) else 1)"
}
# <trained set> <variants root> <variant>
cross() {
  local OUT=robustness_depth_from_$1
  have_rows $OUT $3 && { echo "rows of r$REP exist ($OUT, $3)"; return 0; }
  for d in data/$2/$3; do
    python -c "import json; p = json.load(open('$d/physics.json'))['physics']; print('$d', 'z0', p['z0'],
               {k: v for k, v in p.items() if 'depth' in k})"
  done
  echo "+ $(date '+%F %T') experiment robustness --set $1 --variants-root $2 --variants $3 rep $REP"
  python -m holo_openset experiment robustness --set $1 --variants-root $2 --variants $3 \
         --flows raw prop rec_z0 --rep $REP --out $OUT --device cuda:$GPU --threads 4
}

{
echo "start $(date '+%F %T') gpu $GPU step $STEP rep $REP"
t0=$(date +%s)
case "$STEP" in
  flat_on_u50) cross $FLAT . $U50 ;;
  u50_on_flat) cross $U50 . $FLAT ;;
  u50_on_wide) cross $U50 bench_1mm_robust depth50 ;;
  rep) for S in flat_on_u50 u50_on_flat u50_on_wide; do REP=$REP bash "$0" $GPU $S > /dev/null; done ;;
  table) python scripts/exp_resolucao/depth_tests.py ;;
  *) echo "unknown step $STEP"; exit 1 ;;
esac
echo "end $(date '+%F %T') wall_s $(( $(date +%s) - t0 ))"
} 2>&1 | tee -a $LOG
