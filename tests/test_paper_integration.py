"""The distance study inside the paper: the results the two share agree, the paper's tables carry the narrow autofocus
and the sets whose distance changes per image, and the study's macros are assets of the paper (docs/exp_distancia).

Run with HOLO_RESULTS unset, so that the tables read results/ (the results of the paper)."""
import re

import numpy as np
import pandas as pd
import pytest

from holo_openset import paths

STUDY = paths.PROJECT / 'results_exp_distancia'
NEW_SETS = ['frame_2', 'frame_5', 'walk_05']


def _differences(a, b, keys, skip=()):
    """Rows of a and b with the same keys, and the largest |difference| of each numeric column they share."""
    m = a.merge(b, on=keys, suffixes=('_a', '_b'))
    cols = [c[:-2] for c in m.columns if c.endswith('_a') and c[:-2] not in skip and f'{c[:-2]}_b' in m
            and pd.api.types.is_numeric_dtype(m[c]) and pd.api.types.is_numeric_dtype(m[f'{c[:-2]}_b'])]
    d = {c: float(np.nanmax(np.abs(m[f'{c}_a'].to_numpy(float) - m[f'{c}_b'].to_numpy(float)))) if len(m) else 0.0
         for c in cols}
    return m, d


def _csv(root, name):
    f = root / f'{name}.csv'
    if not f.exists():
        pytest.skip(f'{f} not there')
    return pd.read_csv(f)


# ------------------------------------------------------------------------------------ (a)-(c): the shared results
# Robustness rows computed by both on the same files in this build (the three new sets, and the narrow autofocus, run
# for the paper on the sets and caches of this build): identical up to the rounding of a csv round trip.
FLOAT_NOISE = 1e-12
# The other shared rows (base, session_2, session_5, fullwell_500, beam_narrow) are not computed on the same files: the
# study re-simulated those variants and rebuilt the reconstruction caches of the base set in this build, while the
# rows of the paper come from the published sets and caches (another build). Measured on 2026-11-14: at most 0.0055 on
# any metric (enrollment), 0.0023 on the open-set F1, over 150 rows; 0 for the hologram flows on the base set.
OTHER_BUILD = 0.01


def test_robustness_rows_shared_with_the_study_agree():
    paper, study = _csv(paths.PROJECT / 'results', 'robustness'), _csv(STUDY, 'robustness')
    m, d = _differences(paper, study, ['rep', 'variant', 'flow'], skip=('value',))
    assert m.variant.isin(NEW_SETS).sum() >= 75   # rec_z0, rec_af, rec_afc, prop, bank_jit x 3 sets x 5 repetitions

    def same(df):
        return df[df.variant.isin(NEW_SETS) | (df.flow == 'rec_afc')]
    _, d_same = _differences(same(paper), same(study), ['rep', 'variant', 'flow'], skip=('value',))
    assert max(d_same.values()) <= FLOAT_NOISE, d_same
    assert max(d.values()) <= OTHER_BUILD, d


# Full frames: the same published frames and models in both, and the detector run again by each experiment. On this
# build two runs of the study gave identical files (E1 and the second attempt of the timing session); against the run
# of the paper (another build) the largest difference is 9e-5 on the F1 and 6.5e-4 on the rejection of the unseen.
# One false detection more or less (seen once when the detector of the windows was run again) moves fp_per_frame by
# 1/40 and fp_rejected by about 1/150 = 0.007 in that repetition, and the box-level metrics by well under 0.002.
FULL_TOL = {'fp_per_frame': 0.05, 'fp_rejected': 0.01}
FULL_TOL_DEFAULT = 0.002


def test_full_frames_shared_with_the_study_agree():
    paper, study = _csv(paths.PROJECT / 'results', 'full_frames'), _csv(STUDY, 'full_frames')
    if 'rec_afc' not in set(paper.flow):
        pytest.skip('results/full_frames.csv is not yet the run with every flow of the paper and the narrow autofocus')
    m, d = _differences(paper, study, ['rep', 'flow', 'boxes'], skip=('frames', 'letters'))
    assert {'rec_z0', 'rec_af', 'rec_afc', 'prop', 'bank_jit'} <= set(m.flow)
    far = {c: v for c, v in d.items() if v > FULL_TOL.get(c, FULL_TOL_DEFAULT)}
    assert not far, (far, d)


def test_stage_times_of_the_paper_are_the_timing_session_of_the_study():
    for dev in ['gpu', 'cpu']:
        a, b = paths.PROJECT / 'results' / f'timing_{dev}.csv', STUDY / 'e5' / f'timing_{dev}.csv'
        assert a.read_bytes() == b.read_bytes(), dev


# ------------------------------------------------------------------------------------ (d): the report and its macros
def test_every_macro_of_the_report_exists():
    from holo_openset.reproduce import macros
    have = macros(STUDY / 'numbers_distancia.tex')
    text = (paths.PROJECT / 'docs/exp_distancia/RELATORIO.md').read_text()
    cited = set(re.findall(r'\\(Dist[A-Za-z]+)(?![A-Za-z<]|\.\.\.)', text))   # not the families \\DistCrit<...>
    assert cited and not cited - set(have), sorted(cited - set(have))
    assert not [k for k in cited if have[k] == '?']


# ------------------------------------------------------------------------------------ (e): the tables of the paper
@pytest.fixture
def tables_out(tmp_path, monkeypatch):
    """The tables that change with the integration, written to tmp_path (results/ is only read)."""
    from holo_openset.paper import tables as T
    monkeypatch.setattr(paths, 'PAPER', tmp_path)
    T.M.clear()
    for fn in [T.tab_main, T.tab_stages, T.tab_robustness, T.tab_full_frames, T.focus_numbers]:
        fn()
    return tmp_path / 'tables', dict(T.M)


def _rows(f):
    return [ln for ln in f.read_text().splitlines() if '&' in ln]


def test_the_narrow_autofocus_is_a_flow_of_the_paper(tables_out):
    from holo_openset.paper import style, tables as T
    assert style.ORDER is T.ORDER and T.ORDER.index('rec_afc') == T.ORDER.index('rec_af') + 1
    for d in [T.NAME, T.NEEDS, style.COLORS, style.LABELS, style.SHORT]:
        assert 'rec_afc' in d
    assert T.NAME['rec_af'] == 'blind autofocus' and T.NAME['rec_afc'] == 'narrow autofocus'
    assert len(set(style.COLORS.values())) == len(style.COLORS)   # one colour per entity
    assert T.NEEDS['rec_afc'] == '$\\lambda,\\Delta,B,z_0{\\pm}13\\%$'
    rows = _rows(tables_out[0] / 'tab_main.tex')
    names = [r.split(' & ')[0] for r in rows]
    assert names.index('narrow autofocus') == names.index('blind autofocus') + 1
    assert rows[names.index('narrow autofocus')].count('--') == 0
    assert tables_out[1]['RecAfcFone'] != '?'


def test_the_stage_table_has_the_narrow_search(tables_out):
    names = [r.split(' & ')[0] for r in _rows(tables_out[0] / 'tab_stages.tex')]
    blind = names.index('blind autofocus (114 reconstructions)')
    assert names[blind + 1] == 'narrow autofocus (18 reconstructions of 1/16 of the pixels)'
    M = tables_out[1]
    for k in ['TAutofocusAfcGpuBigMs', 'TAutofocusAfcCpuBigS', 'TBlindOverNarrowGpuBig', 'TBlindOverNarrowCpuBig']:
        assert M[k] != '?', k
    assert (M['FocusBlindN'], M['FocusNarrowN'], M['FocusNarrowPixels'], M['FocusNarrowRangeEffPct']) == \
        ('114', '18', '16', '13')


def test_the_robustness_table_has_the_new_sets_and_column(tables_out):
    from holo_openset.paper.tables import ORDER, robustness_sets
    sets = robustness_sets()
    k = sets.index('session_5')
    assert sets[k + 1:k + 4] == NEW_SETS and sets[0] == 'base' and len(sets) == len(set(sets)) == 36
    rows = _rows(tables_out[0] / 'tab_robustness.tex')
    names = [r.split(' & ')[0] for r in rows]
    k = names.index('distance between sessions (\\%): 5')
    assert names[k + 1:k + 4] == ['distance per frame (\\%): 2', 'distance per frame (\\%): 5',
                                  'distance drift per frame (\\%): 0.5']
    assert all(r.rstrip(' \\').count(' & ') == len(ORDER) + 1 for r in rows)   # label, the flows, the oracle
    M = tables_out[1]
    for v in ['FrameTwo', 'FrameFive', 'WalkZeroFive']:
        assert M[f'Rob{v}RecZZero'] != '?' and M[f'Rob{v}RecAfc'] != '?'


def test_the_detector_share_is_quoted_over_the_flows_that_reconstruct_once(tables_out):
    from holo_openset.paper.tables import ONE_PASS
    M = tables_out[1]
    assert 'rec_af' not in ONE_PASS and 'rec_afc' in ONE_PASS
    shares = {k: float(v) for k, v in M.items() if k.startswith('FullDetectPct') and k[13:] and v != '?'
              and re.fullmatch(r'[0-9.]+', v) and not k.startswith('FullDetectPctMin')}
    assert shares and float(M['FullDetectPctMin']) == min(
        v for k, v in shares.items() if k[13:] in {''.join(w.capitalize() for w in f.split('_')) for f in ONE_PASS})
    assert 0 < float(M['FullDetectPctMin']) < 100


# ------------------------------------------------------------------------------------ the second file of numbers
def test_the_study_delivers_its_macros_to_the_paper_and_the_check_covers_them(tmp_path, monkeypatch):
    from holo_openset import reproduce
    from holo_openset.paper import distance as D
    monkeypatch.setattr(paths, 'PAPER', tmp_path / 'paper')
    monkeypatch.setenv('HOLO_DIST_RESULTS', str(tmp_path / 'nothing'))
    D.main(figures=False)
    a, b = tmp_path / 'paper' / 'numbers_distancia.tex', tmp_path / 'paper' / 'distance' / 'numbers_distancia.tex'
    assert a.read_bytes() == b.read_bytes() and not (tmp_path / 'paper' / 'distance' / 'figures').exists()
    assert str(tmp_path) in a.read_text().splitlines()[1]   # outside the repository: the path as given
    monkeypatch.delenv('HOLO_DIST_RESULTS')
    assert D.results() == STUDY
    assert 'numbers_distancia.tex' in reproduce.NUMBERS


def test_times_of_the_study_are_machine_dependent():
    from holo_openset.reproduce import MACHINE
    machine = ['TAutofocusAfcGpuBigMs', 'TBlindOverNarrowCpuBig', 'FullRecAfcTotalS', 'FullDetectPctMin',
               'BackOverLayerCpuBig', 'DistTimeRecAfsFrontGpuBigMs', 'DistStageAutofocusAfcCpuSmallMs',
               'DistMeasRecAfTotalMs', 'DistMeasRecAfcOverBankJit', 'DistNstarBankJitAfcGpu',
               'DistNstarResolvedBankJitAfrCpu', 'DistPerFrameRecAfcOverBankJitGpu', 'DistSearchBlindOverAfcGpu',
               'DistCritBaseBankJitCheapestGpuCost', 'DistCritBaseBankJitVerdict', 'DistCritMetCount']
    method = ['RecAfcFone', 'RobFrameFiveRecAfc', 'FullRecAfcFone', 'FocusNarrowN', 'DistFoneFrameFiveRecAfc',
              'DistMeasRecAfcFone', 'DistErrBaseAfcMedian', 'DistSearchAfcRangeEffPct', 'DistCritBaseBankJitBest',
              'DistCritBaseBankJitDiff', 'DistSessFiveRecZZeroFOneMeasured', 'DistValBlindBOneTogCost']
    assert [k for k in machine if not MACHINE.match(k)] == []
    assert [k for k in method if MACHINE.match(k)] == []
