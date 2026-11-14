"""Tables, numbers and figures of the distance and autofocus study (docs/exp_distancia/PROTOCOLO.md, sections 7-9, and
the freeze of CADERNO.md), from the csv files of the study. A missing result gives '--' (table), '?' (macro) or a
figure left out, never an error.

    python -m holo_openset paper distance
    -> <HOLO_PAPER>/distance/numbers_distancia.tex     macros \\Dist..., letters only, apart from those of the paper
       <HOLO_PAPER>/distance/tables/<name>.tex         bodies of tabular environments, as the tables of the paper
       <HOLO_PAPER>/distance/tables/<name>.md          the same table in GitHub Markdown, with a header, for a report
       <HOLO_PAPER>/distance/figures/<name>.pdf, .png, captions.md

Inputs under HOLO_RESULTS (results_exp_distancia): robustness.csv, robustness_sessions.csv, focus_error.csv,
focus_error_sessions.csv, focus_sweep.csv, the full-frame triples NAME.csv, NAME_time.csv, NAME_focus.csv, and the
timing of the single measurement session in HOLO_DIST_TIMING (default 'e5', relative to HOLO_RESULTS or absolute):
timing_gpu.csv (min_s), timing_cpu.csv (median_s), full_frames_time.csv and full_frames.csv. HOLO_DIST_TIMING_CPU, if
set, takes timing_cpu.csv from another directory (only to try the module on stand-in timings: the protocol compares
times of one run only).

Every time of a flow that is not a stage of its own is a SUM OF MEASURED STAGE TIMES (FRONT), not a measurement end to
end; the flows that reuse a distance (AMORTISED) divide the search by the images that share it.
"""
import math
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.ticker import FormatStrFormatter, LogLocator, NullFormatter

from holo_openset import paths
from holo_openset.paper.style import COLORS as PAPER_COLORS, INK, MUTED, panel, plt, setup
from holo_openset.paper.tables import DIGITS, tex
from holo_openset.sim.physics import PIXEL, Z0
from holo_openset.sim.variants import ALL as ALL_VARIANTS

M = {}   # macros of this module only, all named \Dist...

# ------------------------------------------------------------------------------------------------ what is compared
SETS = ['base', 'session_2', 'session_5', 'frame_2', 'frame_5', 'walk_05', 'fullwell_500', 'beam_narrow']
FLOWS = ['rec_z0', 'rec_af', 'rec_afs', 'rec_afsc', 'rec_afM', 'rec_afc', 'rec_afr', 'prop', 'bank_jit', 'bank_wide',
         'bank_w2']                                                      # the window sets (test matrix of the freeze)
FLOWS_FULL = ['rec_z0', 'rec_af', 'rec_afs', 'rec_afsc', 'rec_afc', 'rec_afr', 'rec_edfw', 'prop', 'bank_jit',
              'bank_wide', 'bank_w2']                                    # the full frames (E1, E2, E4)
TILT_FLOWS = ['rec_z0', 'rec_af', 'rec_edfw', 'rec_afc', 'bank_jit', 'bank_wide', 'bank_w2']
STACKS = ['bank_jit', 'bank_wide', 'bank_w2']
PAIRS = [('rec_afs', 'rec_af'), ('rec_afsc', 'rec_af'), ('rec_afc', 'rec_af'), ('rec_afr', 'rec_af'),
         ('rec_afM', 'rec_af'), ('bank_jit', 'rec_afc'), ('bank_wide', 'rec_afc'), ('bank_w2', 'rec_afc'),
         ('bank_wide', 'rec_af')]
FRAME_PAIRS = [('rec_afc', 'rec_af'), ('bank_jit', 'rec_afc'), ('bank_wide', 'rec_afc'), ('bank_w2', 'rec_afc'),
               ('rec_edfw', 'rec_afc')]                                  # the full frames, where both flows ran
CONV_FLOWS = ['rec_z0', 'rec_af', 'rec_afs', 'rec_afsc', 'rec_afM', 'rec_afc', 'rec_afr']   # conventional (criterion)
F1_TOL = 0.02                       # protocol, section 3: the stack within 0.02 of the best conventional flow
METHODS = ['af', 'afs', 'afsc', 'afM', 'afc', 'afr']                     # focus_error.csv: the searches of the distance
SESSION_SETS = ['session_5', 'fullwell_500', 'beam_narrow']
VAL_SETS = [('realistic', 'realistic'), ('variants_val/frame_5', 'frame_5'),
            ('variants_val/fullwell_500', 'fullwell_500'), ('variants_val/beam_narrow', 'beam_narrow')]
VAL_CANDIDATES = [('blind-b1-tog', 'reference (paper)'), ('r10b-b4-tog', 'afc (frozen)'), ('r15b-b2-s2', 'afr (frozen)'),
                  ('r10b-b1-tog', 'narrow range only'), ('blind-b4-tog', 'binning 4 only'),
                  ('blind-b1-s2', 'smoothing only'), ('r10b-b8-tog', 'narrow range, binning 8')]
TILTS = [0, 1, 2, 5, 10, 15]
FRAME_SETS = [('full_frames', 'Paper', 'frames of the paper (distance per session)'),
              ('full_frames_frame5', 'FrameFive', 'distance per frame 5 %')] + \
             [(f'full_frames_tilt{t}', f'Tilt{["Zero", "One", "Two", "Five", "Ten", "Fifteen"][i]}', f'tilt {t} deg')
              for i, t in enumerate(TILTS)]
SET_SHORT = {'base': 'base (bench)', 'session_2': 'between sessions 2 %', 'session_5': 'between sessions 5 %',
             'frame_2': 'per frame 2 %', 'frame_5': 'per frame 5 %', 'walk_05': 'drift 0.5 % per frame',
             'fullwell_500': 'full well 500 e$^-$', 'beam_narrow': 'narrow beam'}
F1, GROSS, N_SESSION, M_REFOCUS, FRAMES_PER_SESSION = 'novel_open_macro_f1', 0.01, 100, 10, 5
FULL, WINDOW = (2748, 3840), (640, 640)
HALF_WIDTH_UM = 3840 * PIXEL / 2 * 1e6           # half the width of the sensor: 3.2 mm

# ------------------------------------------------------------------------------------------------ the look
COLORS = {**{f: PAPER_COLORS[f] for f in ['rec_z0', 'rec_af', 'prop', 'bank_jit']},   # the paper keeps its colours
          'rec_afs': '#a3195b', 'rec_afsc': '#c77c02', 'rec_afM': '#b05fa0', 'rec_afc': '#1f4e9c',
          'rec_afr': '#8e3b2f', 'rec_edfw': '#2e9e48', 'bank_wide': '#8fa31f', 'bank_w2': '#55c08a'}
MARKERS = {'rec_z0': 's', 'rec_af': 'o', 'rec_afs': 'D', 'rec_afsc': 'd', 'rec_afM': 'p', 'rec_afc': 'v',
           'rec_afr': '^', 'rec_edfw': 'P', 'prop': 'X', 'bank_jit': '<', 'bank_wide': '>', 'bank_w2': '*'}
SHORT = {'rec_z0': 'rec. $z_0$', 'rec_af': 'autofocus', 'rec_afs': 'AF once/session', 'rec_afsc': 'cheap AF once/session',
         'rec_afM': 'AF every 10', 'rec_afc': 'cheap AF', 'rec_afr': 'robust AF', 'rec_edfw': 'per-object (wide)',
         'prop': 'prop.', 'bank_jit': 'stack 5', 'bank_wide': 'stack 7', 'bank_w2': 'stack 9'}

# ------------------------------------------------------------------------------------------------ cost accounting
# The front end of each flow as a sum of measured stage times: (stage, divisor); 'n' = the images that share one
# search of the distance (N_SESSION by default, a session of the dataset). The flows of the study that reuse a distance
# are AMORTISED: their time is a sum of measured times, not a measurement of the flow.
FRONT = {
    'rec_z0': [('flat_field', 1), ('backprop', 1), ('channels', 1)],
    'rec_af': [('flat_field', 1), ('autofocus', 1), ('backprop', 1), ('channels', 1)],
    'rec_afs': [('flat_field', 1), ('autofocus', 'n'), ('backprop', 1), ('channels', 1)],
    'rec_afM': [('flat_field', 1), ('autofocus', M_REFOCUS), ('backprop', 1), ('channels', 1)],
    'rec_afc': [('flat_field', 1), ('autofocus_afc', 1), ('backprop', 1), ('channels', 1)],
    'rec_afr': [('flat_field', 1), ('autofocus_afr', 1), ('backprop', 1), ('channels', 1)],
    'rec_afsc': [('flat_field', 1), ('autofocus_afc', 'n'), ('backprop', 1), ('channels', 1)],
    'rec_edfw': [('flat_field', 1), ('autofocus', 1), ('per_object_wide', 1), ('channels', 1)],
    'prop': [('layer_prop', 1)], 'bank_jit': [('layer_bank_jit', 1)], 'bank_wide': [('layer_bank_wide', 1)],
    'bank_w2': [('layer_bank_w2', 1)],
}
AMORTISED = [f for f, st in FRONT.items() if any(d != 1 for _, d in st)]    # rec_afs, rec_afM, rec_afsc
BACK_END = ['yolo_tiled', 'embed', 'decide']                                # end to end = front end + these
TIME_FLOWS = ['rec_z0', 'rec_af', 'rec_afs', 'rec_afsc', 'rec_afM', 'rec_afc', 'rec_afr', 'rec_edfw', 'prop',
              'bank_jit', 'bank_wide', 'bank_w2']
LAYER = {'bank_jit': 'layer_bank_jit', 'bank_wide': 'layer_bank_wide', 'bank_w2': 'layer_bank_w2'}
SEARCHES = [('blind', 'autofocus', 'rec_af', 'rec_afs'), ('afc', 'autofocus_afc', 'rec_afc', 'rec_afsc'),
            ('afr', 'autofocus_afr', 'rec_afr', None)]     # name, stage, flow on every image, flow once per session
CONVENTIONAL = ['flat_field', 'backprop', 'channels']       # what a reconstruction costs besides the search


def front_end(flow, t, n=N_SESSION):
    """Front end of a flow (s) from the stage times t {stage: s}; None if a stage was not measured."""
    total = 0.0
    for st, div in FRONT[flow]:
        v = t.get(st)
        if v is None or not np.isfinite(v):
            return None
        total += v / (n if div == 'n' else div)
    return total


def end_to_end(flow, t, n=N_SESSION):
    f = front_end(flow, t, n)
    if f is None or any(t.get(s) is None or not np.isfinite(t[s]) for s in BACK_END):
        return None
    return f + sum(t[s] for s in BACK_END)


def break_even(t, stack, search, simple=False):
    """Frames per mounting above which searching once per mounting is cheaper than the focal stack.
    Complete accounting: n* = T_search / (T_layer - (T_flat_field + T_backprop + T_channels)); simple (protocol, Q2):
    n* = T_search / (T_layer - T_backprop). math.inf if the stack is cheaper at every n; None if not measured."""
    need = [search, LAYER[stack]] + (['backprop'] if simple else CONVENTIONAL)
    if any(t.get(s) is None or not np.isfinite(t[s]) for s in need):
        return None
    den = t[LAYER[stack]] - sum(t[s] for s in (['backprop'] if simple else CONVENTIONAL))
    return math.inf if den <= 0 else t[search] / den


# ------------------------------------------------------------------------------------------------ helpers
def out():
    return paths.PAPER / 'distance'


def tt(name):
    return '\\texttt{' + str(name).replace('_', '\\_') + '}'


def camel(s):
    return ''.join(w[:1].upper() + w[1:] for w in re.split(r'[^0-9A-Za-z]+', str(s)) if w)


def macro(name, value, fmt='{:.3f}'):
    """\\Dist<name>: letters only (digits spelled out as tables.macro does); '?' if missing; inf -> $\\infty$."""
    name = 'Dist' + ''.join(DIGITS.get(c, c) for c in name if c.isalnum())
    if value is None or (isinstance(value, float) and np.isnan(value)):
        M[name] = '?'
    elif isinstance(value, str):
        M[name] = value
    elif isinstance(value, float) and math.isinf(value):
        M[name] = '$\\infty$'
    else:
        M[name] = fmt.format(value)


def ok(v):
    return v is not None and isinstance(v, (int, float, np.floating, np.integer)) and np.isfinite(v)


def num(v, k=3, sign=False):
    return f'{v:+.{k}f}' if ok(v) and sign else f'{v:.{k}f}' if ok(v) else '--'


def pm(x, k=3):
    """mean ± std (Markdown), '--' if empty."""
    x = pd.Series(x, dtype=float).dropna()
    if not len(x):
        return '--'
    return f'{x.mean():.{k}f}' + (f' ± {x.std():.{k}f}' if len(x) > 1 else '')


def mean(x):
    x = pd.Series(x, dtype=float).dropna()
    return float(x.mean()) if len(x) else None


def adaptive(v):
    """A time in its unit: 3 significant places at most, '--' if not measured."""
    if not ok(v):
        return '--'
    return f'{v:.2f}' if abs(v) < 1 else f'{v:.1f}' if abs(v) < 100 else f'{v:.0f}'


def nstar_text(v, latex=True):
    if v is None:
        return '--'
    if math.isinf(v):
        return '$\\infty$' if latex else 'never'
    return f'{v:.1f}' if v < 10 else f'{v:.0f}'


def load(name, root=None):
    f = Path(root or paths.RESULTS) / f'{name}.csv'
    try:
        return pd.read_csv(f) if f.exists() else pd.DataFrame()
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        return pd.DataFrame()


def has(df, *cols):
    return len(df) > 0 and all(c in df for c in cols)


def per_rep(df, col, **where):
    """One value per repetition (mean of duplicates) of the rows matching where."""
    if not has(df, col, 'rep', *where):
        return pd.Series(dtype=float)
    m = np.ones(len(df), bool)
    for k, v in where.items():
        m &= (df[k] == v).to_numpy()
    return df[m].groupby('rep')[col].mean()


def set_label(v, latex=True):
    if v == 'base':
        return 'base (bench)'
    eff, val, _ = ALL_VARIANTS.get(v, (v, '', {}))
    s = f'{eff}: {val}' if val != '' else str(eff)
    return tex(s) if latex else s


def effect(v):
    return 'base' if v == 'base' else ALL_VARIANTS.get(v, (v,))[0]


def dataset_of(v):
    return 'realistic' if v == 'base' else f'variants/{v}'


def write(name, tex_lines, header, md_rows, notes=(), comment=()):
    d = out() / 'tables'
    d.mkdir(parents=True, exist_ok=True)
    head = [f'% {c}' for c in comment]
    (d / f'{name}.tex').write_text('\n'.join(head + list(tex_lines)) + '\n')
    md = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join(['---'] * len(header)) + '|']
    md += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in md_rows]
    if notes:
        md += [''] + [f'{n}' for n in notes]
    (d / f'{name}.md').write_text('\n'.join(md) + '\n')
    print('wrote', d / f'{name}.tex', '(+ .md)')


def reps_note(df):
    r = sorted(df.rep.dropna().astype(int).unique()) if has(df, 'rep') else []
    return f'repetitions present: {", ".join(f"r{x}" for x in r) if r else "none"}'


# ------------------------------------------------------------------------------------------------ timing
def rel(p):
    """A directory of results as it is named under HOLO_RESULTS, for the notes of the tables."""
    try:
        return str(Path(p).relative_to(paths.RESULTS)) or '.'
    except ValueError:
        return str(p)


def timing_dirs():
    t = os.environ.get('HOLO_DIST_TIMING', 'e5')
    g = Path(t) if Path(t).is_absolute() else paths.RESULTS / t
    c = os.environ.get('HOLO_DIST_TIMING_CPU')
    c = g if not c else Path(c) if Path(c).is_absolute() else paths.RESULTS / c
    return g, c


def load_timing():
    """{'gpu' | 'cpu': {(height, width): {stage: seconds}}}: min_s on the GPU, median_s on one CPU core (the paper)."""
    g, c = timing_dirs()
    res = {}
    for dev, root, key in [('gpu', g, 'min_s'), ('cpu', c, 'median_s')]:
        df, d = load(f'timing_{dev}', root), {}
        if has(df, 'height', 'width', 'stage', key):
            for (h, w), x in df.groupby(['height', 'width']):
                d[(int(h), int(w))] = dict(zip(x.stage, x[key].astype(float)))
        res[dev] = d
    return res


# ------------------------------------------------------------------------------------------------ window sets
def tab_dist_metrics():
    """F1, rejection of the unseen, AUROC and accuracy on the seen classes: sets x flows (models of the base set)."""
    d = load('robustness')
    for col, name, key, mac in [(F1, 'tab_dist_f1', 'Fone', True),
                                ('novel_unknown_rejection', 'tab_dist_rejection', 'Rej', True),
                                ('novel_auroc', 'tab_dist_auroc', 'Auroc', False),
                                ('novel_known_acc', 'tab_dist_known', 'Known', False)]:
        base = {f: mean(per_rep(d, col, variant='base', flow=f)) for f in FLOWS}
        lines, md, prev = [], [], 'base'
        for v in SETS:
            if v != 'base' and effect(v) != prev:
                lines.append('\\midrule')
            prev = effect(v)
            ct, cm = [], []
            for f in FLOWS:
                x = per_rep(d, col, variant=v, flow=f)
                m = mean(x)
                bold = v != 'base' and ok(m) and ok(base[f]) and m < base[f] - 0.05
                ct.append(f'\\textbf{{{m:.2f}}}' if bold else num(m, 2))
                cm.append(f'**{pm(x)}**' if bold else pm(x))
                if mac:
                    macro(f'{key}{camel(v)}{camel(f)}', m)
            lines.append(f'{set_label(v)} & ' + ' & '.join(ct) + ' \\\\')
            md.append([set_label(v, False)] + cm)
        write(name, lines, ['set'] + FLOWS, md,
              notes=[f'{col}, mean ± std over the repetitions ({reps_note(d)}); models, galleries and thresholds of the '
                     'base set. Bold: more than 0.05 below the same flow on base (the rule of the paper).'],
              comment=[f'{col}: rows ' + ', '.join(SETS), 'columns: ' + ', '.join(FLOWS)])


def tab_dist_paired():
    """Paired differences of F1 per repetition (same scenes, same repetition), and how many share the sign of the
    mean."""
    d = load('robustness')
    reps = sorted(set(range(1, 6)) | (set(d.rep.dropna().astype(int)) if has(d, 'rep') else set()))
    lines, md = [], []
    for i, v in enumerate(SETS):
        if i:
            lines.append('\\midrule')
        for j, (a, b) in enumerate(PAIRS):
            diff = (per_rep(d, F1, variant=v, flow=a) - per_rep(d, F1, variant=v, flow=b)).dropna()
            m = float(diff.mean()) if len(diff) else None
            k = int((np.sign(diff) == np.sign(m)).sum()) if len(diff) else 0
            sign = f'{k}/{len(diff)}' if len(diff) else '--'
            cells = [num(diff.get(r), 3, sign=True) for r in reps]
            pair = f'{a} − {b}'
            lines.append(f'{set_label(v) if j == 0 else ""} & {tt(a)} $-$ {tt(b)} & {num(m, 3, sign=True)} & ' +
                         ' & '.join(cells) + f' & {sign} \\\\')
            md.append([set_label(v, False) if j == 0 else '', pair, num(m, 3, sign=True)] + cells + [sign])
            macro(f'Pair{camel(v)}{camel(a)}Minus{camel(b)}', m, '{:+.3f}')
            macro(f'PairSign{camel(v)}{camel(a)}Minus{camel(b)}', sign if len(diff) else None)
    write('tab_dist_paired', lines, ['set', 'pair', 'mean'] + [f'r{r}' for r in reps] + ['same sign'], md,
          notes=['Open-set F1 of the first flow minus the second, per repetition (the same test scenes and the same '
                 'held-out classes); "same sign": repetitions whose difference has the sign of the mean.'],
          comment=['set & pair & mean difference & ' + ' & '.join(f'r{r}' for r in reps) + ' & same sign'])


def tab_dist_focus():
    """Distance error on the test split per set and search (focus_error.csv)."""
    e = load('focus_error')
    lines, md = [], []
    for i, v in enumerate(SETS):
        if i:
            lines.append('\\midrule')
        for j, m in enumerate(METHODS):
            x = e[(e['set'] == dataset_of(v)) & (e.method == m)] if has(e, 'set', 'method') else pd.DataFrame()
            r = x.iloc[-1] if len(x) else {}
            med, p90, g, rec = (r.get(k) if len(x) else None for k in ['median_um', 'p90_um', 'gross',
                                                                       'reconstructions_per_image'])
            cells = [adaptive(rec), num(med, 0), num(p90, 0), num(100 * g if ok(g) else None, 1)]
            lines.append(f'{set_label(v) if j == 0 else ""} & \\texttt{{{m}}} & ' + ' & '.join(cells) + ' \\\\')
            md.append([set_label(v, False) if j == 0 else '', m] + cells)
            k = f'Err{camel(v)}{camel(m)}'
            macro(f'{k}Median', med, '{:.0f}')
            macro(f'{k}PNinety', p90, '{:.0f}')
            macro(f'{k}Gross', 100 * g if ok(g) else None, '{:.1f}')
    write('tab_dist_focus', lines, ['set', 'search', 'reconstructions / image', 'median (um)', 'p90 (um)', 'gross (%)'],
          md, notes=[f'|z found − true z| on the test split; gross: share of images with an error above {GROSS:.0%} of '
                     f'the nominal distance ({GROSS * Z0 * 1e6:.1f} um).'],
          comment=['set & search & reconstructions per image & median um & p90 um & gross %'])


def tab_dist_focus_val():
    """The validation sweep: the reference, the frozen searches and the candidates that change one axis at a time."""
    s = load('focus_sweep')
    lines, md = [], []
    for i, (c, role) in enumerate(VAL_CANDIDATES):
        if i:
            lines.append('\\midrule')
        for j, (root, short) in enumerate(VAL_SETS):
            x = s[(s['set'] == root) & (s.candidate == c)] if has(s, 'set', 'candidate') else pd.DataFrame()
            r = x.iloc[-1] if len(x) else None
            g = lambda k: (float(r[k]) if r is not None and k in r and pd.notna(r[k]) else None)   # noqa: E731
            cost, rec = g('cost'), g('reconstructions')
            head = [tt(c), role, num(rec, 0), f'{cost:g}' if ok(cost) else '--'] if j == 0 else ['', '', '', '']
            cells = [short.replace('_', '\\_'), num(g('median_um'), 0), num(g('p90_um'), 0),
                     num(100 * g('gross') if ok(g('gross')) else None, 1)]
            lines.append(' & '.join(head + cells) + ' \\\\')
            md.append(([c, role, num(rec, 0), f'{cost:g}' if ok(cost) else '--'] if j == 0 else ['', '', '', ''])
                      + [short] + cells[1:])
            k = f'Val{camel(c)}{camel(short)}'
            macro(f'{k}Median', g('median_um'), '{:.0f}')
            macro(f'{k}PNinety', g('p90_um'), '{:.0f}')
            macro(f'{k}Gross', 100 * g('gross') if ok(g('gross')) else None, '{:.1f}')
            if j == 0:
                macro(f'Val{camel(c)}Cost', cost, '{:g}')
                macro(f'Val{camel(c)}Reconstructions', rec, '{:.0f}')
    write('tab_dist_focus_val', lines, ['search', 'role', 'reconstructions', 'cost', 'set (val)', 'median (um)',
                                        'p90 (um)', 'gross (%)'], md,
          notes=['Validation split only (the sweep that chose the searches). Cost: in reconstructions of the whole '
                 'window (a reconstruction on the amplitude averaged b x b costs 1/b^2). Gross: error above 1 % of z0.'],
          comment=['search & role & reconstructions & cost (whole-window reconstructions) & set & median um & p90 um & '
                   'gross %'])


def tab_dist_sessions():
    """Per test session: the distance error of the searches done once per session against the search on every image,
    and the accuracy on the seen classes of those flows. One wrong search spoils the whole session."""
    e, r = load('focus_error_sessions'), load('robustness_sessions')
    lines, md = [], []
    flows = ['rec_af', 'rec_afs', 'rec_afsc']
    for i, v in enumerate(SESSION_SETS):
        if i:
            lines.append('\\midrule')
        ev = e[e['set'] == dataset_of(v)] if has(e, 'set', 'method', 'session') else pd.DataFrame()
        rv = r[r.variant == v] if has(r, 'variant', 'flow', 'session', 'known_acc') else pd.DataFrame()
        sessions = (set(ev.session.dropna().astype(int)) if len(ev) else set()) | \
            (set(rv.session.dropna().astype(int)) if len(rv) else set())
        sessions = sorted(sessions) or [None]
        gross = {m: 0 for m in ['afs', 'afsc']}
        for j, s in enumerate(sessions):
            def err(m, k='median_um'):
                x = ev[(ev.method == m) & (ev.session == s)] if len(ev) else []
                return float(x[k].iloc[-1]) if len(x) and pd.notna(x[k].iloc[-1]) else None
            zt = err('af', 'true_z_mean') or err('afs', 'true_z_mean')
            for m in gross:
                g = err(m, 'gross')
                gross[m] += int(ok(g) and g > 0.5)
            known = [per_rep(rv, 'known_acc', flow=f, session=s) if len(rv) else pd.Series(dtype=float) for f in flows]
            cells = [num(zt * 1e3 if ok(zt) else None, 3), num(err('afs'), 0), num(err('afsc'), 0), num(err('af'), 0)]
            lines.append(f'{set_label(v) if j == 0 else ""} & {s if s is not None else "--"} & ' + ' & '.join(cells) +
                         ' & ' + ' & '.join(num(mean(k), 3) for k in known) + ' \\\\')
            md.append([set_label(v, False) if j == 0 else '', s if s is not None else '--'] + cells +
                      [pm(k) for k in known])
        n = len([s for s in sessions if s is not None])
        macro(f'Ses{camel(v)}Sessions', n if n else None, '{}')
        for m in gross:
            macro(f'Ses{camel(v)}{camel(m)}GrossSessions', gross[m] if n else None, '{}')
        for f in flows:
            acc = rv[rv.flow == f].groupby('session').known_acc.mean() if len(rv) else pd.Series(dtype=float)
            macro(f'Ses{camel(v)}{camel(f)}KnownMin', float(acc.min()) if len(acc) else None)
            macro(f'Ses{camel(v)}{camel(f)}KnownMax', float(acc.max()) if len(acc) else None)
    write('tab_dist_sessions', lines, ['set', 'session', 'true z (mm)', 'afs error (um)', 'afsc error (um)',
                                       'af median error (um)'] + [f'{f} known acc.' for f in flows], md,
          notes=['Distance error of the search done once per session (afs, afsc: one distance for the whole session) '
                 'and median error of the search on every image (af); accuracy on the seen classes (accepted and '
                 f'correct) per session, mean ± std over the repetitions ({reps_note(r)}). An error above '
                 f'{GROSS * Z0 * 1e6:.0f} um (1 % of z0) is a gross failure.'],
          comment=['set & session & true z mm & afs err um & afsc err um & af median err um & known acc rec_af & '
                   'rec_afs & rec_afsc'])


def tab_dist_own():
    """The cheap autofocus with the model it borrows (rec_af) against a model trained on its own images, r1."""
    d = load('robustness')
    lines, md, diffs = [], [], {}
    for v in SETS:
        a, b = per_rep(d, F1, variant=v, flow='rec_afc'), per_rep(d, F1, variant=v, flow='rec_afc+own')
        a, b = a.get(1), b.get(1)
        diff = b - a if ok(a) and ok(b) else None
        if ok(diff):
            diffs[v] = diff
        cells = [num(a, 3), num(b, 3), num(diff, 3, sign=True)]
        lines.append(f'{set_label(v)} & ' + ' & '.join(cells) + ' \\\\')
        md.append([set_label(v, False)] + cells)
        macro(f'Own{camel(v)}Diff', diff, '{:+.3f}')
    worst = max(diffs, key=lambda k: abs(diffs[k])) if diffs else None
    macro('OwnMaxAbsDiff', abs(diffs[worst]) if worst else None)
    macro('OwnMaxSet', set_label(worst) if worst else None)
    write('tab_dist_own', lines, ['set', 'rec_afc (model of rec_af)', 'rec_afc+own', 'own − borrowed'], md,
          notes=['Open-set F1, repetition 1. The protocol (6.4) asks that the borrowed model change F1 by at most '
                 f'0.01; largest |difference|: {num(abs(diffs[worst]), 3) if worst else "--"}'
                 f'{f" ({set_label(worst, False)})" if worst else ""}.'],
          comment=['set & F1 rec_afc (borrowed model) & F1 rec_afc+own & difference'])


# ------------------------------------------------------------------------------------------------ cost
def tab_dist_time():
    """Front end and end to end per flow on the full frame and on the 640 window, one GPU and one CPU core."""
    T = load_timing()
    gb, cb, gs, cs = (T['gpu'].get(FULL, {}), T['cpu'].get(FULL, {}), T['gpu'].get(WINDOW, {}),
                      T['cpu'].get(WINDOW, {}))
    ref = {k: (front_end('bank_jit', t), end_to_end('bank_jit', t)) for k, t in [('gpu', gb), ('cpu', cb)]}
    lines, md = [], []
    for f in TIME_FLOWS:
        vals = []
        for t, scale, tag in [(gb, 1e3, 'GpuBigMs'), (cb, 1, 'CpuBigS'), (gs, 1e3, 'GpuSmallMs'), (cs, 1e3, 'CpuSmallMs')]:
            fe, ee = front_end(f, t), end_to_end(f, t)
            vals += [fe * scale if ok(fe) else None, ee * scale if ok(ee) else None]
            macro(f'Time{camel(f)}Front{tag}', vals[-2], '{:.2f}' if tag == 'GpuSmallMs' else '{:.1f}' if 'Ms' in tag
                  else '{:.2f}')
            macro(f'Time{camel(f)}Total{tag}', vals[-1], '{:.2f}' if tag == 'GpuSmallMs' else '{:.1f}' if 'Ms' in tag
                  else '{:.2f}')
        ratios = []
        for dev, t in [('gpu', gb), ('cpu', cb)]:
            fe, ee = front_end(f, t), end_to_end(f, t)
            rf = fe / ref[dev][0] if ok(fe) and ok(ref[dev][0]) else None
            re_ = ee / ref[dev][1] if ok(ee) and ok(ref[dev][1]) else None
            ratios.append(f'{num(rf, 2)} / {num(re_, 2)}')
            tag = {'gpu': 'GpuBig', 'cpu': 'CpuBig'}[dev]
            macro(f'Time{camel(f)}FrontRatio{tag}', rf, '{:.2f}')
            macro(f'Time{camel(f)}TotalRatio{tag}', re_, '{:.2f}')
        name = f + ('$^\\dagger$' if f in AMORTISED else '')
        lines.append(tt(f) + ('$^\\dagger$' if f in AMORTISED else '') + ' & ' +
                     ' & '.join(adaptive(v) for v in vals) + ' & ' + ' & '.join(ratios) + ' \\\\')
        md.append([name.replace('$^\\dagger$', ' †')] + [adaptive(v) for v in vals] + ratios)
    for st in sorted({s for v in FRONT.values() for s, _ in v} | set(BACK_END)):
        for t, scale, tag, fmt in [(gb, 1e3, 'GpuBigMs', '{:.2f}'), (cb, 1, 'CpuBigS', '{:.2f}'),
                                   (gs, 1e3, 'GpuSmallMs', '{:.3f}'), (cs, 1e3, 'CpuSmallMs', '{:.1f}')]:
            macro(f'Stage{camel(st)}{tag}', t[st] * scale if ok(t.get(st)) else None, fmt)
    macro('SessionN', N_SESSION, '{}')
    macro('RefocusM', M_REFOCUS, '{}')
    am = ', '.join(f'{f} (search / {"n" if any(d == "n" for _, d in FRONT[f]) else M_REFOCUS})' for f in AMORTISED)
    comp = '; '.join(f'{f} = ' + ' + '.join(s if d == 1 else f'{s}/{d}' for s, d in FRONT[f]) for f in TIME_FLOWS)
    g, c = map(rel, timing_dirs())
    write('tab_dist_time', lines,
          ['flow', 'GPU front (ms), frame', 'GPU total (ms), frame', 'CPU front (s), frame', 'CPU total (s), frame',
           'GPU front (ms), 640', 'GPU total (ms), 640', 'CPU front (ms), 640', 'CPU total (ms), 640',
           'x stack 5, GPU frame (front / total)', 'x stack 5, CPU frame (front / total)'], md,
          notes=['Sums of measured stage times (timing_gpu.csv: minimum of the repetitions; timing_cpu.csv: one core, '
                 f'median), NOT measurements end to end. Total = front end + {" + ".join(BACK_END)}. '
                 f'† amortised: {am}, n = {N_SESSION} (a session of the dataset). Frame = {FULL[1]} x {FULL[0]} px, '
                 f'640 = the 640 x 640 window. Timing from {g} (GPU) and {c} (CPU).', 'Composition: ' + comp + '.'],
          comment=['SUMS OF MEASURED STAGE TIMES (not end-to-end measurements); total = front end + ' +
                   ' + '.join(BACK_END), 'composition: ' + comp, f'amortised rows (dagger): {am}; n = {N_SESSION}',
                   'columns: flow & GPU front ms & GPU total ms & CPU front s & CPU total s (full frame) & GPU front ms '
                   '& GPU total ms & CPU front ms & CPU total ms (640 window) & front/total over bank_jit, GPU & CPU '
                   '(full frame)', f'timing: GPU {g}, CPU {c}'])


def tab_dist_breakeven():
    """n* for every stack and search, full frame, GPU and CPU; and per frame (n = 1) the front end of the search on
    every image over the front end of the stack."""
    T = load_timing()
    lines, md = [], []
    for i, s in enumerate(STACKS):
        if i:
            lines.append('\\midrule')
        for j, (name, stage, every, _) in enumerate(SEARCHES):
            row = []
            for dev in ['gpu', 'cpu']:
                t = T[dev].get(FULL, {})
                ta = t.get(stage)
                full, simple = break_even(t, s, stage), break_even(t, s, stage, simple=True)
                fe, fs = front_end(every, t), front_end(s, t)
                ratio = fe / fs if ok(fe) and ok(fs) and fs > 0 else None
                row.append((ta * (1e3 if dev == 'gpu' else 1) if ok(ta) else None, full, simple, ratio))
                tag = camel(dev)
                macro(f'Nstar{camel(s)}{camel(name)}{tag}', full, '{:.1f}' if ok(full) and full < 10 else '{:.0f}')
                macro(f'NstarSimple{camel(s)}{camel(name)}{tag}', simple,
                      '{:.1f}' if ok(simple) and simple < 10 else '{:.0f}')
                macro(f'PerFrame{camel(every)}Over{camel(s)}{tag}', ratio, '{:.1f}')
            cells_t = [c for ta, full, simple, ratio in row for c in
                       (adaptive(ta), nstar_text(full), nstar_text(simple), num(ratio, 1))]
            cells_m = [c for ta, full, simple, ratio in row for c in
                       (adaptive(ta), nstar_text(full, False), nstar_text(simple, False), num(ratio, 1))]
            lab = tt(s) if j == 0 else ''
            lines.append(f'{lab} & {name} & ' + ' & '.join(cells_t) + ' \\\\')
            md.append([s if j == 0 else '', name] + cells_m)
    for dev in ['gpu', 'cpu']:          # how many times cheaper the frozen searches are than the blind one, full frame
        t = T[dev].get(FULL, {})
        for name, stage, _, _ in SEARCHES[1:]:
            r = t['autofocus'] / t[stage] if ok(t.get('autofocus')) and ok(t.get(stage)) and t[stage] > 0 else None
            macro(f'SearchBlindOver{camel(name)}{camel(dev)}', r, '{:.0f}')
    g, c = map(rel, timing_dirs())
    write('tab_dist_breakeven', lines,
          ['stack', 'search', 'GPU search (ms)', 'GPU n*', 'GPU n* simple', 'GPU per frame (x)', 'CPU search (s)',
           'CPU n*', 'CPU n* simple', 'CPU per frame (x)'], md,
          notes=['Full frame. n*: frames per mounting above which searching the distance once per mounting is cheaper '
                 'than the focal stack. Complete accounting (the main figure): n* = T_search / (T_layer − (T_flat_field '
                 '+ T_backprop + T_channels)); simple (protocol, Q2): n* = T_search / (T_layer − T_backprop); "never": '
                 'the stack is cheaper at every n. Per frame: the front end of the search on every image (rec_af, '
                 'rec_afc, rec_afr) over the front end of the stack, n = 1. Sums of measured stage times; timing from '
                 f'{g} (GPU, minimum) and {c} (CPU, one core, median).'],
          comment=['stack & search & GPU search ms & GPU n* & GPU n* simple & GPU per-frame ratio & CPU search s & '
                   'CPU n* & CPU n* simple & CPU per-frame ratio', 'n* = T_search / (T_layer - (T_flat_field + '
                   'T_backprop + T_channels)); simple: T_search / (T_layer - T_backprop); $\\infty$: never',
                   f'timing: GPU {g}, CPU {c}'])


READINGS = {'A': 'conventional flows with F1 >= best - 0.02 (the tolerance given to the stack)',
            'B': 'conventional flows with F1 >= the F1 of the stack'}


def criterion(f1, stack, gpu, cpu, tol=F1_TOL):
    """The pre-registered criterion of a legitimate gain of time (protocol, section 3), applied mechanically to one set
    and one stack. f1: {flow: mean F1}; gpu, cpu: {flow: front end}. The stack must have F1 >= best - tol, best being
    the highest mean F1 among the conventional flows (CONV_FLOWS), and a front end cheaper than the cheapest
    conventional flow 'that reaches this F1', which reads two ways, both computed: A, the conventional flows with
    F1 >= best - tol; B, those with F1 >= the F1 of the stack. Cheapest on the GPU and on the CPU separately.
    -> {'best', 'f1_ok', 'A' | 'B': {'gpu': flow | None, 'cpu': flow | None, 'cheaper_gpu', 'cheaper_cpu', 'verdict'}};
    None if the stack or no conventional flow has an F1."""
    conv = {f: f1[f] for f in CONV_FLOWS if ok(f1.get(f))}
    if not conv or not ok(f1.get(stack)):
        return None
    best = max(conv, key=conv.get)
    res = {'best': best, 'f1_ok': f1[stack] >= conv[best] - tol}
    for r, thr in [('A', conv[best] - tol), ('B', f1[stack])]:
        q = [f for f in conv if conv[f] >= thr]
        x = {}
        for dev, c in [('gpu', gpu), ('cpu', cpu)]:
            qc = [f for f in q if ok(c.get(f))]
            x[dev] = min(qc, key=c.get) if qc else None
            x[f'cheaper_{dev}'] = c[stack] < c[x[dev]] if x[dev] and ok(c.get(stack)) else None
        if not res['f1_ok']:
            v = 'F1 fails'
        elif not q:
            v = 'none reaches it'
        elif x['cheaper_gpu'] is None or x['cheaper_cpu'] is None:
            v = '--'
        else:
            v = {(True, True): 'met (GPU and CPU)', (True, False): 'cheaper on GPU only',
                 (False, True): 'cheaper on CPU only', (False, False): 'not cheaper'}[(x['cheaper_gpu'],
                                                                                     x['cheaper_cpu'])]
        x['verdict'] = v
        res[r] = x
    return res


def tab_dist_criterion():
    """The criterion of section 3 of the protocol on the eight window sets and the three stacks: F1 of the windows,
    front ends of the full frame (E5; flows that reuse a distance amortised over n = N_SESSION), both readings."""
    d, T = load('robustness'), load_timing()
    tg, tc = T['gpu'].get(FULL, {}), T['cpu'].get(FULL, {})
    gpu = {f: front_end(f, tg) for f in CONV_FLOWS + STACKS}
    cpu = {f: front_end(f, tc) for f in CONV_FLOWS + STACKS}
    lines, md, met = [], [], {'A': 0, 'B': 0}

    def cost(f, c, scale, unit):
        return f'{f} {c[f] * scale:.2f} {unit}' if f and ok(c.get(f)) else (f'{f} --' if f else 'none reaches it')
    for i, v in enumerate(SETS):
        if i:
            lines.append('\\midrule')
        f1 = {f: mean(per_rep(d, F1, variant=v, flow=f)) for f in CONV_FLOWS + STACKS}
        for j, s in enumerate(STACKS):
            c = criterion(f1, s, gpu, cpu)
            k = f'Crit{camel(v)}{camel(s)}'
            if c is None:
                cells = ['--'] * 11
            else:
                diff = (per_rep(d, F1, variant=v, flow=s) - per_rep(d, F1, variant=v, flow=c['best'])).dropna()
                m = float(diff.mean()) if len(diff) else None
                sign = f'{int((np.sign(diff) == np.sign(m)).sum())}/{len(diff)}' if len(diff) else '--'
                stack_cost = f'{num(gpu[s] * 1e3 if ok(gpu[s]) else None, 2)} ms / {num(cpu[s], 2)} s'
                cells = [f'{c["best"]} {num(f1[c["best"]], 3)}', num(f1[s], 3), f'{num(m, 4, sign=True)} ({sign})',
                         'yes' if c['f1_ok'] else 'no', stack_cost]
                for r in 'AB':
                    cells += [cost(c[r]['gpu'], gpu, 1e3, 'ms'), cost(c[r]['cpu'], cpu, 1, 's'), c[r]['verdict']]
                    met[r] += c[r]['verdict'] == 'met (GPU and CPU)'
                    macro(f'{k}Verdict{r}', c[r]['verdict'])
                    for dev, cc, scale, fmt in [('Gpu', gpu, 1e3, '{:.2f}'), ('Cpu', cpu, 1, '{:.2f}')]:
                        fl = c[r][dev.lower()]
                        macro(f'{k}Cheapest{dev}{r}', tt(fl) if fl else 'none')
                        macro(f'{k}Cheapest{dev}{r}Cost', cc[fl] * scale if fl and ok(cc.get(fl)) else None, fmt)
                macro(f'{k}Best', tt(c['best']))
                macro(f'{k}Diff', m, '{:+.4f}')
                macro(f'{k}Sign', sign if len(diff) else None)
            lab = set_label(v) if j == 0 else ''
            lines.append(f'{lab} & {tt(s)} & ' + ' & '.join(cells).replace('_', '\\_').replace('−', '$-$') + ' \\\\')
            md.append([set_label(v, False) if j == 0 else '', s] + cells)
    for r in 'AB':
        macro(f'CritMetCount{r}', met[r], '{}')
    macro('CritRows', len(SETS) * len(STACKS), '{}')
    g, c_ = map(rel, timing_dirs())
    write('tab_dist_criterion', lines,
          ['set', 'stack', 'best conventional (F1)', 'stack F1', 'stack − best: mean (same sign)',
           f'F1 within {F1_TOL}', 'stack front end: GPU / CPU', 'A: cheapest qualified, GPU',
           'A: cheapest qualified, CPU', 'A: verdict', 'B: cheapest qualified, GPU', 'B: cheapest qualified, CPU',
           'B: verdict'], md,
          notes=['The criterion of section 3 of the protocol, applied mechanically: the stack has F1 within '
                 f'{F1_TOL} of the best conventional flow ({", ".join(CONV_FLOWS)}; prop is neither) and a front end '
                 'cheaper than the cheapest conventional flow "that reaches this F1", on the GPU and on the CPU. That '
                 f'phrase reads two ways, both shown: A = {READINGS["A"]}; B = {READINGS["B"]}. F1: open-set F1 of the '
                 'test windows, mean over the repetitions; stack − best: paired difference per repetition, mean and the '
                 'repetitions with the sign of the mean. Cost: front end per FULL FRAME as a sum of measured stage '
                 f'times (GPU minimum, {g}; CPU one core, median, {c_}); flows that reuse a distance amortised over '
                 f'n = {N_SESSION} frames, as in tab_dist_time. Cheapest: by the front end on that device.'],
          comment=['set & stack & best conventional (F1) & stack F1 & stack - best mean (same sign) & F1 within 0.02 & '
                   'stack front end GPU / CPU & A cheapest GPU & A cheapest CPU & A verdict & B cheapest GPU & '
                   'B cheapest CPU & B verdict',
                   f'A: {READINGS["A"]}; B: {READINGS["B"]}', f'timing: GPU {g}, CPU {c_}'])


STAGE_GROUPS = {'read': ['load', 'normalise'],
                'compute': ['reconstruct', 'autofocus', 'per_object', 'twin', 'channels', 'layer'],
                'embed + decide': ['embed', 'decide']}


def frames_per_session(focus, flow):
    if has(focus, 'flow', 'rep', 'session', 'frame'):
        x = focus[focus.flow == flow]
        if len(x):
            return float(x.groupby(['rep', 'session']).frame.nunique().median())
    return FRAMES_PER_SESSION


def measured(set_name='full_frames', root=None):
    """Per flow: medians over frames and repetitions of the stage groups of NAME_time.csv (s); 'flow': the median over
    frames and repetitions of the sum of all the stages of the flow in a frame (the detector apart); the detector; and
    the frames that share a search (None if the flow searches every frame). For a flow that shares a search, the
    search is left out of the sums per frame and its median over the frames where it ran, divided by the frames that
    share it, is added (to 'compute' and to 'flow')."""
    t, focus = load(f'{set_name}_time', root), load(f'{set_name}_focus', root)
    res = {}
    if not has(t, 'flow', 'stage', 'seconds', 'rep', 'frame'):
        return res, None
    d = t[(t.flow == 'all') & (t.stage == 'detect')].seconds
    det = float(d.median()) if len(d) else None
    for f in t.flow.unique():
        if f == 'all':
            continue
        x = t[t.flow == f]
        frames = len(x[['rep', 'frame']].drop_duplicates())
        af = x[x.stage == 'autofocus']
        amort = 0 < len(af[['rep', 'frame']].drop_duplicates()) < frames
        per = (x[x.stage != 'autofocus'] if amort else x).groupby(['rep', 'frame', 'stage']).seconds.sum() \
            .unstack('stage').fillna(0)
        g = {k: float(per[[c for c in v if c in per]].sum(1).median()) for k, v in STAGE_GROUPS.items()}
        g['flow'] = float(per.sum(1).median())
        k = None
        if amort:
            k = frames_per_session(focus, f)
            g['compute'] += float(af.seconds.median()) / k
            g['flow'] += float(af.seconds.median()) / k
        res[f] = dict(g, shared=k)
    return res, det


def tab_dist_time_measured():
    """The timed run of full frames (E5), in the format of the paper's tab_full: per flow the stage groups, the time per
    frame without and with the detector (ms) and that total over the total of the stack of the paper (bank_jit)."""
    g, _ = timing_dirs()
    res, det = measured('full_frames', g)
    acc = load('full_frames', g)
    lines, md, shared = [], [], {}
    macro('MeasDetectMs', det * 1e3 if ok(det) else None, '{:.1f}')
    tot = {f: det + r['flow'] if ok(det) else None for f, r in res.items()}
    ref = tot.get('bank_jit')
    for f in FLOWS_FULL:
        r = res.get(f)
        dt = per_rep(acc, F1, flow=f, boxes='det') if has(acc, 'boxes') else pd.Series(dtype=float)
        total = tot.get(f)
        ratio = total / ref if ok(total) and ok(ref) and ref > 0 else None
        if r and r['shared']:
            shared[f] = r['shared']
        cells = [num(r[k] * 1e3, 1) if r else '--' for k in ['read', 'compute', 'embed + decide', 'flow']] + \
                [num(total * 1e3 if ok(total) else None, 0), num(ratio, 2)]
        mark = '$^\\dagger$' if f in shared else ''
        lines.append(tt(f) + mark + ' & ' + ' & '.join(cells) + f' & {num(mean(dt), 3)} \\\\')
        md.append([f + (' †' if f in shared else '')] + cells + [pm(dt)])
        k = camel(f)
        macro(f'Meas{k}ReadMs', r['read'] * 1e3 if r else None, '{:.1f}')
        macro(f'Meas{k}ComputeMs', r['compute'] * 1e3 if r else None, '{:.1f}')
        macro(f'Meas{k}EmbedMs', r['embed + decide'] * 1e3 if r else None, '{:.1f}')
        macro(f'Meas{k}FlowMs', r['flow'] * 1e3 if r else None, '{:.1f}')
        macro(f'Meas{k}TotalMs', total * 1e3 if ok(total) else None, '{:.0f}')
        macro(f'Meas{k}OverBankJit', ratio, '{:.2f}')
        macro(f'Meas{k}Fone', mean(dt))
    note = ('† the search of the distance ran on the first frame of each session only: its median over the frames '
            'where it ran is divided by the frames of a session of the set (' +
            ', '.join(f'{f}: {v:g}' for f, v in shared.items()) + ').') if shared else \
        f'Flows that reuse a distance (rec_afs, rec_afsc): the search is divided by the frames of a session ({FRAMES_PER_SESSION}).'
    write('tab_dist_time_measured', lines, ['flow', 'read (ms)', 'compute (ms)', 'embed + decide (ms)',
                                            'without the detector (ms)', 'total with the detector (ms)', 'x stack 5',
                                            'F1 end to end'], md,
          notes=[f'Timed run of the full frames in {rel(g)}, one GPU. read = load (layers) or normalise (reconstructions: '
                 'read the frame and the blank frame and normalise); compute = reconstruction, search of the distance, '
                 'per-object focus, channels or layer. read, compute, embed + decide: medians over frames and repetitions '
                 'of each group; "without the detector": median over frames and repetitions of the sum of all the stages '
                 'of the flow in a frame (so the three groups do not add up to it exactly); total = that + the detector '
                 f'({num(det * 1e3 if ok(det) else None, 1)} ms, median). x stack 5: total over the total of bank_jit. '
                 f'F1 on the detected boxes, mean ({reps_note(acc)}).', note],
          comment=['flow & read ms & compute ms & embed+decide ms & per frame without the detector ms & total with the '
                   'detector ms & total over bank_jit & F1 (detected boxes)',
                   'groups: medians over frames and repetitions; without the detector: median of the sum per frame; '
                   'dagger: the search ran on one frame per session and is divided by the frames of a session',
                   f'source: {rel(g)}'])


# ------------------------------------------------------------------------------------------------ full frames
def tab_dist_frames():
    """End-to-end F1 (detected boxes) per flow and set of full frames, with the recall of the detector."""
    accs = {s: load(s) for s, _, _ in FRAME_SETS}
    lines, md = [], []
    for f in FLOWS_FULL:
        ct, cm = [], []
        base = mean(per_rep(accs['full_frames'], F1, flow=f, boxes='det'))
        for s, key, _ in FRAME_SETS:
            x = per_rep(accs[s], F1, flow=f, boxes='det')
            m = mean(x)
            bold = s != 'full_frames' and ok(m) and ok(base) and m < base - 0.05
            ct.append(f'\\textbf{{{m:.2f}}}' if bold else num(m, 2))
            cm.append(f'**{pm(x)}**' if bold else pm(x))
            macro(f'Frame{key}{camel(f)}Fone', m)
        lines.append(tt(f) + ' & ' + ' & '.join(ct) + ' \\\\')
        md.append([f] + cm)
    rec = []
    for s, key, _ in FRAME_SETS:
        a = accs[s]
        r = mean(a[a.boxes == 'det'].detector_recall) if has(a, 'boxes', 'detector_recall') else None
        rec.append(r)
        macro(f'Frame{key}Recall', r)
    lines += ['\\midrule', 'detector recall & ' + ' & '.join(num(r, 3) for r in rec) + ' \\\\']
    md.append(['detector recall'] + [num(r, 3) for r in rec])
    write('tab_dist_frames', lines, ['flow'] + [lab for _, _, lab in FRAME_SETS], md,
          notes=['Open-set F1 on the detected boxes (end to end), mean ± std over the repetitions present. Bold: more '
                 'than 0.05 below the same flow on the frames of the paper.'],
          comment=['rows: flows; columns: ' + ', '.join(s for s, _, _ in FRAME_SETS) + '; last row: detector recall'])


def tab_dist_frames_paired():
    """Paired differences of the end-to-end F1 (detected boxes) per repetition on the sets of full frames, where both
    flows ran; the format of tab_dist_paired."""
    accs = {s: load(s) for s, _, _ in FRAME_SETS}
    reps = sorted(set(range(1, 6)) | {int(r) for a in accs.values() if has(a, 'rep') for r in a.rep.dropna()})
    lines, md = [], []
    for s, key, lab in FRAME_SETS:
        rows = []
        for a, b in FRAME_PAIRS:
            diff = (per_rep(accs[s], F1, flow=a, boxes='det') - per_rep(accs[s], F1, flow=b, boxes='det')).dropna()
            if len(diff):
                rows.append((a, b, diff))
        if not rows:
            continue
        if lines:
            lines.append('\\midrule')
        for j, (a, b, diff) in enumerate(rows):
            m = float(diff.mean())
            sign = f'{int((np.sign(diff) == np.sign(m)).sum())}/{len(diff)}'
            cells = [num(diff.get(r), 3, sign=True) for r in reps]
            lines.append(f'{tex(lab) if j == 0 else ""} & {tt(a)} $-$ {tt(b)} & {num(m, 3, sign=True)} & ' +
                         ' & '.join(cells) + f' & {sign} \\\\')
            md.append([lab if j == 0 else '', f'{a} − {b}', num(m, 3, sign=True)] + cells + [sign])
            macro(f'FramePair{key}{camel(a)}Minus{camel(b)}', m, '{:+.3f}')
            macro(f'FramePairSign{key}{camel(a)}Minus{camel(b)}', sign)
    write('tab_dist_frames_paired', lines, ['set of full frames', 'pair', 'mean'] + [f'r{r}' for r in reps] +
          ['same sign'], md,
          notes=['End-to-end open-set F1 (boxes found by the detector) of the first flow minus the second, per '
                 'repetition (the same frames and the same held-out classes); only the pairs where both flows ran on '
                 'that set. "same sign": repetitions whose difference has the sign of the mean.'],
          comment=['set & pair & mean difference & ' + ' & '.join(f'r{r}' for r in reps) + ' & same sign'])


def tab_dist_frames_focus():
    """Distance error on the full frames, from NAME_focus.csv."""
    focs = {s: load(f'{s}_focus') for s, _, _ in FRAME_SETS}
    lines, md = [], []
    for f in [f for f in FLOWS_FULL if f.startswith('rec_')]:
        cells = []
        for s, key, _ in FRAME_SETS:
            x = focs[s]
            x = x[x.flow == f] if has(x, 'flow', 'z', 'true_z') else pd.DataFrame()
            e = (x.z - x.true_z).abs().dropna() * 1e6 if len(x) else pd.Series(dtype=float)
            med, p90 = (float(e.median()), float(e.quantile(0.9))) if len(e) else (None, None)
            cells.append(f'{num(med, 0)} / {num(p90, 0)}')
            macro(f'FrameErr{key}{camel(f)}Median', med, '{:.0f}')
            macro(f'FrameErr{key}{camel(f)}PNinety', p90, '{:.0f}')
        lines.append(tt(f) + ' & ' + ' & '.join(cells) + ' \\\\')
        md.append([f] + cells)
    write('tab_dist_frames_focus', lines, ['flow'] + [lab for _, _, lab in FRAME_SETS], md,
          notes=['|z used − true z| on the full frames, median / 90th percentile in um, over frames and repetitions. '
                 'Under a tilt the true distance is the one of the frame recorded in the metadata.'],
          comment=['rows: flows; cells: median um / p90 um; columns: ' + ', '.join(s for s, _, _ in FRAME_SETS)])


# ------------------------------------------------------------------------------------------------ figures
CAPTIONS = {
    'fig_dist_breakeven': (
        'Cost of the front end per full frame against the number of frames n that share one search of the distance '
        '(frames per mounting, log scale). Curves: the blind search of the paper (AF once/session) and the cheap '
        'search (cheap AF once/session) done once and reused by the n frames; the cost falls as 1/n. Horizontal '
        'lines: the three learned focal stacks (5, 7 and 9 distances), which cost the same whatever n, and two '
        'conventional references, the reconstruction at the nominal distance and the cheap search on every frame; '
        'each is named on the right, joined to its line by a thin connector. Where a curve crosses a stack line (open circles, with the value of n*), focusing once per mounting becomes '
        'cheaper than the stack: below n* the stack is cheaper, above it the conventional flow is. (a) One GPU '
        '(minimum time over the repetitions). (b) One CPU core (median). All times are sums of measured stage times.'),
    'fig_dist_cost_f1': (
        'Cost against accuracy on full frames of the sensor. Each point is a flow; up and to the left is better. Time '
        'per frame on one GPU (log scale), as sums of measured stage times; the flows that reuse a distance are '
        'charged a session of 100 frames. Accuracy: open-set F1 on the boxes found by the detector. (a) Distance '
        'fixed in each session (the frames of the paper), cost of the front end only. (b) The same frames, cost end '
        'to end, with the detector. (c) Distance changing at every frame by 5 %, front end only. (d) The same, end '
        'to end.'),
    'fig_dist_tilt': (
        'Open-set F1 end to end on full frames against the tilt of the slide (bottom axis, degrees). The top axis '
        'gives the change of distance this tilt makes at the edge of the frame, 3.2 mm x tan(tilt), in micrometres. '
        'Each line is a flow: reconstructions at the nominal distance, after a global autofocus, with per-object '
        'focus over a wide range, the cheap autofocus, and the three focal stacks (legend below the axis). Single '
        'panel; mean over the five repetitions.'),
    'fig_dist_sets': (
        'Open-set F1 of every flow (columns) in every set of test windows (rows): the bench, the distance changing '
        'between sessions (2 and 5 %), at every image (2 and 5 %) or drifting 0.5 % per image, strong shot noise and '
        'a narrow beam. Models, galleries and thresholds are those of the base set; mean over the repetitions. '
        'Darker is better.'),
    'fig_dist_sweep': (
        'The validation sweep of the 256 candidate searches of the distance: share of validation images with a gross '
        'error (above 1 % of the nominal distance; symmetric log scale) against the cost of the search in '
        'reconstructions of the whole window (log scale). Grey: every candidate. Highlighted and labelled: the blind '
        'search of the paper (reference) and the two searches frozen for the test split, the cheap one (afc) and the '
        'robust one (afr). (a) The bench (validation split of the base set). (b) Distance changing at every image by '
        '5 %. (c) Strong shot noise (full well of 500 electrons). (d) Narrow illumination beam.'),
}


def save(fig, name):
    d = out() / 'figures'
    d.mkdir(parents=True, exist_ok=True)
    fig.savefig(d / f'{name}.pdf', bbox_inches='tight', pad_inches=0.02, metadata={'CreationDate': None})  # same bytes on a rerun
    fig.savefig(d / f'{name}.png', bbox_inches='tight', pad_inches=0.02, dpi=200)
    plt.close(fig)
    print('wrote', d / f'{name}.pdf')


def empty(ax, text='not measured yet'):
    ax.text(0.5, 0.5, text, transform=ax.transAxes, ha='center', va='center', color=MUTED, fontsize=7)
    ax.set_xticks([])
    ax.set_yticks([])


def spread(ys, ax, gap=0.07):
    """Label positions (data units, log y axis) at least gap (axes fraction) apart, in the order of ys, each as close
    to its own value as the others allow (overlapping labels are pooled into a block centred on their values) and
    kept inside the axis."""
    lo, hi = np.log10(ax.get_ylim())
    step = gap * (hi - lo)
    order = np.argsort(ys)
    want = np.log10(np.asarray(ys, float))[order]
    blocks = []                                   # [first index (in order), base]: positions base + k * step
    for i, y in enumerate(want):
        blocks.append([i, y])
        while len(blocks) > 1:
            (i0, b0), (i1, b1) = blocks[-2], blocks[-1]
            n0 = i1 - i0
            if b0 + (n0 - 1) * step + step <= b1 + 1e-12:
                break
            members = range(i0, i + 1)
            blocks[-2:] = [[i0, float(np.mean([want[k] - (k - i0) * step for k in members]))]]
    pos = np.empty(len(want))
    for (i0, b), nxt in zip(blocks, blocks[1:] + [[len(want), None]]):
        pos[i0:nxt[0]] = b + step * np.arange(nxt[0] - i0)
    pos += max(0.0, lo + step / 2 - pos.min()) if len(pos) else 0.0   # inside the axis: first up, then down
    pos -= max(0.0, pos.max() - (hi - step / 2)) if len(pos) else 0.0
    res = np.empty(len(want))
    res[order] = pos
    return 10 ** res


def fig_dist_breakeven():
    T = load_timing()
    if not T['gpu'].get(FULL) and not T['cpu'].get(FULL):
        print('skipped fig_dist_breakeven: no timing of the full frame')
        return
    n = np.logspace(0, 2, 300)
    fig, axs = plt.subplots(1, 2, figsize=(7.16, 2.6), gridspec_kw=dict(wspace=0.62))
    for ax, dev, letter, scale, unit in [(axs[0], 'gpu', 'a', 1e3, 'ms'), (axs[1], 'cpu', 'b', 1, 's')]:
        panel(ax, letter)
        t = T[dev].get(FULL, {})
        drawn = False
        for f, stage in [('rec_afs', 'autofocus'), ('rec_afsc', 'autofocus_afc')]:
            if front_end(f, t, 1) is None:
                continue
            ax.plot(n, [front_end(f, t, k) * scale for k in n], color=COLORS[f], label=SHORT[f])
            for s in STACKS:
                ns = break_even(t, s, stage)
                if ok(ns) and 1 <= ns <= 100:
                    y = front_end(s, t) * scale
                    ax.plot(ns, y, 'o', mfc='white', mec=COLORS[f], ms=4, mew=1, zorder=5)
                    ax.annotate(f'{ns:.0f}' if ns >= 10 else f'{ns:.1f}', (ns, y), xytext=(2, 4),
                                textcoords='offset points', fontsize=5.5, color=INK)
            drawn = True
        labels = []
        for f in STACKS + ['rec_z0', 'rec_afc']:
            v = front_end(f, t)
            if v is None:
                continue
            ax.axhline(v * scale, color=COLORS[f], lw=1.0, ls='--' if f in STACKS else ':')
            labels.append((v * scale, SHORT[f], COLORS[f]))
            drawn = True
        if not drawn:
            empty(ax)
            continue
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlim(1, 100)
        ax.set_xticks([1, 2, 5, 10, 20, 50, 100])
        ax.set_xticklabels(['1', '2', '5', '10', '20', '50', '100'])
        ax.set_ylim(ax.get_ylim())                # freeze the limits before placing the labels
        tr = ax.get_yaxis_transform()             # x in axis fraction, y in data
        for (y0, lab, col), y in zip(labels, spread([y for y, _, _ in labels], ax)):
            ax.annotate(lab, (1.0, y0), xycoords=tr, xytext=(1.07, y), textcoords=tr, color=INK, fontsize=5.5,
                        va='center', annotation_clip=False,
                        arrowprops=dict(arrowstyle='-', color=col, lw=0.6, shrinkA=0, shrinkB=1))
        ax.set_xlabel('frames per mounting, n')
        ax.set_ylabel(f'front end per frame ({unit})')
        ax.set_title('one GPU' if dev == 'gpu' else 'one CPU core', fontsize=7)
        ax.legend(loc='upper right', fontsize=5.8, handlelength=1.4)
    save(fig, 'fig_dist_breakeven')


def fig_dist_cost_f1():
    T = load_timing()
    t = T['gpu'].get(FULL, {})
    sets = [('full_frames', 'distance fixed per session'), ('full_frames_frame5', 'distance changing per frame (5 %)')]
    accs = {s: load(s) for s, _ in sets}
    if not t or not any(has(a, 'flow', 'boxes', F1) for a in accs.values()):
        print('skipped fig_dist_cost_f1: no timing of the full frame or no full frames')
        return
    fig, axs = plt.subplots(2, 2, figsize=(7.16, 4.8), gridspec_kw=dict(wspace=0.28, hspace=0.5))
    shown = {}
    for i, (s, title) in enumerate(sets):
        for j, (fn, scale, xl) in enumerate([(front_end, 1e3, 'front end per frame, one GPU (ms)'),
                                             (end_to_end, 1, 'time per frame end to end, one GPU (s)')]):
            ax = axs[i, j]
            panel(ax, 'abcd'[2 * i + j])
            pts = 0
            for f in FLOWS_FULL:
                x, y = fn(f, t), mean(per_rep(accs[s], F1, flow=f, boxes='det'))
                if not ok(x) or not ok(y):
                    continue
                ax.plot(x * scale, y, MARKERS[f], color=COLORS[f], ms=5, mec='white', mew=0.4, label=SHORT[f])
                pts += 1
                shown.setdefault(f, ax.lines[-1])
            if not pts:
                empty(ax, 'not run yet')
                continue
            ax.set_xscale('log')
            ax.xaxis.set_major_locator(LogLocator(subs=(1, 2, 5)))
            ax.xaxis.set_major_formatter(FormatStrFormatter('%g'))
            ax.xaxis.set_minor_formatter(NullFormatter())
            ax.set_xlabel(xl)
            ax.set_ylabel('open-set F1, end to end')
            ax.set_title(f'{title}, {"front end" if j == 0 else "with the detector"}', fontsize=7)
            ax.text(0.97, 0.05, 'better: up and left', transform=ax.transAxes, ha='right', fontsize=5.5, color=MUTED)
    order = [f for f in FLOWS_FULL if f in shown]
    fig.legend([shown[f] for f in order], [SHORT[f] for f in order], loc='lower center', ncol=6, fontsize=6,
               bbox_to_anchor=(0.5, -0.06), handletextpad=0.3, columnspacing=1.0)
    save(fig, 'fig_dist_cost_f1')


def fig_dist_tilt():
    accs = {t: load(f'full_frames_tilt{t}') for t in TILTS}
    if not any(has(a, 'flow', 'boxes', F1) for a in accs.values()):
        print('skipped fig_dist_tilt: no tilted frames')
        return
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    for f in TILT_FLOWS:
        xs, ys = [], []
        for t in TILTS:
            y = mean(per_rep(accs[t], F1, flow=f, boxes='det'))
            if ok(y):
                xs.append(t)
                ys.append(y)
        if xs:
            ax.plot(xs, ys, '-', marker=MARKERS[f], color=COLORS[f], ms=3.5, lw=1.1, label=SHORT[f])
    ax.set_xlabel('tilt of the slide (degrees)')
    ax.set_ylabel('open-set F1, end to end')
    ax.set_xlim(-0.5, 15.5)
    top = ax.secondary_xaxis('top', functions=(lambda d: HALF_WIDTH_UM * np.tan(np.radians(d)),
                                               lambda u: np.degrees(np.arctan(np.asarray(u) / HALF_WIDTH_UM))))
    top.set_xticks([0, 100, 250, 500, 850])
    top.set_xlabel('change of distance at the edge of the frame ($\\mu$m)', fontsize=7, color=MUTED)
    ax.legend(fontsize=5.8, ncol=4, loc='upper center', bbox_to_anchor=(0.5, -0.2), handlelength=1.6,
              handletextpad=0.3, columnspacing=0.9)   # below the axis, off the curves
    save(fig, 'fig_dist_tilt')


def fig_dist_sets():
    d = load('robustness')
    if not has(d, 'variant', 'flow', F1):
        print('skipped fig_dist_sets: no robustness.csv')
        return
    piv = d.groupby(['variant', 'flow', 'rep'])[F1].mean().groupby(['variant', 'flow']).mean().unstack()
    rows, cols = [v for v in SETS if v in piv.index], [f for f in FLOWS if f in piv.columns]
    if not rows or not cols:
        print('skipped fig_dist_sets: none of the sets or flows of the study')
        return
    A = piv.reindex(index=rows, columns=cols).to_numpy(float)
    fig, ax = plt.subplots(figsize=(3.5, 0.5 + 0.28 * len(rows) + 0.6))
    ax.imshow(A, cmap='Blues', vmin=0, vmax=1, aspect='auto')
    for i in range(len(rows)):
        for j in range(len(cols)):
            v = A[i, j]
            if np.isfinite(v):
                ax.text(j, i, f'{v:.2f}'[1:] if v < 1 else '1.0', ha='center', va='center', fontsize=5,
                        color='white' if v > 0.6 else INK)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([SHORT[c] for c in cols], rotation=60, ha='right', fontsize=6)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([SET_SHORT.get(r, r) for r in rows], fontsize=5.5)
    ax.grid(False)
    save(fig, 'fig_dist_sets')


def fig_dist_sweep():
    s = load('focus_sweep')
    if not has(s, 'set', 'candidate', 'cost', 'gross'):
        print('skipped fig_dist_sweep: no focus_sweep.csv')
        return
    hl = {'blind-b1-tog': ('reference', COLORS['rec_af']), 'r10b-b4-tog': ('afc', COLORS['rec_afc']),
          'r15b-b2-s2': ('afr', COLORS['rec_afr'])}
    fig, axs = plt.subplots(2, 2, figsize=(7.16, 4.4), gridspec_kw=dict(wspace=0.25, hspace=0.45))
    for ax, (root, short), letter in zip(axs.flat, VAL_SETS, 'abcd'):
        panel(ax, letter)
        x = s[s['set'] == root]
        if not len(x):
            empty(ax, 'not swept')
            continue
        ax.plot(x.cost, 100 * x.gross, 'o', color=MUTED, ms=2.2, alpha=0.45, mew=0)
        for c, (lab, col) in hl.items():
            y = x[x.candidate == c]
            if len(y):
                cx, cy = float(y.cost.iloc[0]), 100 * float(y.gross.iloc[0])
                ax.plot(cx, cy, 'o', color=col, ms=5, mec='white', mew=0.6, zorder=5)
                left = c == 'blind-b1-tog'   # the most expensive: its label goes to the left
                ax.annotate(f'{lab}\n{c}', (cx, cy), xytext=(-5 if left else 5, 4), textcoords='offset points',
                            fontsize=5.3, color=INK, ha='right' if left else 'left', va='bottom')
        ax.set_xscale('log')
        ax.set_yscale('symlog', linthresh=1)
        ax.set_ylim(-0.1, 150)
        ax.set_yticks([0, 1, 10, 100])
        ax.set_yticklabels(['0', '1', '10', '100'])
        ax.xaxis.set_major_formatter(FormatStrFormatter('%g'))
        ax.set_xlabel('cost (reconstructions of the whole window)')
        ax.set_ylabel('gross failures (%)')
        ax.set_title({'realistic': 'bench (validation)', 'frame_5': 'distance per frame 5 %',
                      'fullwell_500': 'shot noise, full well 500 e$^-$', 'beam_narrow': 'narrow beam'}[short],
                     fontsize=7)
    save(fig, 'fig_dist_sweep')


def write_captions():
    d = out() / 'figures'
    d.mkdir(parents=True, exist_ok=True)
    (d / 'captions.md').write_text('\n\n'.join(f'**{k}.** {v}' for k, v in CAPTIONS.items()) + '\n')


# ------------------------------------------------------------------------------------------------ main
TABLES = [tab_dist_metrics, tab_dist_paired, tab_dist_focus, tab_dist_focus_val, tab_dist_sessions, tab_dist_time,
          tab_dist_time_measured, tab_dist_breakeven, tab_dist_criterion, tab_dist_frames, tab_dist_frames_paired,
          tab_dist_frames_focus, tab_dist_own]
FIGURES = [fig_dist_breakeven, fig_dist_cost_f1, fig_dist_tilt, fig_dist_sets, fig_dist_sweep]


def main(timing=None):
    if timing:
        os.environ['HOLO_DIST_TIMING'] = str(timing)
    M.clear()
    setup()
    out().mkdir(parents=True, exist_ok=True)
    for fn in TABLES + FIGURES + [write_captions]:
        try:
            fn()
        except Exception as e:  # noqa: BLE001  one missing result must not stop the others
            print('FAILED', fn.__name__, repr(e))
    g, c = timing_dirs()
    f = out() / 'numbers_distancia.tex'
    f.write_text('% generated by python -m holo_openset paper distance -- do not edit\n'
                 f'% results: {paths.RESULTS}; timing: GPU {g}, CPU {c}\n' +
                 '\n'.join(f'\\newcommand{{\\{k}}}{{{v}}}' for k, v in sorted(M.items())) + '\n')
    print('wrote', f, len(M), 'macros')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
