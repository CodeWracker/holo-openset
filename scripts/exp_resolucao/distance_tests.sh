#!/bin/bash
# Distance tests of the curve stage, round d1 (docs/exp_resolucao/CADERNO_CURVA.md, Q0 item d; executor notebook
# CADERNO_CURVA_DISTANCIA.md): the five models of the pilot (bench_1mm, trained at 1.0 mm) on the test split recorded
# again at another distance, as is and recalibrated without labels. The steps are those of 0.7 mm in pilot_1mm.sh
# (record_07, robust_a, robust_b), with the distance as a parameter:
#   ZROB=09|11 [REP=1..5] bash scripts/exp_resolucao/distance_tests.sh <physical GPU> <step>
# 0.7 mm is NOT run here: its sets, rows and json exist and stay those of pilot_1mm.sh (ZROB=07 is refused).
# Round d2 (CADERNO_CURVA.md Q1): FAM=u50 runs the same steps on the five models of the sparse level of the standard
# family (curve_u50_L008: depth uniform over the 50 um channel) at ZROB=07|09|11, the recordings inheriting the
# physics of that set (only z0 changes): data/curve_u50_robust/z<ZROB>[_val], rows in
# robustness_curve_u50_L008_dist.csv, recal_curve_u50_L008_z<ZROB>.json, distance_checks_u50_z<ZROB>.json, table
# distance_tests_u50.csv (distance_tests.py --family u50), logs dist_u50_<step>_z<ZROB>[_r<REP>].log.
# FAM=pilot (the default) is round d1, unchanged.
# Steps (each one skips what exists; log logs/exp_resolucao/dist_<step>_z<ZROB>[_r<REP>].log with start, end, seconds):
#   record     the test and validation splits of bench_1mm recorded again at z0 = ZROB/10 mm, exactly as record_07
#              (simulate like: same scenes, seeds, sessions, camera and recorder; the session distance keeps its
#              relative spread, z_s = z0 (1 + 0.005 N(0, 1)), with the same draws): data/bench_1mm_robust/z<ZROB>
#              (test) and data/bench_1mm_robust/z<ZROB>_val (validation)
#   checks     scripts/exp_resolucao/distance_checks.py on both splits against bench_1mm
#              -> results_exp_resolucao/distance_checks_z<ZROB>.json
#   robust_a   as is: rec_z0 of the test split back-propagated at 1.0 mm (the nominal z0 of bench_1mm), models, gallery
#              and threshold of bench_1mm -> rows z<ZROB> raw, prop, rec_z0 of results_exp_resolucao/
#              robustness_bench_1mm_dist.csv (a file of its own: robustness_bench_1mm.csv, which holds the 0.7 mm
#              rows, is never rewritten)
#   robust_b   recalibrated without labels on 32 holograms of the validation split at that distance
#              (recalibrate_distance.py, grid extended 12 steps: 0.485-75.5 mm) -> recal_bench_1mm_z<ZROB>.json;
#              literal (the recalibrated alpha replaces the trained one; rec_z0 at the recalibrated z, _recal) and by
#              ratio (the trained alpha times alpha / alpha_ref; rec_z0 at 1.0 mm times the ratio, _recal_ratio)
#              -> rows prop+recal, rec_z0+recal, prop+recal_ratio, rec_z0+recal_ratio
#   rep        robust_a and robust_b of repetition REP
#   table      scripts/exp_resolucao/distance_tests.py -> distance_tests.csv, distance_tests_rows.csv (no GPU)
set -e
cd "$(dirname "$0")/../.."
source scripts/exp_resolucao/env.sh
GPU=$1; STEP=$2
[ -n "$GPU" ] && [ -n "$STEP" ] || { sed -n '2,35p' "$0"; exit 1; }
FAM=${FAM:-pilot}
case "$FAM" in
  pilot) SET=bench_1mm; ROBUST=bench_1mm_robust; OUTCSV=robustness_bench_1mm_dist; CHK=distance_checks; LP=dist ;;
  u50) SET=curve_u50_L008; ROBUST=curve_u50_robust; OUTCSV=robustness_curve_u50_L008_dist; CHK=distance_checks_u50
       LP=dist_u50 ;;
  *) echo "FAM must be pilot or u50"; exit 1 ;;
esac
WORKERS=3          # scene builders (PIL, one thread each), as record_07
REP=${REP:-1}
case "$REP" in 1|2|3|4|5) ;; *) echo "REP must be 1-5"; exit 1 ;; esac
ZROB=${ZROB:-}
case "$ZROB" in
  09) ZM=0.9e-3 ;;
  11) ZM=1.1e-3 ;;
  07) if [ "$FAM" = u50 ]; then ZM=0.7e-3; else
      echo "0.7 mm is pilot_1mm.sh (record_07, robust_a, robust_b): its files exist and are not redone"; exit 1; fi ;;
  *) if [ "$STEP" = table ]; then ZROB=all; else echo "ZROB must be 09 or 11"; exit 1; fi ;;
esac
V=z$ZROB
LOG=logs/exp_resolucao/${LP}_${STEP}_z${ZROB}$([ "$REP" != 1 ] && echo _r$REP || true).log
mkdir -p logs/exp_resolucao
py() { echo "+ $(date '+%F %T') python -m holo_openset $*"; python -m holo_openset "$@"; }
# rows of robustness_bench_1mm_dist.csv for this repetition, variant and flows exist already?
have_rows() {
  python -c "import sys, pandas as pd, pathlib; p = pathlib.Path('$HOLO_RESULTS/$OUTCSV.csv')
t = pd.read_csv(p) if p.exists() else None
need = {('$1', f) for f in sys.argv[1:]}
sys.exit(0 if t is not None and need <= set(zip(t[t.rep == $REP].variant, t[t.rep == $REP].flow)) else 1)" "${@:2}"
}

{
echo "start $(date '+%F %T') gpu $GPU family $FAM set $SET step $STEP z $ZROB rep $REP"
python -c "from holo_openset import paths; print('data', paths.DATA, 'results', paths.RESULTS, 'models', paths.MODELS)"
t0=$(date +%s)
case "$STEP" in
  record)
    for SP in test val; do
      if [ $SP = val ]; then OUT=$ROBUST/${V}_val; else OUT=$ROBUST/$V; fi
      [ -f data/$OUT/physics.json ] || py simulate like --like $SET --name $OUT --split $SP --set-physics z0=$ZM \
                                          --device cuda:$GPU --workers $WORKERS
    done
    ;;
  checks)
    J=$HOLO_RESULTS/${CHK}_$V.json
    [ -f $J ] && { echo "exists $J"; exit 0; }
    python scripts/exp_resolucao/distance_checks.py --sets $ROBUST/$V $ROBUST/${V}_val --ref $SET --z0 $ZM \
           --out $J --device cuda:$GPU
    ;;
  robust_a)
    Z_SET=$(python -c "import json; print(json.load(open('data/$SET/physics.json'))['physics']['z0'])")
    [ -f data/$ROBUST/$V/autofocus.csv ] || py reconstruct --set $ROBUST/$V --methods z0 --z0 $Z_SET --device cuda:$GPU
    have_rows $V raw prop rec_z0 && { echo "rows of r$REP exist"; exit 0; }
    python -m holo_openset experiment robustness --set $SET --variants-root $ROBUST --variants $V \
           --flows raw prop rec_z0 --rep $REP --out $OUTCSV --device cuda:$GPU --threads 4
    ;;
  robust_b)
    J=$HOLO_RESULTS/recal_${SET}_$V.json
    [ -f $J ] || python scripts/exp_resolucao/recalibrate_distance.py --set $ROBUST/${V}_val --ref $SET --n 32 \
                   --extend 12 --out $J --device cuda:$GPU
    Z=$(python scripts/exp_resolucao/recalibrate_distance.py --read $J z)
    [ -f data/$ROBUST/$V/autofocus_recal.csv ] || \
      py reconstruct --set $ROBUST/$V --methods z0 --z0 $Z --tag _recal --device cuda:$GPU
    have_rows $V prop+recal rec_z0+recal || \
    python -m holo_openset experiment robustness --set $SET --variants-root $ROBUST --variants $V \
           --flows prop rec_z0 --rep $REP --out $OUTCSV --alpha-json $J --rec-tag _recal \
           --device cuda:$GPU --threads 4
    ZR=$(python scripts/exp_resolucao/recalibrate_distance.py --read $J z_ratio)
    [ -f data/$ROBUST/$V/autofocus_recal_ratio.csv ] || \
      py reconstruct --set $ROBUST/$V --methods z0 --z0 $ZR --tag _recal_ratio --device cuda:$GPU
    have_rows $V prop+recal_ratio rec_z0+recal_ratio || \
    python -m holo_openset experiment robustness --set $SET --variants-root $ROBUST --variants $V \
           --flows prop rec_z0 --rep $REP --out $OUTCSV --alpha-json $J --alpha-mode ratio \
           --rec-tag _recal_ratio --suffix +recal_ratio --device cuda:$GPU --threads 4
    ;;
  rep)
    for S in robust_a robust_b; do FAM=$FAM ZROB=$ZROB REP=$REP bash "$0" $GPU $S > /dev/null; done
    ;;
  table)
    if [ "$FAM" = u50 ]; then python scripts/exp_resolucao/distance_tests.py --family u50
    else python scripts/exp_resolucao/distance_tests.py; fi
    ;;
  *) echo "unknown step $STEP"; exit 1 ;;
esac
echo "end $(date '+%F %T') wall_s $(( $(date +%s) - t0 ))"
} 2>&1 | tee -a $LOG
