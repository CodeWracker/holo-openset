"""Tables (bodies of tabular environments) and the numbers quoted in the text (LaTeX macros), from
results/holo_openset and the datasets. A missing result gives '--' (table) or '?' (macro), never an error.

    python -m holo_openset paper tables   -> figures/paper/tables/*.tex, figures/paper/numbers.tex
"""
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

from holo_openset import paths
from holo_openset.flows import FLOWS
from holo_openset.sim.variants import BASE as VBASE, VARIANTS

R = paths.RESULTS
ORDER = ['raw', 'learned', 'complex', 'wiener', 'rec_z0', 'rec_af', 'rec_edf', 'rec_twin']
NAME = {'raw': 'hologram crops', 'learned': 'learned layer', 'complex': 'complex layer', 'wiener': 'Wiener filter',
        'rec_z0': 'reconstruction at $z_0$', 'rec_af': 'autofocus', 'rec_edf': 'per-object focus',
        'rec_twin': 'autofocus + twin removal', 'oracle_pixel': 'pixel oracle'}
NEEDS = {'raw': '--', 'learned': '--', 'complex': '--', 'wiener': '$\\lambda,\\Delta,z_0$',
         'rec_z0': '$\\lambda,\\Delta,z_0,B$', 'rec_af': '$\\lambda,\\Delta,B$', 'rec_edf': '$\\lambda,\\Delta,B$',
         'rec_twin': '$\\lambda,\\Delta,B$', 'oracle_pixel': '$\\lambda,\\Delta,z_0,B$'}
M = {}   # macros


DIGITS = dict(zip('0123456789', ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']))


def macro(name, value, fmt='{:.3f}'):
    name = ''.join(DIGITS.get(c, c) for c in name if c.isalnum())   # LaTeX command names are letters only
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        M[name] = '?'
    elif isinstance(value, str):
        M[name] = value
    else:
        M[name] = fmt.format(value)


def tex(text):
    """Plain text of a label -> LaTeX."""
    return (str(text).replace('%', '\\%').replace(' um', ' $\\mu$m').replace('(um)', '($\\mu$m)')
            .replace('mm2', 'mm$^2$').replace('e-', 'e$^-$'))


def write_table(name, lines):
    d = paths.PAPER / 'tables'
    d.mkdir(parents=True, exist_ok=True)
    (d / f'{name}.tex').write_text('\n'.join(lines) + '\n')
    print('wrote', d / f'{name}.tex')


def ms(x, k=3, std=True):
    """mean ± std of a series (LaTeX), '--' if empty."""
    x = pd.Series(x).dropna()
    if not len(x):
        return '--'
    return f'{x.mean():.{k}f}' + (f'$\\pm${x.std():.{k}f}' if std and len(x) > 1 else '')


def evals(set_='realistic', tag='', train_set=None):
    """One row per (flow, rep) of the evaluations in results/holo_openset/eval/<set>."""
    rows = []
    for f in glob.glob(str(R / 'eval' / set_ / '*.json')):
        d = json.load(open(f))
        if d.get('tag', '') != tag or d.get('train_set', set_) != (train_set or set_):
            continue
        rows.append(d)
    return pd.DataFrame(rows)


def load_csv(name):
    f = R / f'{name}.csv'
    return pd.read_csv(f) if f.exists() else pd.DataFrame()


def load_json(name):
    f = R / f'{name}.json'
    return json.load(open(f)) if f.exists() else {}


# ------------------------------------------------------------------------------------------------ data
def data_numbers():
    """The numbers of the datasets come from the data; results/data_summary.json keeps them for who has none."""
    f = paths.RESULTS / 'data_summary.json'
    if (paths.dataset(paths.BASE) / 'physics.json').exists():
        before = set(M)
        set_numbers()
        json.dump({k: M[k] for k in sorted(set(M) - before)}, open(f, 'w'), indent=1)
    else:
        M.update(load_json('data_summary'))
    run_numbers()


def set_numbers():
    root = paths.dataset(paths.BASE)
    cfg = json.load(open(root / 'physics.json'))
    p = cfg['physics']
    meta, ann = pd.read_csv(root / 'metadata.csv'), pd.read_csv(root / 'annotations.csv')
    ses = pd.read_csv(root / 'sessions.csv')
    macro('SimImages', f'{len(meta):,}'.replace(',', '{,}'))
    macro('SimPatterns', f'{len(ann):,}'.replace(',', '{,}'))
    macro('SimSessions', len(ses), '{}')
    macro('SimPerSession', cfg['per_session'], '{}')
    for s, n in [('train', 'Train'), ('val', 'Val'), ('test', 'Test')]:
        macro(f'Sim{n}Sessions', int((ses.split == s).sum()), '{}')
        macro(f'Sim{n}Patterns', f'{int((ann.split == s).sum()):,}'.replace(',', '{,}'))
    macro('SimTestImages', int((meta.split == 'test').sum()), '{}')
    macro('SimMargin', p['margin'], '{}')
    macro('SimReachMm', p['reach'] * 1.67e-3, '{:.1f}')
    macro('SimOutside', meta.n_outside.mean(), '{:.0f}')
    macro('SimAbsMean', p['absorption_mean'], '{:g}')
    macro('SimAbsStd', p['absorption_std'], '{:g}')
    macro('SimPhaseMean', p['phase_mean'], '{:g}')
    macro('SimPhaseStd', p['phase_std'], '{:g}')
    macro('SimPhaseMax', p['phase_max'], '{:g}')
    macro('SimDepthStd', p['depth_std'] * 1e6, '{:.0f}')
    macro('SimDepthMax', p['depth_max'] * 1e6, '{:.0f}')
    macro('SimSessionZ', p['session_z_std'] * 100, '{:g}')
    macro('SimDust', p['dust_density'], '{:g}')
    macro('SimSensorDust', p['sensor_dust_density'], '{:g}')
    macro('SimBandwidth', p['bandwidth'] * 1e9, '{:g}')
    macro('SimNLambda', p['n_wavelengths'], '{}')
    macro('SimPinhole', p['pinhole'] * 1e6, '{:g}')
    macro('SimSourceCm', p['source_distance'] * 100, '{:g}')
    macro('SimBlurUm', p['pinhole'] * p['z0'] / p['source_distance'] * 1e6, '{:.1f}')
    macro('SimWaistLo', p['beam_waist'][0], '{:g}')
    macro('SimWaistHi', p['beam_waist'][1], '{:g}')
    macro('SimBeamOff', p['beam_offset_std'], '{:g}')
    macro('SimFullWell', f"{p['full_well']:,.0f}".replace(',', '{,}'))
    macro('SimExposure', p['exposure'] * 100, '{:.0f}')
    macro('SimRead', p['read_noise'], '{:g}')
    macro('SimPRNU', p['prnu'] * 100, '{:g}')
    macro('SimBits', p['bits'], '{}')
    macro('SimBlanks', cfg['n_blanks'], '{}')
    ff = paths.dataset('full_frames')
    if (ff / 'annotations.csv').exists():
        a = pd.read_csv(ff / 'annotations.csv')
        macro('FullFrames', a.image_id.nunique(), '{}')
        macro('FullLetters', f'{len(a):,}'.replace(',', '{,}'))
        macro('FullPerFrame', len(a) / a.image_id.nunique(), '{:.0f}')


def run_numbers():
    fn = load_json('figure_numbers')
    macro('CropEnergyCoherent', 100 * fn['crop_energy_coherent'] if 'crop_energy_coherent' in fn else None, '{:.0f}')
    macro('CropEnergyBench', 100 * fn['crop_energy_bench'] if 'crop_energy_bench' in fn else None, '{:.0f}')
    macro('ComplexRealShare', 100 * fn['complex_real_share'] if 'complex_real_share' in fn else None, '{:.0f}')
    g = load_json('gaps')
    macro('GapPeriodic', 100 * g['periodic_rel_diff_mean'] if g else None, '{:.0f}')
    macro('GapQuadratic', 100 * g['quadratic_rel_energy_mean'] if g else None, '{:.0f}')
    import re
    secs = []
    for f in glob.glob(str(paths.LOGS / 'train_*_r[1-5].log')):
        m = re.findall(r'step 2999/3000 loss [0-9.]+ \((\d+)s\)', open(f).read())
        if m:
            secs.append(int(m[-1]))
    run = load_json('run_summary')   # the training logs and the models are not in git
    n_yolo = len(glob.glob(str(paths.MODELS / '*' / 'yolo_r*.pt')))
    n_models = len(glob.glob(str(paths.MODELS / '*' / '*_r[1-5].pt'))) - n_yolo
    macro('TrainMinutes', np.median(secs) / 60 if secs else run.get('train_minutes'), '{:.0f}')
    macro('NModels', n_models or run.get('n_models'), '{}')
    macro('NYolo', n_yolo or run.get('n_yolo'), '{}')


# ------------------------------------------------------------------------------------------------ main results
def tab_main():
    e = evals()
    o = load_csv('oracle')
    lines = []
    for f in ORDER + ['oracle_pixel']:
        if f == 'oracle_pixel':
            d = o[(o.variant == 'base') & (o.boxes == 'gt')] if len(o) else pd.DataFrame()
        else:
            d = e[e.flow == f] if len(e) else pd.DataFrame()
        cells = [ms(d[k]) if k in d else '--' for k in ['novel_auroc', 'novel_oscr', 'novel_known_acc',
                                                         'novel_unknown_rejection', 'novel_open_macro_f1']]
        if f == 'wiener' or f == 'oracle_pixel':
            lines.append('\\midrule')
        lines.append(f'{NAME[f]} & {NEEDS[f]} & ' + ' & '.join(cells) + ' \\\\')
        if len(d) and 'novel_open_macro_f1' in d:
            key = {'oracle_pixel': 'Oracle'}.get(f, ''.join(w.capitalize() for w in f.split('_')))
            macro(f'{key}AUROC', d.novel_auroc.mean())
            macro(f'{key}Rej', d.novel_unknown_rejection.mean())
            macro(f'{key}Known', d.novel_known_acc.mean())
            macro(f'{key}Fone', d.novel_open_macro_f1.mean())
    write_table('tab_main', lines)


def tab_ablation():
    lines = []
    for label, tag, flow in [('learned layer, $\\mathrm{lr}_F=3\\cdot10^{-1}$ (proposed)', '', 'learned'),
                             ('learned layer, $\\mathrm{lr}_F=3\\cdot10^{-3}$', '_lr3e-3', 'learned'),
                             ('learned layer, no auxiliary scenes', '_noaux', 'learned'),
                             ('layer frozen at the identity (hologram crops)', '', 'raw'),
                             ('complex layer', '', 'complex')]:
        e = evals(tag=tag)
        d = e[e.flow == flow] if len(e) else pd.DataFrame()
        cells = [ms(d[k]) if k in d else '--' for k in ['novel_auroc', 'novel_unknown_rejection', 'novel_known_acc',
                                                         'novel_open_macro_f1', 'world20_new_class_acc']]
        lines.append(f'{label} & ' + ' & '.join(cells) + ' \\\\')
        if tag and len(d):
            macro('Abl' + {'_lr3e-3': 'Lr', '_noaux': 'Noaux'}[tag] + 'Fone', d.novel_open_macro_f1.mean())
            macro('Abl' + {'_lr3e-3': 'Lr', '_noaux': 'Noaux'}[tag] + 'AUROC', d.novel_auroc.mean())
    write_table('tab_ablation', lines)


def tab_enroll():
    e = evals()
    lines = []
    for f in ORDER:
        d = e[e.flow == f] if len(e) else pd.DataFrame()
        cells = [ms(d[k], std=False) if k in d else '--' for k in
                 ['world5_new_class_acc', 'world20_new_class_acc', 'worldall_new_class_acc',
                  'world20_new_class_rank1', 'world20_absent_rejection', 'world20_seen_acc']]
        lines.append(f'{NAME[f]} & ' + ' & '.join(cells) + ' \\\\')
        if len(d) and f in ('learned', 'rec_z0', 'complex'):
            k = ''.join(w.capitalize() for w in f.split('_'))
            for s in ['5', '20', 'all']:
                macro(f'{k}Enroll{s.capitalize() if s == "all" else {"5": "Five", "20": "Twenty"}[s]}',
                      d[f'world{s}_new_class_acc'].mean())
    write_table('tab_enroll', lines)


def tab_e2e():
    d = load_csv('e2e')
    o = load_csv('oracle')
    lines = []
    for f in ORDER + ['oracle_pixel']:
        x = (o[(o.variant == 'base') & (o.boxes == 'det')] if len(o) else pd.DataFrame()) if f == 'oracle_pixel' \
            else (d[d.flow == f] if len(d) else pd.DataFrame())
        if f == 'oracle_pixel':
            lines.append('\\midrule')
        cells = [ms(x[k], std=False) if k in x else '--' for k in ['detector_recall', 'fp_per_img', 'fp_rejected',
                                                                    'novel_auroc', 'novel_unknown_rejection',
                                                                    'novel_open_macro_f1']]
        lines.append(f'{NAME[f]} & ' + ' & '.join(cells) + ' \\\\')
        if len(x):
            k = {'oracle_pixel': 'Oracle'}.get(f, ''.join(w.capitalize() for w in f.split('_')))
            macro(f'EtoE{k}Fone', x.novel_open_macro_f1.mean())
            macro(f'EtoE{k}Recall', x.detector_recall.mean())
    if len(d):
        macro('EtoERecall', d.detector_recall.mean())
        macro('EtoEFp', d.fp_per_img.mean(), '{:.2f}')
    write_table('tab_e2e', lines)


def tab_discovery():
    d = load_csv('discovery')
    lines = []
    for f in ['learned', 'rec_z0']:
        x = d[d.flow == f] if len(d) else pd.DataFrame()
        for r, row in x.sort_values('rep').iterrows():
            lines.append(f"{NAME[f]} & r{row.rep} & {row.frr * 100:g}\\,\\% & {row.cut:g} & {row.pool:.0f} & "
                         f"{row.unseen_in_pool:.2f} & {row.seen_leak:.2f} & {row.n_clusters:.0f} & {row.bcubed_p:.2f} & "
                         f"{row.bcubed_r:.2f} & {row.bcubed_f1:.2f} \\\\")
        if len(x):
            lines.append(f"\\multicolumn{{2}}{{l}}{{{NAME[f]}, mean}} & & & {x.pool.mean():.0f} & "
                         f"{x.unseen_in_pool.mean():.2f} & {x.seen_leak.mean():.2f} & {x.n_clusters.mean():.1f} & "
                         f"{x.bcubed_p.mean():.2f} & {x.bcubed_r.mean():.2f} & {x.bcubed_f1.mean():.2f} \\\\")
            lines.append('\\midrule')
            k = ''.join(w.capitalize() for w in f.split('_'))
            macro(f'Disc{k}Fone', x.bcubed_f1.mean(), '{:.2f}')
            macro(f'Disc{k}Reach', x.unseen_in_pool.mean(), '{:.2f}')
            macro(f'Disc{k}Cut', x.cut.iloc[0], '{:g}')
            macro(f'Disc{k}Frr', x.frr.iloc[0] * 100, '{:g}')
            macro(f'Disc{k}Leak', x.seen_leak.mean(), '{:.2f}')
            macro(f'Disc{k}Clusters', x.n_clusters.mean(), '{:.0f}')
    write_table('tab_discovery', lines[:-1] if lines and lines[-1] == '\\midrule' else lines)


# ------------------------------------------------------------------------------------------------ cost
STAGE_GROUPS = {'read': ['load', 'normalise'],   # reading the frame (and, for a reconstruction, its blank frame)
                'compute': ['reconstruct', 'autofocus', 'per_object', 'twin', 'channels', 'layer'],
                'embed + decide': ['embed', 'decide']}


def tab_full_frames():
    acc, t = load_csv('full_frames'), load_csv('full_frames_time')
    lines = []
    if not len(acc) or not len(t):
        write_table('tab_full', ['\\multicolumn{9}{c}{(not run yet)} \\\\'])
        return
    det = t[t.stage == 'detect'].seconds.median()
    macro('FullDetectS', det, '{:.2f}')
    per = t[t.flow != 'all'].groupby(['flow', 'frame', 'rep', 'stage']).seconds.sum().unstack('stage').fillna(0)
    for f in ORDER:
        if f not in per.index.get_level_values(0):
            continue
        p = per.loc[f]
        g = {k: p[[c for c in v if c in p]].sum(1).median() for k, v in STAGE_GROUPS.items()}
        a = acc[acc.flow == f]
        gt, dt = a[a.boxes == 'gt'], a[a.boxes == 'det']
        total = det + sum(g.values())
        lines.append(f"{NAME[f]} & {g['read'] * 1e3:.0f} & {g['compute'] * 1e3:.1f} & {g['embed + decide'] * 1e3:.0f} & "
                     f"{total:.2f} & {ms(gt.novel_auroc, std=False)} & {ms(gt.novel_open_macro_f1, std=False)} & "
                     f"{ms(dt.novel_open_macro_f1, std=False)} & {ms(dt.fp_rejected, std=False)} \\\\")
        k = ''.join(w.capitalize() for w in f.split('_'))
        macro(f'Full{k}ComputeMs', g['compute'] * 1e3, '{:.1f}')
        macro(f'Full{k}ReadMs', g['read'] * 1e3, '{:.0f}')
        macro(f'Full{k}TotalS', total, '{:.2f}')
        macro(f'Full{k}Fone', dt.novel_open_macro_f1.mean() if len(dt) else None)
        macro(f'Full{k}FoneGt', gt.novel_open_macro_f1.mean() if len(gt) else None)
        macro(f'Full{k}Rej', dt.novel_unknown_rejection.mean() if len(dt) else None)
    if len(acc[acc.boxes == 'det']):
        macro('FullRecall', acc[acc.boxes == 'det'].detector_recall.mean())
        macro('FullFpFrame', acc[acc.boxes == 'det'].fp_per_frame.mean(), '{:.1f}')
        macro('FullReps', acc.rep.nunique(), '{}')
    write_table('tab_full', lines)


STAGES = [('flat_field', 'flat field $\\sqrt{I/B}$'), ('layer_real', 'learned layer (real)'),
          ('layer_complex', 'learned layer (complex)'), ('backprop', 'one back-propagation'),
          ('autofocus', 'autofocus (114 reconstructions)'), ('per_object', 'per-object focus (25 more)'),
          ('twin', 'twin removal (50 passes)'), ('channels', 'channels of the network input'),
          ('yolo_tiled', 'YOLO localiser, tiles'), ('embed', 'ResNet18 embedding, all boxes'),
          ('decide', 'gallery search (5k)')]


def tab_stages():
    c, g = load_csv('timing_cpu'), load_csv('timing_gpu')
    lines = []
    big, small = (2748, 3840), (640, 640)

    def get(df, stage, size, key='median_s'):
        if not len(df):
            return None
        x = df[(df.stage == stage) & (df.height == size[0]) & (df.width == size[1])]
        return float(x[key].iloc[0]) if len(x) else None

    def fmt(v, unit):
        if v is None:
            return '--'
        return f'{v * 1e3:.1f}' if unit == 'ms' and v < 10 else f'{v * 1e3:.0f}' if unit == 'ms' else f'{v:.2f}'
    for st, label in STAGES:
        cs, cb, gs, gb = get(c, st, small), get(c, st, big), get(g, st, small, 'min_s'), get(g, st, big, 'min_s')
        ratio = f'{cb / cs:.0f}' if cs and cb else '--'
        lines.append(f'{label} & {fmt(cs, "ms")} & {fmt(cb, "s")} & {ratio} & {fmt(gs, "ms")} & {fmt(gb, "ms")} \\\\')
        k = ''.join(w.capitalize() for w in st.split('_'))
        macro(f'T{k}CpuSmallMs', cs * 1e3 if cs else None, '{:.1f}')
        macro(f'T{k}CpuBigS', cb, '{:.2f}')
        macro(f'T{k}GpuSmallMs', gs * 1e3 if gs else None, '{:.2f}')
        macro(f'T{k}GpuBigMs', gb * 1e3 if gb else None, '{:.1f}')
        macro(f'T{k}CpuRatio', cb / cs if cs and cb else None, '{:.0f}')
    # what a back-propagation costs against the layer, both one transform pair
    for tag, df, size, key in [('GpuSmall', g, small, 'min_s'), ('GpuBig', g, big, 'min_s'), ('CpuSmall', c, small,
                                                                                            'median_s'),
                               ('CpuBig', c, big, 'median_s')]:
        b_, l_ = get(df, 'backprop', size, key), get(df, 'layer_real', size, key)
        macro(f'BackOverLayer{tag}', b_ / l_ if b_ and l_ else None, '{:.1f}')
    write_table('tab_stages', lines)


# ------------------------------------------------------------------------------------------------ robustness
def tab_robustness():
    d, o = load_csv('robustness'), load_csv('oracle')
    lines = []
    if not len(d):
        write_table('tab_robustness', ['\\multicolumn{10}{c}{(not run yet)} \\\\'])
        return
    piv = d.groupby(['variant', 'flow']).novel_open_macro_f1.mean().unstack()
    opiv = o[o.boxes == 'det'].groupby('variant').novel_open_macro_f1.mean() if len(o) else pd.Series(dtype=float)
    base = piv.loc['base'] if 'base' in piv.index else None
    effect = None
    for v in ['base'] + list(VARIANTS):
        if v not in piv.index:
            continue
        eff, val, _ = VARIANTS.get(v, ('base', 'bench', {}))
        if eff != effect and v != 'base':
            lines.append('\\midrule')
            effect = eff
        cells = []
        for f in ORDER:
            x = piv.loc[v].get(f, np.nan)
            if not np.isfinite(x):
                cells.append('--')
            elif v != 'base' and base is not None and x < base[f] - 0.05:
                cells.append(f'\\textbf{{{x:.2f}}}')
            else:
                cells.append(f'{x:.2f}')
        cells.append(f'{opiv[v]:.2f}' if v in opiv else '--')
        label = 'base (bench)' if v == 'base' else tex(f'{eff}: {val}')
        lines.append(f'{label} & ' + ' & '.join(cells) + ' \\\\')
        for f in ORDER:
            if np.isfinite(piv.loc[v].get(f, np.nan)):
                macro(f'Rob{"".join(w.capitalize() for w in v.split("_"))}{"".join(w.capitalize() for w in f.split("_"))}',
                      piv.loc[v][f], '{:.2f}')
    write_table('tab_robustness', lines)


def tab_ideal():
    lines = []
    real, ideal, cross = evals('realistic'), evals('ideal'), evals('realistic', train_set='ideal')
    o = load_csv('oracle')
    for f in ['raw', 'learned', 'complex', 'wiener', 'rec_z0']:
        cells = []
        for e in [ideal, real, cross]:
            d = e[e.flow == f] if len(e) else pd.DataFrame()
            cells += [ms(d.novel_auroc, std=False) if len(d) else '--',
                      ms(d.novel_open_macro_f1, std=False) if len(d) else '--']
        lines.append(f'{NAME[f]} & ' + ' & '.join(cells) + ' \\\\')
        for name, e in [('Ideal', ideal), ('Cross', cross)]:
            d = e[e.flow == f] if len(e) else pd.DataFrame()
            if len(d):
                macro(f'{name}{"".join(w.capitalize() for w in f.split("_"))}Fone', d.novel_open_macro_f1.mean())
    if len(o) and 'periodic' in set(o.variant):
        x = o[(o.variant == 'periodic') & (o.boxes == 'det')]
        macro('OraclePeriodicFone', x.novel_open_macro_f1.mean())
    write_table('tab_ideal', lines)


def tab_scale():
    lines = []
    sets = [('realistic', '45--125\\,px, 19.25\\,mm'), ('small_z0', '12--36\\,px, 19.25\\,mm'),
            ('small_near', '12--36\\,px, 2\\,mm')]
    data = {s: evals(s) for s, _ in sets}
    for f in ['raw', 'learned', 'complex', 'wiener', 'rec_z0', 'rec_af', 'rec_twin']:
        cells = []
        for s, _ in sets:
            d = data[s][data[s].flow == f] if len(data[s]) else pd.DataFrame()
            cells.append(ms(d.novel_open_macro_f1, std=False) if len(d) else '--')
            if len(d) and s != 'realistic':
                macro(f'Scale{"".join(w.capitalize() for w in s.split("_"))}{"".join(w.capitalize() for w in f.split("_"))}',
                      d.novel_open_macro_f1.mean(), '{:.2f}')
        lines.append(f'{NAME[f]} & ' + ' & '.join(cells) + ' \\\\')
    write_table('tab_scale', lines)


def fidelity_numbers():
    d = load_json('fidelity')
    if not d:
        return
    p = d['psnr_db']
    for k, name in [('hologram', 'Holo'), ('z0', 'Zzero'), ('af', 'Af'), ('edf', 'Edf'), ('twin50', 'Twin'),
                    ('twin10', 'TwinTen'), ('twin100', 'TwinHundred')]:
        macro(f'Psnr{name}', p.get(k), '{:.1f}')
    macro('AfErrUm', d['autofocus_abs_error_um_median'], '{:.0f}')
    macro('AfErrPct', 100 * d['autofocus_rel_error_median'], '{:.2f}')


def main():
    paths.PAPER.mkdir(parents=True, exist_ok=True)
    for fn in [data_numbers, tab_main, tab_ablation, tab_enroll, tab_e2e, tab_discovery, tab_full_frames, tab_stages,
               tab_robustness, tab_ideal, tab_scale, fidelity_numbers]:
        try:
            fn()
        except Exception as e:  # noqa: BLE001  one missing result must not stop the others
            print('FAILED', fn.__name__, repr(e))
    out = paths.PAPER / 'numbers.tex'
    out.write_text('% generated by python -m holo_openset paper tables -- do not edit\n' +
                   '\n'.join(f'\\newcommand{{\\{k}}}{{{v}}}' for k, v in sorted(M.items())) + '\n')
    print('wrote', out, len(M), 'macros')
