# Environment of the distance/autofocus experiments (docs/exp_distancia). Source it from the root of the repository:
#   source scripts/exp_distancia/env.sh
# New results never touch results/ (the csv behind the tables of the paper): they go to results_exp_distancia/.
export HOLO_RESULTS=$PWD/results_exp_distancia
export HOLO_LOGS=$PWD/logs/exp_distancia
# The server reports 224 CPUs: every library is held to a few threads per process.
for v in OMP_NUM_THREADS OPENBLAS_NUM_THREADS MKL_NUM_THREADS NUMEXPR_NUM_THREADS NUMEXPR_MAX_THREADS \
         OPENCV_FOR_THREADS_NUM NUMBA_NUM_THREADS POLARS_MAX_THREADS RAYON_NUM_THREADS; do
  export $v=${HOLO_THREADS:-4}
done
# The environment of the paper (requirements-lock.txt), when it is not the active one.
if [ -x "$PWD/../.envbuild/holo-openset/bin/python" ]; then export PATH=$PWD/../.envbuild/holo-openset/bin:$PATH; fi
export PYTHONUNBUFFERED=1
