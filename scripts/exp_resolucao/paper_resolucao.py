"""Numbers and the parameter table of the section "The simulation changes the answer" of the paper (PROTOCOLO_CURVA.md,
"ESCRITA"), from the stored results of the source-resolution study. Nothing is typed: every number is read from a file.

    python scripts/exp_resolucao/paper_resolucao.py --out <paper>/figures/paper
    -> <out>/numbers_resolucao.tex          macros \\Res..., letters only (the paper inputs it next to numbers.tex)
       <out>/tables/tab_parameters.tex      body of the tabular of every parameter of the simulator, value and source

Inputs (read only):
  results_exp_resolucao/ (HOLO_RES_RESULTS moves it): eval/<set>/<flow>_r<n>.json, pilot_five_reps.csv,
      pilot_five_reps_robustness.csv, pilot_five_reps_alpha.csv, depth_training.csv, sets_by_fresnel.csv,
      setup_comparison.csv, pattern_in_crop_z_summary.csv, envelope_z.csv, spectrum_cutoff.csv,
      simulator_parameters.csv, hologram_diameter_summary.json (when it exists)
  results/eval/{realistic,ideal} (the idealised model against the bench, as tables.tab_ideal reads them)
  data/<set>/physics.json and metadata.csv (the physics and the density of each set)
Nothing is written in results/, expected/ or results_exp_resolucao/.

Repetitions. The sets of the 1.0 mm family are found by themselves: every directory of eval/ whose data set has
z0 = 1.0 mm and the Fresnel layout. A set enters with the mean of five repetitions when r1-r5 exist for the three flows
(crops, propagation layer, reconstruction at z0), and with r1 alone until then; the macros \\Res<Set>Reps say which.
So the five repetitions of the dense set, and the levels of the density curve, enter when their files arrive.
"""
import argparse
import json
import math
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

from holo_openset import paths
from holo_openset.sim.envelope import Setup, cutoff
from holo_openset.sim.physics import PIXEL

RES = Path(os.environ.get('HOLO_RES_RESULTS', paths.PROJECT / 'results_exp_resolucao'))
PAPER_RESULTS = paths.PROJECT / 'results'          # the results of the paper (read only)
DATA = paths.DATA
FLOWS = ['raw', 'prop', 'rec_z0']                  # crops, propagation layer, reconstruction at z0
FLOW_KEY = {'raw': 'Raw', 'prop': 'Prop', 'rec_z0': 'Rec'}
IDEAL_FLOWS = ['raw', 'learned', 'complex', 'wiener', 'prop', 'rec_z0']   # the rows of Table tab:ideal
WINDOW_MM2 = (640 * PIXEL * 1e3) ** 2              # one 640 x 640 window, mm^2
# The 1.0 mm family of the paper is the standard family of Q1 (depths uniform over the 50 um channel). Its dense level
# enters when it has been evaluated; until then the dense set of the pilot (nearly flat sample) stands in, with a flag.
SPARSE, DENSE_STD = 'curve_u50_L008', 'curve_u50_L154'
PILOT, DENSE_PILOT = 'bench_1mm', 'bench_1mm_dense'                  # the first sets at 1.0 mm (nearly flat sample)
DEPTH, CBMS, CODE = 'bench_1mm_depth50', 'realistic', 'base_newrec'   # the wide depth law (stress test); 19.25 mm
DENSE = DENSE_PILOT                                                   # set by numbers(): the dense set in use
F1, REJ, CLOSED = 'novel_open_macro_f1', 'novel_unknown_rejection', 'novel_closed_acc'
ORDINAL = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth']
CARDINAL = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
DIGITS = dict(zip('0123456789', ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']))

M = {}


def macro(name, value, fmt='{:.3f}'):
    """\\Res<name>: letters only; '?' when the value is missing."""
    name = 'Res' + ''.join(DIGITS.get(c, c) for c in name if c.isalnum())
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        M[name] = '?'
    elif isinstance(value, str):
        M[name] = value
    else:
        M[name] = fmt.format(value)


def csv(name, root=RES):
    f = Path(root) / f'{name}.csv'
    return pd.read_csv(f) if f.exists() else pd.DataFrame()


# ------------------------------------------------------------------------------------------------ evaluations
def evals(set_, root=RES, train_set=None, tag=''):
    """One row per (flow, rep) of root/eval/<set>/*.json trained on train_set (default: the set itself)."""
    rows = []
    for f in sorted((Path(root) / 'eval' / set_).glob('*.json')):
        d = json.loads(f.read_text())
        if d.get('tag', '') != tag or d.get('train_set', set_) != (train_set or set_):
            continue
        rows.append(d)
    return pd.DataFrame(rows)


def reps_mode(df):
    """5 when r1-r5 exist for the three flows, else 1 (r1 alone), else 0 (no r1)."""
    if not len(df):
        return 0
    have = {f: set(df[df.flow == f].rep.astype(int)) for f in FLOWS}
    if all({1, 2, 3, 4, 5} <= have[f] for f in FLOWS):
        return 5
    return 1 if all(1 in have[f] for f in FLOWS) else 0


def value(df, flow, col, mode):
    """Mean over r1-r5 (mode 5) or the value of r1 (mode 1) of one flow."""
    if not mode or not len(df):
        return None
    d = df[df.flow == flow]
    d = d[d.rep.astype(int).isin(range(1, 6) if mode == 5 else [1])]
    return float(d[col].mean()) if len(d) else None


def per_rep(df, flow, col):
    d = df[df.flow == flow]
    return d.groupby(d.rep.astype(int))[col].mean()


def physics(set_):
    f = DATA / set_ / 'physics.json'
    return json.loads(f.read_text()) if f.exists() else None


def density(set_):
    """Objects per mm^2 in the window as recorded (annotated letters plus the letters that fill the sample), and the
    mean number per window, from data/<set>/metadata.csv."""
    f = DATA / set_ / 'metadata.csv'
    if not f.exists():
        return None, None
    m = pd.read_csv(f)
    n = m.n_letters + (m.n_fill_window if 'n_fill_window' in m else 0)
    return float(n.mean()) / WINDOW_MM2, float(n.mean())


def family():
    """Every evaluated set at z0 = 1.0 mm with the Fresnel layout: name, density, depth law, repetitions."""
    out = []
    for d in sorted(p for p in (RES / 'eval').rglob('*') if p.is_dir()):
        name = str(d.relative_to(RES / 'eval'))
        ph = physics(name)
        if not ph or ph.get('layout') != 'fresnel' or abs(ph['physics']['z0'] - 1e-3) > 1e-9:
            continue
        df = evals(name)
        mode = reps_mode(df)
        if not mode:
            continue
        dens, per_window = density(name)
        out.append(dict(set=name, density=dens, per_window=per_window, depth_std_um=ph['physics']['depth_std'] * 1e6,
                        depth_max_um=ph['physics']['depth_max'] * 1e6, law=depth_law(ph), mode=mode, df=df))
    return out


def depth_law(ph):
    """The depth law of a set: ('uniform', half-height um) with depth_uniform > 0 (the standard of Q1), else
    ('normal', sd um, cut um)."""
    p = ph['physics']
    if p.get('depth_uniform', 0) > 0:
        return ('uniform', round(p['depth_uniform'] * 1e6, 3))
    return ('normal', round(p['depth_std'] * 1e6, 3), round(p['depth_max'] * 1e6, 3))


def law_tex(law):
    if law[0] == 'uniform':
        return f'uniform in $\\pm${g(law[1])}\\,$\\mu$m'
    return f'$\\mathcal{{N}}(0,{g(law[1])}^2)$, $\\le${g(law[2])}\\,$\\mu$m'


def cbms_equivalent_density():
    """The density of the geometry of CBMS 2024 at the letter scale of the 1.0 mm sets: its letters per mm^2 divided by
    the square of the scale factor between the two sizes of letter (same Fresnel number)."""
    ph = physics(SPARSE)
    dens, _ = density(CBMS)
    if not ph or dens is None:
        return None
    return dens / ph['layout_params']['scale'] ** 2


def ideal_vs_bench():
    """F1 per flow: trained and tested on the idealised model, on the bench, idealised -> bench (mean of five)."""
    out = {}
    for key, s, tr in [('ideal', 'ideal', None), ('bench', 'realistic', None), ('cross', 'realistic', 'ideal')]:
        df = evals(s, PAPER_RESULTS, train_set=tr)
        out[key] = {f: (float(df[df.flow == f][F1].mean()) if len(df) and (df.flow == f).any() else None)
                    for f in IDEAL_FLOWS}
    return out


# ------------------------------------------------------------------------------------------------ the macros
def set_macros(key, df, mode):
    macro(f'{key}Reps', mode if mode else None, '{}')
    macro(f'{key}RepsText', {5: 'the mean of five repetitions', 1: 'one repetition (r1)'}.get(mode))
    for f in FLOWS:
        k = FLOW_KEY[f]
        macro(f'{key}{k}Fone', value(df, f, F1, mode))
        macro(f'{key}{k}Rej', value(df, f, REJ, mode))
        macro(f'{key}{k}Closed', value(df, f, CLOSED, mode))
    for a, b in [('prop', 'raw'), ('rec_z0', 'raw'), ('rec_z0', 'prop')]:
        for col, c in [(F1, 'Fone'), (REJ, 'Rej')]:
            va, vb = value(df, a, col, mode), value(df, b, col, mode)
            macro(f'{key}{FLOW_KEY[a]}Minus{FLOW_KEY[b]}{c}', va - vb if None not in (va, vb) else None, '{:+.3f}')


def criterion(key, df, mode):
    """The criterion of P0, descriptively: prop - raw >= 0.10 in F1 and >= 0.30 in rejection, per repetition."""
    if mode != 5:
        for k in ['CritFone', 'CritRej', 'CritBoth', 'RejSign', 'FoneSign']:
            macro(f'{key}{k}', None)
        return
    gf = per_rep(df, 'prop', F1) - per_rep(df, 'raw', F1)
    gr = per_rep(df, 'prop', REJ) - per_rep(df, 'raw', REJ)
    gf, gr = gf.loc[1:5], gr.loc[1:5]
    macro(f'{key}CritFone', int((gf >= 0.10 - 1e-12).sum()), '{}')
    macro(f'{key}CritRej', int((gr >= 0.30 - 1e-12).sum()), '{}')
    macro(f'{key}CritBoth', int(((gf >= 0.10 - 1e-12) & (gr >= 0.30 - 1e-12)).sum()), '{}')
    macro(f'{key}RejSign', CARDINAL[int((gr > 0).sum())])
    macro(f'{key}FoneSign', CARDINAL[int((gf > 0).sum())])
    macro(f'{key}RejGapMin', float(gr.min()))
    macro(f'{key}RejGapMax', float(gr.max()))
    macro(f'{key}RawRejMin', float(per_rep(df, 'raw', REJ).loc[1:5].min()))
    macro(f'{key}RawRejMax', float(per_rep(df, 'raw', REJ).loc[1:5].max()))


def numbers():
    global DENSE
    M.clear()
    # ---- the sparse set of the standard family, five repetitions, and r1 alone (for comparisons paired with r1)
    sp = evals(SPARSE)
    m_sp = reps_mode(sp)
    set_macros('Sparse', sp, m_sp)
    set_macros('SparseROne', sp, 1 if m_sp else 0)
    criterion('Sparse', sp, m_sp)
    raw_rej = value(sp, 'raw', REJ, m_sp)
    macro('SparseRawAcceptPct', 100 * (1 - raw_rej) if raw_rej is not None else None, '{:.0f}')
    # ---- the pilot (nearly flat sample): where the margin of P0 was registered and first read
    pi = evals(PILOT)
    m_pi = reps_mode(pi)
    set_macros('Pilot', pi, m_pi)
    criterion('Pilot', pi, m_pi)

    # ---- the dense set: the standard family when evaluated (any number of repetitions), else the pilot's, flagged;
    # the paired difference dense - sparse, against the sparse set of the same family and in the same mode
    de = evals(DENSE_STD)
    m_de = reps_mode(de) if len(de) else 0
    if m_de:
        DENSE, ref, ref_df = DENSE_STD, SPARSE, sp
        have = sorted(set(de[de.flow == 'raw'].rep.astype(int)))
        m_text = {5: 'the mean of five repetitions'}.get(m_de, f'one repetition (r1) of {len(have)} so far'
                                                         if len(have) > 1 else 'one repetition (r1)')
        macro('DenseFallback', '')
        macro('DenseFamilyText', 'of the standard sets')
    else:
        DENSE, ref, ref_df = DENSE_PILOT, PILOT, pi
        de = evals(DENSE_PILOT)
        m_de = reps_mode(de)
        m_text = None
        print('WARNING: the dense level of the standard family (%s) has no evaluation yet: the dense numbers come from '
              'the pilot (%s), and \\ResDenseFallback puts a visible note in the text' % (DENSE_STD, DENSE_PILOT))
        macro('DenseFallback', '\\todo[inline]{Dense numbers from the first dense set at 1.0\\,mm (nearly flat '
              'sample, paired with the first sparse set); they move to the dense level of the standard sets when its '
              'evaluations exist.}')
        macro('DenseFamilyText', 'of the first sets at 1.0\\,mm (nearly flat sample)')
    set_macros('Dense', de, m_de)
    if m_text:
        macro('DenseRepsText', m_text)
    criterion('Dense', de, m_de)
    for f in FLOWS:
        for col, c in [(F1, 'Fone'), (REJ, 'Rej')]:
            vd, vs = value(de, f, col, m_de), value(ref_df, f, col, m_de)
            macro(f'DenseMinusSparse{FLOW_KEY[f]}{c}', vd - vs if None not in (vd, vs) else None, '{:+.3f}')
            macro(f'DenseRefSparse{FLOW_KEY[f]}{c}', vs)        # the sparse set in the mode of the dense set
    macro('DensePairText', {5: 'over the same five repetitions', 1: 'in the same repetition'}.get(m_de))

    # ---- the geometry of CBMS 2024 with the same recipe (no auxiliary scenes; r1), and the control of the code
    cb = evals(CBMS)
    set_macros('Cbms', cb, reps_mode(cb))
    co = evals(CODE)
    set_macros('Code', co, reps_mode(co))

    # ---- densities (objects per mm^2) and letters per window
    for key, s in [('Sparse', SPARSE), ('Dense', DENSE), ('Cbms', CBMS)]:
        d, n = density(s)
        macro(f'{key}Density', d, '{:.0f}')
        macro(f'{key}PerWindow', n, '{:.0f}')
    macro('CbmsDensityEquiv', cbms_equivalent_density(), '{:.0f}')
    fam = family()
    dens = [x['density'] for x in fam if x['density'] is not None]
    macro('DensityLo', min(dens) if dens else None, '{:.0f}')
    macro('DensityHi', max(dens) if dens else None, '{:.0f}')
    macro('DensityLevels', CARDINAL[len({round(d) for d in dens})] if dens else None)
    ph = physics(SPARSE)
    macro('ScaleFactor', ph['layout_params']['scale'] if ph else None)
    macro('WindowMmSq', WINDOW_MM2, '{:.2f}')

    # ---- size, Fresnel number and the share of a letter's own pattern outside its crop (sets_by_fresnel.csv)
    sb = csv('sets_by_fresnel')
    for key, s in [('Cbms', CBMS), ('Bench', PILOT)]:   # the letters of the 1.0 mm sets: those of the pilot
        r = sb[sb.set == s]
        r = r[r.repetitions == 'r1'] if (r.repetitions == 'r1').any() else r
        if not len(r):
            continue
        r = r.iloc[0]
        for q, Q in [('p5', 'Lo'), ('p50', 'Mid'), ('p95', 'Hi')]:
            macro(f'{key}Fresnel{Q}', r[f'fresnel_{q}'], '{:.2f}')
            macro(f'{key}Outside{Q}', 100 * r[f'outside_crop_{q}'], '{:.0f}')
            macro(f'{key}Side{Q}Um', r[f'side_px_{q}'] * PIXEL * 1e6, '{:.0f}')
            macro(f'{key}Side{Q}Px', r[f'side_px_{q}'], '{:.0f}')
        macro(f'{key}ZMm', r.z0_mm, '{:.1f}' if r.z0_mm < 10 else '{:g}')
    r_c, r_b = sb[(sb.set == CBMS)], sb[(sb.set == PILOT)]
    if len(r_c) and len(r_b):
        macro('SizeRatio', r_c.side_px_p50.iloc[0] / r_b.side_px_p50.iloc[0], '{:.1f}')
    # the median letter of the CBMS geometry (129 um) at 1 mm and at 19.25 mm (pattern_in_crop_z_summary.csv)
    pz = csv('pattern_in_crop_z_summary')
    big = pz[(pz.source == 'bench') & (pz['size'] == 'base p50')]
    if len(big):
        macro('BigLetterUm', big.side_px.iloc[0] * PIXEL * 1e6, '{:.0f}')
        for z, k in [(1.0, 'OneMm'), (19.25, 'Cbms')]:
            row = big[np.isclose(big.z_mm, z)]
            if len(row):
                macro(f'BigLetterOutside{k}', 100 * (1 - row.share_mean.iloc[0]), '{:.0f}')
                macro(f'BigLetterFresnel{k}', row.fresnel.iloc[0], '{:.1f}' if z < 5 else '{:.2f}')

    # ---- the distance: what the source keeps, and the reduction it would allow (envelope_z.csv, spectrum_cutoff.csv)
    ez = csv('envelope_z')
    for key, z in [('Cbms', 19.25), ('Bench', 1.0), ('Near', 2.0)]:
        r = ez[np.isclose(ez.z_mm, z)]
        if not len(r):
            continue
        r = r.iloc[0]
        macro(f'Env{key}ZMm', r.z_mm, '{:.1f}' if r.z_mm < 10 else '{:g}')
        macro(f'Env{key}BlurUm', r.blur_um, '{:.1f}' if r.blur_um >= 1 else '{:.2f}')
        macro(f'Env{key}Cut', r['f_c_0.1'], '{:.0f}')
        macro(f'Env{key}Bmax', int(r['b_max_0.1']), '{}')
        macro(f'Env{key}BmaxWord', CARDINAL[int(r['b_max_0.1'])])
        macro(f'Env{key}Pixels', int(r['b_max_0.1']) ** 2, '{}')
        macro(f'Env{key}CutOverNyquist', r['f_c_0.1'] / r.nyquist_cyc_per_mm, '{:.2f}')
    if len(ez):
        macro('Nyquist', ez.nyquist_cyc_per_mm.iloc[0], '{:.0f}')
    sc = csv('spectrum_cutoff')
    for key, s in [('Cbms', 'realistic'), ('Near', 'small_near')]:
        r = sc[(sc.set == s) & (sc.signal == 'I/B') & (sc.preregistered.astype(str) == 'True')]
        if len(r):
            macro(f'Blind{key}Cut', r.f_c_cyc_per_mm.iloc[0], '{:.0f}')
            macro(f'Blind{key}B', int(r.b_blind.iloc[0]), '{}')
            macro(f'Blind{key}Images', int(r.n_images.iloc[0]), '{}')

    # ---- the depth laws, and training against test (depth_tests.csv)
    deep, flat, std = physics(DEPTH), physics(PILOT), physics(SPARSE)
    if deep and flat and std:
        macro('DeepStdUm', deep['physics']['depth_std'] * 1e6, '{:g}')
        macro('DeepMaxUm', deep['physics']['depth_max'] * 1e6, '{:g}')
        macro('DeepPctCbms', 100 * deep['physics']['depth_std'] / physics(CBMS)['physics']['z0'], '{:.1f}')
        macro('DeepPctBench', 100 * deep['physics']['depth_std'] / deep['physics']['z0'], '{:.0f}')
        macro('FlatStdUm', flat['physics']['depth_std'] * 1e6, '{:g}')
        macro('FlatMaxUm', flat['physics']['depth_max'] * 1e6, '{:g}')
        half = std['physics'].get('depth_uniform', 0) * 1e6
        macro('StdHalfUm', half or None, '{:g}')
        macro('ChannelUm', 2 * half or None, '{:g}')
        macro('DeepOverChannel', 2 * deep['physics']['depth_max'] * 1e6 / (2 * half) if half else None, '{:g}')
    depth_macros()

    # ---- the propagation layer calibrates itself: the distance its calibration finds on the sparse standard set
    # (recal_<set>_*.json: z_ref, 32 unlabelled validation holograms at 1.0 mm); the pilot's training-time file kept
    rj = sorted(RES.glob(f'recal_{SPARSE}_*.json'))
    macro('AlphaZCalibMm', json.loads(rj[0].read_text())['z_ref'] * 1e3 if rj else None, '{:.2f}')
    ca = csv('curve_alpha')          # alpha calibrated on 32 training holograms and after training, per level and rep
    if len(ca):
        sp_ = ca[ca.set == SPARSE]
        macro('AlphaZCalibMm', sp_.z_calibrated_mm.mean(), '{:.2f}')
        macro('AlphaZCalibLoMm', sp_.z_calibrated_mm.min(), '{:.3f}')
        macro('AlphaZCalibHiMm', sp_.z_calibrated_mm.max(), '{:.3f}')
        macro('AlphaZCalibOffLoPct', 100 * (sp_.z_calibrated_mm.min() - 1.0), '{:+.1f}')
        macro('AlphaChangeLoPct', -100 * sp_.change.max(), '{:.1f}')
        macro('AlphaChangeHiPct', -100 * sp_.change.min(), '{:.1f}')
        macro('AlphaChangeMeanPct', -100 * sp_.change.mean(), '{:.1f}')
        dn = ca[ca.level == ca.level.max()]
        macro('AlphaChangeDensestMeanPct', -100 * dn.change.mean(), '{:.1f}')
        macro('AlphaRepsTotal', len(sp_), '{}')
    al = csv('pilot_five_reps_alpha')
    if len(al):
        macro('PilotAlphaZCalibMm', al.z_calibrated_mm.mean(), '{:.2f}')
        macro('PilotAlphaChangeLoPct', -100 * al.change.max(), '{:.1f}')
        macro('PilotAlphaChangeHiPct', -100 * al.change.min(), '{:.1f}')
    macro('CalibStepPct', calib_step_pct(), '{:.2f}')

    # ---- the idealised model against the bench: the rank of the Wiener filter (results/eval, as tab_ideal)
    ib = ideal_vs_bench()
    for key in ['ideal', 'bench']:
        v = {f: x for f, x in ib[key].items() if x is not None}
        if 'wiener' in v:
            rank = sorted(v, key=lambda f: -v[f]).index('wiener')
            macro(f'{key.capitalize()}WienerRank', ORDINAL[rank])
            macro(f'{key.capitalize()}Flows', CARDINAL[len(v)])

    # ---- the effective diameter of the hologram (the axis of the density curve), when it has been measured
    hd = RES / 'hologram_diameter_summary.json'
    macro('HoloDiameterUm', None)
    if hd.exists():
        j = json.loads(hd.read_text())          # hologram_diameter.py: the axis chosen by the rule of Q0
        d = j.get('D_ef_um', {}).get(j.get('axis'))
        macro('HoloDiameterUm', d, '{:.0f}')
        if d is not None:                         # Seo et al. 2009: 1 - exp(-pi D^2 sigma), at the densities obtained
            for key, s_ in [('Sparse', SPARSE), ('Dense', DENSE)]:
                sigma = density(s_)[0]
                macro(f'{key}OverlapPct', 100 * (1 - math.exp(-math.pi * (d * 1e-3) ** 2 * sigma))
                      if sigma is not None else None, '{:.0f}')

    # ---- the distance of the sample changes (distance_tests_u50.csv when it exists, else distance_tests.csv)
    distance_macros()

    curve_macros()

    # ---- the main results (geometry of CBMS 2024, the models of the paper): closed-set accuracy, not in numbers.tex
    mn = evals(CBMS, PAPER_RESULTS)
    for f in FLOWS:
        macro(f'Main{FLOW_KEY[f]}Closed', value(mn, f, CLOSED, reps_mode(mn)))
    # ---- enrollment, propagation layer against the reconstruction at z0, paired by repetition (enroll_paired.csv)
    ep = csv('enroll_paired')
    if len(ep):
        for metric, k in [('world5_new_class_acc', 'Five'), ('world20_new_class_acc', 'Twenty'),
                          ('worldall_new_class_acc', 'All'), ('world20_absent_rejection', 'AbsentTwenty')]:
            r = ep[(ep.layer == 'prop') & (ep.reconstruction == 'rec_z0') & (ep.metric == metric)]
            if len(r):
                r = r.iloc[0]
                macro(f'EnrollPair{k}Diff', r.diff_mean, '{:+.3f}')
                macro(f'EnrollPair{k}Layer', r.layer_mean)
                macro(f'EnrollPair{k}Rec', r.rec_mean)
                macro(f'EnrollPair{k}Lo', r.diff_min, '{:+.3f}')
                macro(f'EnrollPair{k}Hi', r.diff_max, '{:+.3f}')
                macro(f'EnrollPair{k}Pos', int(sum(r[f'diff_r{i}'] > 0 for i in range(1, 6))), '{}')

    # ---- the parameter table: counts by source
    pt = csv('simulator_parameters')
    if len(pt):
        modelled = pt[~pt.code_name.astype(str).str.contains(r'not modelled|derived', regex=True)]
        macro('ParamCount', len(modelled), '{}')
        # 'personal communication' in the csv: what the authors know of their own bench and the article does not report
        for t, k in [('article', 'Article'), ('datasheet', 'Datasheet'), ('personal communication', 'Bench'),
                     ('our assumption', 'Assumption')]:
            macro(f'Param{k}', int((modelled.source_type == t).sum()), '{}')
    return M, fam


DIST_KEY = {0.7: 'SevenTenths', 0.9: 'NineTenths', 1.0: 'One', 1.1: 'ElevenTenths'}


def distance_macros():
    """Models of the 1.0 mm sets tested at other distances: as they are, and with the distance recalibrated without
    labels (literal, and by ratio: the variant registered as the main one). distance_tests_u50.csv (models of the
    standard family) is preferred when it exists; distance_tests.csv holds the models of the sparse pilot set."""
    u50 = csv('distance_tests_u50')
    dt = u50 if len(u50) else csv('distance_tests')
    rows = csv('distance_tests_u50_rows') if len(u50) else csv('distance_tests_rows')
    macro('DistModelsText', None if not len(dt) else
          'the five models of the sparse set of the standard family' if len(u50) else
          'the five models of the sparse set with a nearly flat sample')
    if not len(dt):
        return
    met = dt[dt.kind == 'metric']
    for d, k in DIST_KEY.items():
        macro(f'Dist{k}Mm', d, '{:.1f}')
        for cond, c in [('as_is', 'As'), ('recal_literal', 'Literal'), ('recal_ratio', 'Ratio')]:
            for f in FLOWS:
                r = met[np.isclose(met.distance_mm, d) & (met.flow == f) & (met.condition == cond)]
                if len(r):
                    macro(f'Dist{c}{k}{FLOW_KEY[f]}Fone', r.f1_mean.iloc[0])
                    macro(f'Dist{c}{k}{FLOW_KEY[f]}Rej', r.rejection_mean.iloc[0])
                if len(rows) and 'known_acc' in rows:
                    q = rows[(rows.kind == 'metric') & np.isclose(rows.distance_mm, d) & (rows.flow == f)
                             & (rows.condition == cond)]
                    if len(q):
                        macro(f'Dist{c}{k}{FLOW_KEY[f]}Known', q.known_acc.mean(), '{:.2f}')
    near = [d for d in DIST_KEY if d != 1.0 and d != 0.7]          # 0.7 mm is the stress test (Q1)
    asis = met[(met.condition == 'as_is') & met.distance_mm.round(3).isin(near) & met.flow.isin(['prop', 'rec_z0'])]
    if len(asis):
        macro('DistAsIsFoneLo', asis.f1_mean.min())
        macro('DistAsIsFoneHi', asis.f1_mean.max())
        macro('DistAsIsRejLo', asis.rejection_mean.min())
    cond = 'rec_z0 recal_ratio - prop recal_ratio'
    rm = dt[(dt.kind == 'rec_minus_prop') & (dt.condition == cond)]
    if len(rm):
        macro('DistRecMinusPropLo', rm.f1_mean.min())
        macro('DistRecMinusPropHi', rm.f1_mean.max())
        macro('DistRecMinusPropRepLo', rm.f1_min.min())
        macro('DistRecMinusPropRepHi', rm.f1_max.max())
        macro('DistRecAbovePropDistances', CARDINAL[len(rm)])
        for d, k in DIST_KEY.items():
            x = rm[np.isclose(rm.distance_mm, d)]
            if len(x):
                macro(f'DistRecMinusProp{k}', x.f1_mean.iloc[0], '{:+.3f}')
        rr = rows[(rows.kind == 'rec_minus_prop') & (rows.condition == cond)] if len(rows) else rows
        if len(rr):          # per repetition: how many of the comparisons have the reconstruction above the layer
            macro('DistRecAbovePropCount', int((rr.f1 > 0).sum()), '{}')
            macro('DistRecAbovePropTotal', len(rr), '{}')
    one = met[np.isclose(met.distance_mm, 1.0) & (met.condition == 'as_is')].set_index('flow')
    if {'prop', 'rec_z0'} <= set(one.index):
        macro('DistRecMinusPropAtOne', one.loc['rec_z0', 'f1_mean'] - one.loc['prop', 'f1_mean'], '{:+.3f}')
    rc = dt[dt.kind == 'recal']
    if len(rc):
        macro('DistRecalImages', int(rc.n.iloc[0]), '{}')
        for d, k in DIST_KEY.items():
            x = rc[np.isclose(rc.z_nominal_mm, d)]
            if len(x):   # the distance found by ratio against the true mean distance of the recorded sessions
                macro(f'DistZErr{k}Pct', 100 * x.z_ratio_minus_true_mm.iloc[0] / x.z_true_mm.iloc[0], '{:+.2f}')


def calib_step_pct():
    """The step of the fine scan of calibrate_alpha, relative to alpha (from its own defaults)."""
    import inspect
    try:
        from holo_openset.train import calibrate_alpha
    except Exception as e:      # noqa: BLE001  the generator must not fail on an import
        print('WARNING: calibrate_alpha not importable:', e)
        return None
    p = {k: v.default for k, v in inspect.signature(calibrate_alpha).parameters.items()}
    r = (p['hi'] / p['lo']) ** (1 / (p['n_coarse'] - 1))
    return 100 * (r - 1 / r) / (p['n_fine'] - 1)


LAWS = [('flat', 'Flat'), ('u50', 'Std'), ('wide', 'Wide')]      # depth_tests.csv: nearly flat, standard, stress


def depth_macros():
    """Training law -> test law, F1 per flow and number of repetitions, and the paired differences
    (depth_tests.csv; its 'diff' rows)."""
    dt = csv('depth_tests')
    if not len(dt):
        print('WARNING: depth_tests.csv missing')
        return
    m = dt[dt.kind != 'diff']
    for tr, T in LAWS:
        for te, E in LAWS:
            for f in FLOWS:
                r = m[(m.trained == tr) & (m.tested == te) & (m.flow == f)]
                if len(r):
                    macro(f'Depth{T}To{E}{FLOW_KEY[f]}Fone', r.f1_mean.iloc[0])
                    macro(f'Depth{T}To{E}Reps', int(r.n_reps.iloc[0]), '{}')
                    macro(f'Depth{T}To{E}RepsWord', CARDINAL[int(r.n_reps.iloc[0])])
    d = dt[dt.kind == 'diff']
    for key, cond in [('FlatToStd', 'flat->u50 - flat->flat'), ('StdToWide', 'u50->wide - u50->u50'),
                      ('StdToFlat', 'u50->flat - u50->u50')]:
        for f in FLOWS:
            r = d[(d.tested == cond) & (d.flow == f)]
            if len(r):
                r = r.iloc[0]
                macro(f'DepthDiff{key}{FLOW_KEY[f]}', r.f1_mean, '{:+.3f}')
                macro(f'DepthDiff{key}{FLOW_KEY[f]}Lo', r.f1_min, '{:+.3f}')
                macro(f'DepthDiff{key}{FLOW_KEY[f]}Hi', r.f1_max, '{:+.3f}')
                macro(f'DepthDiff{key}{FLOW_KEY[f]}Loss', -r.f1_mean, '{:.2f}')
                n_neg = 'five' if r.f1_max < 0 and int(r.n_reps) == 5 else None
                macro(f'DepthDiff{key}{FLOW_KEY[f]}AllNeg', n_neg or 'not all')
    raw = d[d.flow == 'raw']
    if len(raw):
        macro('DepthRawMaxAbs', float(np.abs(raw[['f1_min', 'f1_max']].to_numpy()).max()), '{:.3f}')
    flat_wide = m[(m.trained == 'flat') & (m.tested == 'wide')].set_index('flow')
    flat_flat = m[(m.trained == 'flat') & (m.tested == 'flat')].set_index('flow')
    for f in ['prop', 'rec_z0']:
        if f in flat_wide.index and f in flat_flat.index:
            macro(f'DepthFlatToWideLoss{FLOW_KEY[f]}', flat_flat.loc[f, 'f1_mean'] - flat_wide.loc[f, 'f1_mean'],
                  '{:.2f}')


def curve_table():
    """tab_curve: one row per level of the density curve: objects per mm^2, share of overlapping holograms, F1 and
    rejection of the three flows (mean of five, or r1), rejection with its min-max over the repetitions."""
    t = csv('density_curve')
    if not len(t):
        return None
    lines = []
    for lv, g in t.groupby('level'):
        g = g.set_index('flow')
        r0 = g.iloc[0]
        five = int(g.loc['raw', 'n_reps']) == 5
        f1 = [f'{(g.loc[f, "f1_mean"] if five else g.loc[f, "f1_r1"]):.3f}' for f in FLOWS]
        rej = [(f'{g.loc[f, "rejection_mean"]:.3f} \\tiny({g.loc[f, "rejection_min"]:.2f}--{g.loc[f, "rejection_max"]:.2f})'
                if five else f'{g.loc[f, "rejection_r1"]:.3f}') for f in FLOWS]
        ov = 100 * r0.overlap
        lines.append(f'{r0.per_mm2:.0f} & {ov:.0f} & ' + ' & '.join(f1) + ' & ' + ' & '.join(rej)
                     + f' & {int(g.loc["raw", "n_reps"])} \\\\')
    return lines


def depth_table():
    """tab_depth: rows the training law, columns the test law, cells 'layer / reconstruction' F1, and the number of
    repetitions of each row (depth_tests.csv)."""
    dt = csv('depth_tests')
    if not len(dt):
        return ['\\multicolumn{5}{l}{(depth tests missing)} \\\\']
    m = dt[dt.kind != 'diff']
    name = {'flat': 'nearly flat', 'u50': 'standard (channel)', 'wide': 'stress test'}
    lines = []
    for tr, _ in LAWS:
        cells, reps = [], set()
        for te, _ in LAWS:
            r = m[(m.trained == tr) & (m.tested == te)].set_index('flow')
            if {'prop', 'rec_z0'} <= set(r.index):
                cells.append(f'{r.loc["prop", "f1_mean"]:.3f} / {r.loc["rec_z0", "f1_mean"]:.3f}')
                reps.add(int(r.loc['prop', 'n_reps']))
            else:
                cells.append('--')
        lines.append(f'{name[tr]} & ' + ' & '.join(cells) + f' & {"/".join(map(str, sorted(reps)))} \\\\')
    return lines


LEVEL_WORD = {8: 'Eight', 15: 'Fifteen', 69: 'SixtyNine', 154: 'OneFiftyFour', 343: 'ThreeFortyThree'}


def curve_macros():
    """The density curve (density_curve.csv and density_curve_reading.json of density_curve_table.py), per level and
    flow: F1 and rejection (the mean of five where five exist, else r1), repetitions, density, overlap and pi D^2
    sigma, and the reading of Q0 ('fell' in F1 and in rejection). Skipped, with a warning, until the csv exists."""
    t = csv('density_curve')
    if not len(t):
        print('WARNING: density_curve.csv missing: no curve macros')
        macro('CurveAvailable', 'no')
        return
    macro('CurveAvailable', 'yes')
    macro('CurveLevels', CARDINAL[t.level.nunique()] if t.level.nunique() < len(CARDINAL) else str(t.level.nunique()))
    for lv, g in t.groupby('level'):
        L = 'Curve' + LEVEL_WORD.get(int(lv), f'L{int(lv)}')
        r0 = g.iloc[0]
        macro(f'{L}Density', r0.per_mm2, '{:.0f}')
        macro(f'{L}PerWindow', r0.letters_per_window, '{:.0f}')
        macro(f'{L}OverlapPct', 100 * r0.overlap, '{:.0f}')
        macro(f'{L}PiDSigma', r0.pi_D2_sigma, '{:.2f}')
        for _, r in g.iterrows():
            if r.flow not in FLOW_KEY:
                continue
            k, five = FLOW_KEY[r.flow], int(r.n_reps) == 5
            macro(f'{L}{k}Reps', int(r.n_reps), '{}')
            macro(f'{L}{k}Fone', r.f1_mean if five else r.f1_r1)
            macro(f'{L}{k}Rej', r.rejection_mean if five else r.rejection_r1)
            for m_, M_ in [('f1', 'Fone'), ('rej', 'Rej')]:
                v = r.get(f'fell_{m_}_4of5') if five else r.get(f'fell_{m_}_r1')
                macro(f'{L}{k}Fell{M_}', None if pd.isna(v) else ('fell' if str(v) == 'True' else 'did not fall'))
    # the paired differences per level (rows 'prop - raw', 'rec_z0 - prop'), with the count of repetitions by sign
    reps = csv('density_curve_reps')
    for lv, g in t.groupby('level'):
        L = 'Curve' + LEVEL_WORD.get(int(lv), f'L{int(lv)}')
        for fl, K in [('prop - raw', 'PropMinusRaw'), ('rec_z0 - prop', 'RecMinusProp')]:
            r = g[g.flow == fl]
            if len(r):
                r = r.iloc[0]
                macro(f'{L}{K}Fone', r.f1_mean, '{:+.3f}')
                macro(f'{L}{K}Rej', r.rejection_mean, '{:+.3f}')
                if fl == 'prop - raw' and not pd.isna(r.get('p0_both_count')):
                    macro(f'{L}MarginBoth', int(r.p0_both_count), '{}')
            if len(reps):
                q = reps[(reps.level == lv) & (reps.flow == fl)]
                if len(q):
                    macro(f'{L}{K}RejPos', int((q.rejection > 0).sum()), '{}')
                    macro(f'{L}{K}FonePos', int((q.f1 > 0).sum()), '{}')
        for f in FLOWS:
            r = g[g.flow == f]
            if len(r):
                r = r.iloc[0]
                macro(f'{L}{FLOW_KEY[f]}Closed', r.closed_acc_mean)
                macro(f'{L}{FLOW_KEY[f]}DropFone', -r.d_f1_mean, '{:.3f}')
                macro(f'{L}{FLOW_KEY[f]}DropRej', -r.d_rej_mean, '{:.3f}')
                macro(f'{L}{FLOW_KEY[f]}RejLo', r.rejection_min)
                macro(f'{L}{FLOW_KEY[f]}RejHi', r.rejection_max)
                if len(reps):
                    q = reps[(reps.level == lv) & (reps.flow == f)]
                    macro(f'{L}{FLOW_KEY[f]}DropRejRepLo', -q.d_rej.max(), '{:.3f}')
                    macro(f'{L}{FLOW_KEY[f]}DropRejRepHi', -q.d_rej.min(), '{:.3f}')
                    macro(f'{L}{FLOW_KEY[f]}FellRejCount', int(q.fell_rej.astype(str).eq('True').sum()), '{}')
                    macro(f'{L}{FLOW_KEY[f]}FellFoneCount', int(q.fell_f1.astype(str).eq('True').sum()), '{}')
    # where each flow falls first (rule of Q0, from the five repetitions), as a density
    for f in FLOWS:
        for m_, M_ in [('f1', 'Fone'), ('rej', 'Rej')]:
            g = t[(t.flow == f) & (t[f'fell_{m_}_4of5'].astype(str) == 'True')].sort_values('per_mm2')
            macro(f'CurveFirstFall{FLOW_KEY[f]}{M_}', g.per_mm2.iloc[0] if len(g) else 'none', '{:.0f}')
    macro('CurveDensestDensity', t.per_mm2.max(), '{:.0f}')
    macro('CurveSparsestDensity', t.per_mm2.min(), '{:.0f}')
    # the sets that existed before, on the same axis (hologram_diameter_<set>_summary.json: their own D)
    sb = csv('sets_by_fresnel')
    for key, s_ in [('Cbms', CBMS), ('SmallNear', 'small_near')]:
        f = RES / f'hologram_diameter_{s_}_summary.json'
        if f.exists():
            j = json.loads(f.read_text())
            macro(f'{key}HoloDiameterUm', j['D_ef_um'][j['axis']], '{:.0f}')
            macro(f'{key}OverlapPct', 100 * j['density']['overlap_window'], '{:.0f}')
            macro(f'{key}PiDSigma', j['density']['pi_D2_sigma_window'], '{:.2f}')
            macro(f'{key}ZAxisMm', j['z_mm'], '{:g}')
        r = sb[(sb.set == s_) & (sb.repetitions == 'mean5')]
        if len(r):
            macro(f'{key}MeanFiveRawFone', r.f1_raw.iloc[0])
            macro(f'{key}MeanFiveRawRej', r.rejection_raw.iloc[0])
            macro(f'{key}MeanFivePropFone', r.f1_prop.iloc[0])
            macro(f'{key}MeanFiveRecFone', r.f1_rec_z0.iloc[0])
    rd = RES / 'density_curve_reading.json'
    if rd.exists():
        j = json.loads(rd.read_text())
        for k, K in [('f1', 'Fone'), ('rej', 'Rej')]:
            v = j.get('layer_falls_first', {}).get(k)
            macro(f'CurveLayerFallsFirst{K}', f'{v} letters per window' if isinstance(v, int) else str(v))
        macro('CurveProvisional', 'provisional (one repetition at some levels)' if j.get('provisional') else 'final')


# ------------------------------------------------------------------------------------------------ parameter table
def tex(s):
    """A value of simulator_parameters.csv in LaTeX (units joined by a thin space, ranges with an en dash)."""
    s = re.sub(r'\s*\(on\)', '', str(s))
    s = re.sub(r'(\d)-(\d)', r'\1--\2', s.replace('A-Z', 'A--Z'))
    s = s.replace('%', '\\%').replace('+-', '$\\pm$').replace('_', '\\_').replace(' deg', '$^\\circ$')
    s = re.sub(r'(\d) (px|mm|nm|cm|um|e-)', r'\1\\,\2', s)
    s = re.sub(r'(?<![A-Za-z])um(?![A-Za-z])', '$\\\\mu$m', s)
    return s.replace('mm2', 'mm$^2$').replace('e-', 'e$^-$').replace(' x ', '$\\times$')


def g(x, k=3):
    """A number without trailing zeros."""
    return f'{x:.{k}g}'


def source_cell(row, cite):
    t = row.source_type
    if t == 'article':
        return f'article~\\cite{{{cite["article"]}}}'
    if t == 'datasheet':
        return 'datasheet~\\cite{' + (cite['led'] if 'Thorlabs' in row.source else cite['sensor']) + '}'
    if t == 'personal communication':
        return 'the bench (not reported in the article)'
    kind = next((w for w in ('numerical', 'design', 'implementation', 'protocol', 'standard', 'physics')
                 if w in str(row.source)), None)
    return 'our assumption' + {'numerical': ' (numerical)', 'design': ' (design)', 'protocol': ' (design)',
                               'implementation': ' (implementation)', 'standard': ' (standard)',
                               'physics': ' (physics)'}.get(kind, '')


def parameter_table(fam, cite):
    """One row per parameter of simulator_parameters.csv, with the value in the geometry of CBMS 2024 and in the
    1.0 mm sets read from their physics.json (and metadata.csv) where the code has a field for it; rows that exist only
    in the 1.0 mm sets are added in their place."""
    pt = csv('simulator_parameters')
    pc, pb = physics(CBMS), physics(SPARSE)
    if not len(pt) or not pc or not pb:
        return ['\\multicolumn{4}{l}{(parameter files missing)} \\\\']
    c, b, lb = pc['physics'], pb['physics'], pb['layout_params']
    deep = physics(DEPTH)
    sb = csv('sets_by_fresnel')
    meta_c = pd.read_csv(DATA / CBMS / 'metadata.csv')
    meta_b = pd.read_csv(DATA / SPARSE / 'metadata.csv')
    dens = sorted(x['density'] for x in fam if x['density'] is not None)
    laws = {x['law'] for x in fam}
    pf = physics(PILOT)
    std_law = depth_law(pb)
    depth_cell = '; '.join(
        ([f'{law_tex(std_law)}, the {g(2 * std_law[1])}\\,$\\mu$m channel (standard)'] if std_law[0] == 'uniform' else [])
        + ([f'{law_tex(depth_law(pf))} (nearly flat: first sets and depth tests)'] if pf else [])
        + ([f'{law_tex(depth_law(deep))} (stress test)'] if deep else []))

    def side(s):
        r = sb[sb.set == s].iloc[0]
        return (f'{r.side_px_p5:.0f}--{r.side_px_p95:.0f}\\,px ({r.side_px_p5 * PIXEL * 1e6:.0f}--'
                f'{r.side_px_p95 * PIXEL * 1e6:.0f}\\,$\\mu$m)')

    same = object()
    V = {   # parameter -> (value in the CBMS geometry, value at 1.0 mm); `same`: one value for both
        'LED bandwidth (FWHM)': (f'{g(c["bandwidth"] * 1e9)}\\,nm', same),
        'wavelength nodes': (f'{c["n_wavelengths"]}', same),
        'pinhole diameter': (f'{g(c["pinhole"] * 1e6)}\\,$\\mu$m', same),
        'pinhole distance': (f'{g(c["source_distance"] * 100)}\\,cm', same),
        'bit depth': (f'{c["bits"]}', same),
        'full well': (f'{g(c["full_well"], 4)}\\,e$^-$', same),
        'read noise': (f'{g(c["read_noise"])}\\,e$^-$ rms', same),
        'exposure': (f'{g(100 * c["exposure"])}\\,\\% of full scale', same),
        'PRNU': (f'{g(100 * c["prnu"])}\\,\\% rms', same),
        'sample-to-sensor distance': (f'{g(c["z0"] * 1e3, 4)}\\,mm', f'{b["z0"] * 1e3:.1f}\\,mm'),
        'distance spread between sessions': (f'{g(100 * c["session_z_std"])}\\,\\% of $z_0$', same),
        'depth spread of objects': (law_tex(depth_law(pc)), depth_cell),
        'absorption of the letters': (f'$\\mathcal{{N}}({g(c["absorption_mean"])},{g(c["absorption_std"])}^2)$ in '
                                      f'$[{g(c["absorption_min"])},1]$', same),
        'phase delay of the letters': (f'$\\mathcal{{N}}({g(c["phase_mean"])},{g(c["phase_std"])}^2)$\\,rad in '
                                       f'$[0,{g(c["phase_max"])}]$', same),
        'letter size (base)': (side(CBMS), side(PILOT)),
        'letters per window': (f'{lb["letters_mean"]:g} (sd {lb["letters_std"]:g}, {lb["letters_min"]}--'
                               f'{lb["letters_max"]}) annotated', same),
        'rotation': (f'$\\pm${lb["rotation"]:g}$^\\circ$', same),
        'letters outside the window': (f'{meta_c.n_outside.mean():.0f} per window, up to {c["reach"]}\\,px',
                                       f'{meta_b.n_outside.mean():.0f} per window, up to {b["reach"]}\\,px'),
        'window': (f'{c["window"][0]}$\\times${c["window"][1]}\\,px', same),
        'simulated margin': (f'{c["margin"]}\\,px', f'{b["margin"]}\\,px'),
        'reach of outside objects': None,     # merged into 'letters outside the window'
        'dust on the glass': (f'{g(c["dust_density"])}/mm$^2$ per surface', same),
        'depth of the glass surfaces': (f'$+${g(c["dust_depths"][0] * 1e3)} and ${g(c["dust_depths"][1] * 1e3)}$\\,mm',
                                        same),
        'dust on the sensor window': (f'{g(c["sensor_dust_density"])}/mm$^2$', same),
        'distance of the sensor window': (f'{g(c["sensor_dust_z"] * 1e3)}\\,mm', same),
        'beam waist': (f'{g(c["beam_waist"][0])}--{g(c["beam_waist"][1])} half-diagonals', same),
        'beam centre offset': (f'{g(c["beam_offset_std"])} half-diagonals', same),
        'blank frames per session': (f'{pc["n_blanks"]}', same),
        'images per session': (f'{pc["per_session"]}', same),
        'seeds': (f'{pc["seed"]} / {pc["camera_seed"]}', same),
        'recorded quantity': ('intensity $|U|^2$', same),
        'propagation model': ('Fresnel, $e^{-i\\pi\\lambda z|\\mathbf{f}|^2}$, in air', same),
        'distance spread per image': ('0 (robustness sets only)', same),
        'distance drift per image': ('0 (one robustness set)', same),
        'tilt of the sample plane': (f'{g(pb["physics"].get("tilt_deg", 0))}$^\\circ$', same),
        'letter size (small sets)': (tex(str(pt[pt.parameter == 'letter size (small sets)'].value.iloc[0])
                                         .split('(')[1].rstrip(')')), '--'),
    }
    extra = {   # rows of the 1.0 mm sets only, inserted after the row named
        'propagation model': ('recording grid', '1 (pixel)', f'{b.get("oversample", 1)}$\\times$ finer than the '
                              'pixel', 'our assumption (numerical; convergence test)'),
        'letter size (base)': ('object density', f'{density(CBMS)[0]:.0f}/mm$^2$',
                               (f'{dens[0]:.0f} to {dens[-1]:.0f}/mm$^2$ (an axis)' if dens else '--'),
                               'our assumption'),
    }
    notes = {   # what the source cell must say besides its type, where the two columns differ in source
        'sample-to-sensor distance': 'CBMS 2024: read from the code of its generator~\\cite{%s}; 1.0\\,mm: the bench '
                                     '(not reported in the article)' % cite['cbms'],
        'depth spread of objects': ('1.0\\,mm standard: the height of the channel, article~\\cite{%s}; the uniform law '
                                    'and the distance of the session at the middle of the channel: our assumption; '
                                    'the other laws: our assumption' % cite['article']
                                    if std_law[0] == 'uniform' else 'our assumption'),
        'letter size (base)': 'our assumption; 1.0\\,mm: scaled to the Fresnel number of the CBMS geometry',
        'pinhole distance': 'article~\\cite{%s} (to the sensor; the simulator takes it to the sample)' % cite['article'],
    }
    label = {'letter size (base)': 'letter size (5th--95th percentile)', 'depth spread of objects': 'depth of objects',
             'letter size (small sets)': 'letter size (small-object sets)',
             'letters outside the window': 'letters outside the window (not annotated)'}
    lines = []
    for _, r in pt.iterrows():
        p = r.parameter
        if p in V and V[p] is None:
            continue
        if p in V:
            vc, vb = V[p]
            vb = vc if vb is same else vb
        else:
            vc = tex(f'{r.value} {r.unit}'.replace(' -', '').strip())
            vb = '--' if p == 'letter size (small sets)' else vc
        if '(not modelled)' in str(r.code_name):
            vc = vb = 'not modelled'
        if '(derived)' in str(r.code_name):
            vc += ' (derived)'
            vb = vc
        src = notes.get(p, source_cell(r, cite))
        if vb == vc:
            lines.append(f'{label.get(p, p)} & \\multicolumn{{2}}{{>{{\\raggedright\\arraybackslash}}p{{\\paramw}}}}{{{vc}}} & {src} \\\\')
        else:
            lines.append(f'{label.get(p, p)} & {vc} & {vb} & {src} \\\\')
        if p in extra:
            n, xc, xb, xs = extra[p]
            lines.append(f'{n} & {xc} & {xb} & {xs} \\\\')
    return lines


# ------------------------------------------------------------------------------------------------ main
def write(out, cite):
    out = Path(out)
    (out / 'tables').mkdir(parents=True, exist_ok=True)
    m, fam = numbers()
    head = ['% generated by scripts/exp_resolucao/paper_resolucao.py -- do not edit',
            f'% results: {RES.relative_to(paths.PROJECT) if RES.is_relative_to(paths.PROJECT) else RES}; '
            'sets of the 1.0 mm family: ' + ', '.join(f'{x["set"]} ({x["mode"]} rep.)' for x in fam)]
    body = [f'\\newcommand{{\\{k}}}{{{v}}}' for k, v in sorted(m.items())]
    (out / 'numbers_resolucao.tex').write_text('\n'.join(head + body) + '\n')
    print('wrote', out / 'numbers_resolucao.tex', f'({len(body)} macros, {sum(v == "?" for v in m.values())} missing)')
    lines = ['% generated by scripts/exp_resolucao/paper_resolucao.py from simulator_parameters.csv and the '
             'physics.json of the sets -- do not edit'] + parameter_table(fam, cite)
    (out / 'tables' / 'tab_parameters.tex').write_text('\n'.join(lines) + '\n')
    print('wrote', out / 'tables' / 'tab_parameters.tex', f'({len(lines) - 1} rows)')
    ct = curve_table()
    if ct:
        (out / 'tables' / 'tab_curve.tex').write_text('\n'.join(
            ['% generated by scripts/exp_resolucao/paper_resolucao.py from density_curve.csv -- do not edit'] + ct) + '\n')
        print('wrote', out / 'tables' / 'tab_curve.tex')
    else:
        print('WARNING: density_curve.csv missing: tab_curve not written')
    lines = ['% generated by scripts/exp_resolucao/paper_resolucao.py from depth_tests.csv -- do not edit'] + depth_table()
    (out / 'tables' / 'tab_depth.tex').write_text('\n'.join(lines) + '\n')
    print('wrote', out / 'tables' / 'tab_depth.tex')


CITE = dict(article='sobieranski2015portable', led='thorlabsM385L2', sensor='onsemiMT9J003', cbms='rockembach')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', default=str(paths.PAPER), help='directory of the figures of the paper (figures/paper)')
    write(ap.parse_args().out, CITE)
