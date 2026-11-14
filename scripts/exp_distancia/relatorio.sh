#!/usr/bin/env bash
# Tables, macros and figures of the distance study, and the copies the protocol and the report read. From the root of
# the repository:   bash scripts/exp_distancia/relatorio.sh
#   1. python -m holo_openset paper distance  -> results_exp_distancia/distance/{tables,figures,numbers_distancia.tex}
#   2. results_exp_distancia/distance/numbers_distancia.tex -> results_exp_distancia/numbers_distancia.tex (protocol 9.4)
#   3. results_exp_distancia/distance/figures/*.png         -> docs/exp_distancia/img/ (figures of RELATORIO.md)
# Reads only the csv files of results_exp_distancia/ (timing session: e5/); runs nothing on a GPU.
set -euo pipefail
cd "$(dirname "$0")/../.."
source scripts/exp_distancia/env.sh
export HOLO_PAPER=$PWD/results_exp_distancia
python -m holo_openset paper distance
cp results_exp_distancia/distance/numbers_distancia.tex results_exp_distancia/numbers_distancia.tex
mkdir -p docs/exp_distancia/img
cp results_exp_distancia/distance/figures/fig_dist_*.png docs/exp_distancia/img/
echo "copied numbers_distancia.tex and $(ls results_exp_distancia/distance/figures/fig_dist_*.png | wc -l) figures"
