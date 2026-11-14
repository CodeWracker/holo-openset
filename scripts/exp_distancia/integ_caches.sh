#!/bin/bash
# Integration of the distance study into the paper (docs/exp_distancia/CADERNO_INTEGRACAO.md, step 2): reconstruction
# caches of a set without touching any file of the set that exists.
#   bash scripts/exp_distancia/integ_caches.sh cuda:N <set under data/> <method> ...    (repository root, in tmux)
# Methods of reconstruct.FOCUS (afc) write only rec_<m>.npy and autofocus_<m>.csv: they run on the set itself, unless
# one of those files exists. Methods of the paper (z0 af edf twin) always rewrite autofocus.csv: they run with the same
# command on a staging copy (data/_integ_staging/<set>, symbolic links to the inputs); the new rec_<m>.npy are moved
# into the set (never over an existing file) and the staging autofocus.csv is compared with the set's one.
set -e
source scripts/exp_distancia/env.sh
unset HOLO_RESULTS
export HOLO_LOGS=$PWD/logs/integracao
DEV=$1; SET=$2; shift 2
D=data/$SET
stamp() { echo "== $(date '+%F %T') | $(uptime | sed 's/.*load/load/') | ready threads $(ps -eLo stat= | grep -c '^R')"; }
focus=(); paper=()
for m in "$@"; do
  if [ -e $D/rec_$m.npy ]; then echo "exists $D/rec_$m.npy: skipped"; continue; fi
  case $m in z0|af|edf|twin) paper+=($m);; *) focus+=($m);; esac
done
for m in "${focus[@]}"; do
  if [ -e $D/autofocus_$m.csv ]; then echo "exists $D/autofocus_$m.csv without rec_$m.npy: stop"; exit 1; fi
done
if [ ${#focus[@]} -gt 0 ]; then
  stamp; echo "reconstruct --set $SET --methods ${focus[*]}"
  python -m holo_openset reconstruct --set $SET --methods "${focus[@]}" --device $DEV
fi
if [ ${#paper[@]} -gt 0 ]; then
  ST=data/_integ_staging/$SET
  if [ -e $ST ]; then echo "staging $ST exists (an interrupted run?): remove it by hand after checking"; exit 1; fi
  mkdir -p $ST
  for f in holograms.npy backgrounds.npy metadata.csv annotations.csv physics.json sessions.csv dust.csv; do
    [ -e $D/$f ] && ln -s $(realpath $D/$f) $ST/$f
  done
  stamp; echo "reconstruct --set _integ_staging/$SET --methods ${paper[*]}"
  python -m holo_openset reconstruct --set _integ_staging/$SET --methods "${paper[@]}" --device $DEV
  if [ -e $D/autofocus.csv ]; then   # edf adds a column z_objects: compare the columns both logs have
    python - $ST/autofocus.csv $D/autofocus.csv <<'EOF'
import sys
import pandas as pd
a, b = pd.read_csv(sys.argv[1]), pd.read_csv(sys.argv[2])
c = [k for k in b.columns if k in a.columns]
same = len(a) == len(b) and (a[c].astype(str).values == b[c].astype(str).values).all()
print(f'autofocus.csv of the staging copy against the set, columns {c}:', 'identical' if same else 'DIFFERENT',
      f'(largest |z_af difference| {(a.z_af - b.z_af).abs().max() if len(a) == len(b) else "n/a"})')
EOF
  fi
  mkdir -p $HOLO_LOGS/staging_autofocus
  cp $ST/autofocus.csv $HOLO_LOGS/staging_autofocus/$(echo $SET | tr / _)_$(IFS=_; echo "${paper[*]}").csv
  for m in "${paper[@]}"; do
    if [ -e $D/rec_$m.npy ]; then echo "$D/rec_$m.npy appeared meanwhile: left in $ST"; exit 1; fi
    mv -n $ST/rec_$m.npy $D/rec_$m.npy && echo "moved rec_$m.npy into $D"
  done
  rm $ST/autofocus.csv; find $ST -type l -delete; rmdir $ST; rmdir -p $(dirname $ST) 2>/dev/null || true
fi
stamp; echo "done $SET"
