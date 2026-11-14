#!/bin/bash
# P2 / B, the reference of the code control: the base set as it is on disk (data/realistic: old recorder, old scene,
# 19.25 mm) trained now in r1 with the recipe of the pilot (--no-aux): raw, prop (the default calibration grid of
# alpha: 19.25 mm is inside it), rec_z0 (reads data/realistic/rec_z0.npy, which exists); evaluated in r1.
# Models -> models_exp_resolucao/realistic/, results -> results_exp_resolucao/eval/realistic/. The script refuses to
# run if the environment would point them to the paper's models/ or results/, or if a target file exists.
#   bash scripts/exp_resolucao/reference_noaux.sh <physical GPU>
# Log: logs/exp_resolucao/reference_noaux.log
set -e
cd "$(dirname "$0")/../.."
source scripts/exp_resolucao/env.sh
GPU=$1
[ -n "$GPU" ] || { sed -n '2,8p' "$0"; exit 1; }
LOG=logs/exp_resolucao/reference_noaux.log
py() { echo "+ $(date '+%F %T') python -m holo_openset $*"; python -m holo_openset "$@"; }
{
echo "start $(date '+%F %T') gpu $GPU"
python - <<'PY'
from holo_openset import paths
targets = [paths.weights(f, 1, 'realistic') for f in ('raw', 'prop', 'rec_z0')] + \
          [paths.RESULTS / 'eval' / 'realistic' / f'{f}_r1.json' for f in ('raw', 'prop', 'rec_z0')]
for t in targets:
    print('target', t)
assert paths.MODELS.name == 'models_exp_resolucao' and paths.RESULTS.name == 'results_exp_resolucao', 'paper folders'
assert not any(t.exists() for t in targets), 'a target exists'
PY
t0=$(date +%s)
py train --set realistic --flow raw --rep 1 --no-aux --device cuda:$GPU --threads 4
py train --set realistic --flow prop --rep 1 --no-aux --device cuda:$GPU --threads 4
py train --set realistic --flow rec_z0 --rep 1 --no-aux --device cuda:$GPU --threads 4
for F in raw prop rec_z0; do py evaluate --set realistic --flow $F --rep 1 --device cuda:$GPU --threads 4; done
echo "end $(date '+%F %T') wall_s $(( $(date +%s) - t0 ))"
} 2>&1 | tee -a $LOG
