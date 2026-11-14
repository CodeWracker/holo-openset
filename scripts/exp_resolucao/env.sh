# Environment of the source-resolution study (docs/exp_resolucao). Source it from the root of the repository:
#   source scripts/exp_resolucao/env.sh
# New results never touch results/ (the csv behind the tables of the paper): they go to results_exp_resolucao/.
# New models never touch models/ (the models of the paper): they go to models_exp_resolucao/. The b = 1 reference IS
# the paper's r1 models: evaluate it with HOLO_MODELS=$PWD/models on the command line (read only; nothing is trained
# at b = 1).
export HOLO_RESULTS=$PWD/results_exp_resolucao
export HOLO_MODELS=$PWD/models_exp_resolucao
export HOLO_LOGS=$PWD/logs/exp_resolucao
# The server reports 224 CPUs: every library is held to a few threads per process.
for v in OMP_NUM_THREADS OPENBLAS_NUM_THREADS MKL_NUM_THREADS NUMEXPR_NUM_THREADS NUMEXPR_MAX_THREADS \
         OPENCV_FOR_THREADS_NUM NUMBA_NUM_THREADS POLARS_MAX_THREADS RAYON_NUM_THREADS; do
  export $v=${HOLO_THREADS:-4}
done
# The environment of the paper (requirements-lock.txt), when it is not the active one.
if [ -x "$PWD/../.envbuild/holo-openset/bin/python" ]; then export PATH=$PWD/../.envbuild/holo-openset/bin:$PATH; fi
export PYTHONUNBUFFERED=1
# The package is not installed in that environment: scripts import it from the repository.
export PYTHONPATH=$PWD${PYTHONPATH:+:$PYTHONPATH}
# Temporaries: never /tmp
export TMPDIR=/home/jovyan/privado/.persist/.cache/tmp/claude-1000/-home-jovyan-compartilhado-ralph-openset-microscopy/2460bd2f-62a2-4eb8-bda4-b04332eeb593/scratchpad/piloto
# reproduce check and pytest compare the tables of the PAPER: run them with HOLO_RESULTS unset
#   env -u HOLO_RESULTS -u HOLO_MODELS python -m pytest -q;  env -u HOLO_RESULTS -u HOLO_MODELS python -m holo_openset reproduce check
# (with HOLO_MODELS set, \\NModels counts the models of models_exp_resolucao instead of the paper's)
