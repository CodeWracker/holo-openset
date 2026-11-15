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
SPARSE, DENSE, DEPTH, CBMS, CODE = 'bench_1mm', 'bench_1mm_dense', 'bench_1mm_depth50', 'realistic', 'base_newrec'
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
                        depth_max_um=ph['physics']['depth_max'] * 1e6, mode=mode, df=df))
    return out


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
    M.clear()
    # ---- the sparse set at 1.0 mm (the pilot), five repetitions, and r1 alone (for comparisons paired with r1)
    sp = evals(SPARSE)
    m_sp = reps_mode(sp)
    set_macros('Sparse', sp, m_sp)
    set_macros('SparseROne', sp, 1 if m_sp else 0)
    criterion('Sparse', sp, m_sp)
    raw_rej = value(sp, 'raw', REJ, m_sp)
    macro('SparseRawAcceptPct', 100 * (1 - raw_rej) if raw_rej is not None else None, '{:.0f}')

    # ---- the dense set (control C): r1 until r1-r5 exist; the paired difference dense - sparse in the same mode
    de = evals(DENSE)
    m_de = reps_mode(de)
    set_macros('Dense', de, m_de)
    criterion('Dense', de, m_de)
    for f in FLOWS:
        for col, c in [(F1, 'Fone'), (REJ, 'Rej')]:
            vd, vs = value(de, f, col, m_de), value(sp, f, col, m_de)
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
    for key, s in [('Cbms', CBMS), ('Bench', SPARSE)]:
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
    r_c, r_b = sb[(sb.set == CBMS)], sb[(sb.set == SPARSE)]
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

    # ---- the depth of the sample (depth_training.csv: r1; pilot_five_reps_robustness.csv: five repetitions)
    dt = csv('depth_training')
    rb = csv('pilot_five_reps_robustness')
    deep, flat = physics(DEPTH), physics(SPARSE)
    if deep and flat:
        macro('DeepStdUm', deep['physics']['depth_std'] * 1e6, '{:g}')
        macro('DeepMaxUm', deep['physics']['depth_max'] * 1e6, '{:g}')
        macro('DeepPctCbms', 100 * deep['physics']['depth_std'] / physics(CBMS)['physics']['z0'], '{:.1f}')
        macro('DeepPctBench', 100 * deep['physics']['depth_std'] / deep['physics']['z0'], '{:.0f}')
        macro('FlatStdUm', flat['physics']['depth_std'] * 1e6, '{:g}')
        macro('FlatMaxUm', flat['physics']['depth_max'] * 1e6, '{:g}')
    for f in FLOWS:
        k = FLOW_KEY[f]
        if len(rb):
            b = rb[(rb.variant == 'base') & (rb.flow == f)]
            d = rb[(rb.variant == 'depth50') & (rb.flow == f)]
            if len(b) and len(d):
                macro(f'DepthFlatToDeep{k}Fone', d.novel_open_macro_f1_mean.iloc[0])
                macro(f'DepthLoss{k}', b.novel_open_macro_f1_mean.iloc[0] - d.novel_open_macro_f1_mean.iloc[0])
        if len(dt):
            for tr, te, name in [('deep', 'deep', 'DeepToDeep'), ('deep', 'flat', 'DeepToFlat'),
                                 ('flat', 'deep', 'FlatToDeepROne'), ('flat', 'flat', 'FlatToFlatROne')]:
                um = {'deep': dt.trained_um.max(), 'flat': dt.trained_um.min()}
                r = dt[(dt.flow == f) & np.isclose(dt.trained_um, um[tr]) & np.isclose(dt.tested_um, um[te])]
                if len(r):
                    macro(f'Depth{name}{k}Fone', r.f1.iloc[0])

    # ---- the propagation layer calibrates itself (pilot_five_reps_alpha.csv)
    al = csv('pilot_five_reps_alpha')
    if len(al):
        macro('AlphaZCalibMm', al.z_calibrated_mm.mean(), '{:.2f}')
        macro('AlphaChangeLoPct', -100 * al.change.max(), '{:.1f}')
        macro('AlphaChangeHiPct', -100 * al.change.min(), '{:.1f}')

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
        j = json.loads(hd.read_text())
        d = next((j[k] for k in ('axis_um', 'D_axis_um', 'D_ef_axis_um') if isinstance(j.get(k), (int, float))), None)
        macro('HoloDiameterUm', d, '{:.0f}')

    # ---- the parameter table: counts by source
    pt = csv('simulator_parameters')
    if len(pt):
        modelled = pt[~pt.code_name.astype(str).str.contains(r'not modelled|derived', regex=True)]
        macro('ParamCount', len(modelled), '{}')
        for t, k in [('article', 'Article'), ('datasheet', 'Datasheet'), ('personal communication', 'Personal'),
                     ('our assumption', 'Assumption')]:
            macro(f'Param{k}', int((modelled.source_type == t).sum()), '{}')
    return M, fam


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
        return 'pers.\\ comm.'
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
        'depth spread of objects': (f'$\\mathcal{{N}}(0,{g(c["depth_std"] * 1e6)}^2)$, $\\le${g(c["depth_max"] * 1e6)}'
                                    '\\,$\\mu$m',
                                    f'$\\mathcal{{N}}(0,{g(b["depth_std"] * 1e6)}^2)$, $\\le${g(b["depth_max"] * 1e6)}'
                                    '\\,$\\mu$m' + (f'; depth set {g(deep["physics"]["depth_std"] * 1e6)}, '
                                                    f'$\\le${g(deep["physics"]["depth_max"] * 1e6)}' if deep else '')),
        'absorption of the letters': (f'$\\mathcal{{N}}({g(c["absorption_mean"])},{g(c["absorption_std"])}^2)$ in '
                                      f'$[{g(c["absorption_min"])},1]$', same),
        'phase delay of the letters': (f'$\\mathcal{{N}}({g(c["phase_mean"])},{g(c["phase_std"])}^2)$\\,rad in '
                                       f'$[0,{g(c["phase_max"])}]$', same),
        'letter size (base)': (side(CBMS), side(SPARSE)),
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
        'sample-to-sensor distance': 'CBMS: our reading of the routine of~\\cite{%s}; 1.0\\,mm: pers.\\ comm.\\ '
                                     '($z\\approx1$\\,mm)' % cite['cbms'],
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


CITE = dict(article='sobieranski2015portable', led='thorlabsM385L2', sensor='onsemiMT9J003', cbms='rockembach')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', default=str(paths.PAPER), help='directory of the figures of the paper (figures/paper)')
    write(ap.parse_args().out, CITE)
