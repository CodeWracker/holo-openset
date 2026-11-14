#!/bin/bash
# The reduced sets of the pilot (docs/exp_resolucao, T3-T4) and their back-propagation caches at the effective pixel.
# Resumable: a set whose physics.json exists is not reduced again, a cache whose autofocus log exists is not rebuilt.
#   bash scripts/exp_resolucao/build_sets.sh <physical GPU> [b ...]      (default b: 1 2 4 8)
# b = 1 is the identity check (data/realistic_b1 against data/realistic) and gives the validation recordings of the
# variants a place for their cache (data/variants_val_b1: the paper's variants_val have none); its test variants are
# the paper's (data/variants/<v>, which have their cache).
set -e
cd "$(dirname "$0")/../.."
source scripts/exp_resolucao/env.sh
GPU=$1; shift
BS=${@:-1 2 4 8}
TIMEFORMAT='  %R s'
py() { echo "+ $(date '+%F %T') python -m holo_openset $*"; time python -m holo_openset "$@"; }
for b in $BS; do
  [ -f data/realistic_b$b/physics.json ] || py reduce --set realistic --bin $b --aux r1
  for v in fullwell_500 beam_narrow; do
    [ "$b" = 1 ] || [ -f data/variants_b$b/$v/physics.json ] || py reduce --set variants/$v --bin $b
    [ -f data/variants_val_b$b/$v/physics.json ] || py reduce --set variants_val/$v --bin $b
  done
done
for b in $BS; do
  [ -f data/realistic_b$b/autofocus.csv ] || py reconstruct --set realistic_b$b --methods z0 --device cuda:$GPU
  [ "$b" = 1 ] || [ -f data/realistic_b$b/aux/r1_autofocus.csv ] || \
    py reconstruct --set realistic_b$b --aux r1 --methods z0 --device cuda:$GPU
  for v in fullwell_500 beam_narrow; do
    [ "$b" = 1 ] || [ -f data/variants_b$b/$v/autofocus.csv ] || \
      py reconstruct --set variants_b$b/$v --methods z0 --device cuda:$GPU
    [ -f data/variants_val_b$b/$v/autofocus.csv ] || py reconstruct --set variants_val_b$b/$v --methods z0 --device cuda:$GPU
  done
done
echo "done $(date '+%F %T')"
