"""Where the pipeline reads and writes, relative to the repository unless an environment variable says otherwise.
Data and models stay out of git; results (csv, json) are small and versioned; expected/ is the snapshot of the tables
and numbers of the paper that `python -m holo_openset reproduce` compares against."""
import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get('HOLO_DATA', PROJECT / 'data'))
MODELS = Path(os.environ.get('HOLO_MODELS', PROJECT / 'models'))
RESULTS = Path(os.environ.get('HOLO_RESULTS', PROJECT / 'results'))
LOGS = Path(os.environ.get('HOLO_LOGS', PROJECT / 'logs'))
EXPECTED = PROJECT / 'expected'
CHECKSUMS = PROJECT / 'checksums'
PARTITIONS = Path(__file__).resolve().parent / 'partitions'
PAPER = Path(os.environ.get('HOLO_PAPER', PROJECT / 'output/paper'))

BASE = 'realistic'   # the dataset every result is reported on
IDEAL = 'ideal'      # the same scenes under the idealised model


def dataset(name):
    """data/<name>; variants are named 'variants/<variant>'."""
    return DATA / name


def weights(flow, rep, dataset_name=BASE, tag=''):
    return MODELS / dataset_name / f'{flow}{tag}_r{rep}.pt'


def yolo_weights(rep, dataset_name=BASE):
    return MODELS / dataset_name / f'yolo_r{rep}.pt'
