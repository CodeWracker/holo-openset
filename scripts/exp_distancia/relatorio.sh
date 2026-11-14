#!/usr/bin/env bash
# Tables, macros and figures of the distance study, and the copies the protocol and the report read. From the root of
# the repository:   bash scripts/exp_distancia/relatorio.sh
#   1. python -m holo_openset paper distance  -> results_exp_distancia/distance/{tables,figures,numbers_distancia.tex}
#      and results_exp_distancia/numbers_distancia.tex (protocol 9.4; the generator writes it next to its HOLO_PAPER)
#   2. results_exp_distancia/distance/figures/*.png         -> docs/exp_distancia/img/ (figures of RELATORIO.md)
# Reads only the csv files of results_exp_distancia/ (the generator's default; timing session: e5/); runs nothing on a
# GPU. The paper takes the same macros with `python -m holo_openset paper distance` into its own HOLO_PAPER.
set -euo pipefail
cd "$(dirname "$0")/../.."
source scripts/exp_distancia/env.sh
export HOLO_PAPER=$PWD/results_exp_distancia
python -m holo_openset paper distance
mkdir -p docs/exp_distancia/img
cp results_exp_distancia/distance/figures/fig_dist_*.png docs/exp_distancia/img/
echo "wrote numbers_distancia.tex and copied $(ls results_exp_distancia/distance/figures/fig_dist_*.png | wc -l) figures"
