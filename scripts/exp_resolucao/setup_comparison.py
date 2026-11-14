"""Z8.1: the three existing sets side by side (base letters at 19.25 mm, small letters at 19.25 mm and at 2 mm): open-set
F1 and rejection of unknowns of hologram crops, the propagation layer and the reconstruction at z0 (mean of the five
repetitions, the paired gap to the crops and how many repetitions share its sign), next to the share of a pattern that
falls OUTSIDE its crop for the letter sizes of the set at its own distance (pattern_in_crop_z_summary.csv, source of the
bench, mean of four letters). A last row gives the share outside for base letters at 1 mm (no recognition result
exists there). Reads small_preview*.csv and pattern_in_crop_z_summary.csv; writes $HOLO_RESULTS/setup_comparison.csv.

    python scripts/exp_resolucao/setup_comparison.py
"""
import pandas as pd

from holo_openset import paths

SETS = [('realistic', 'base letters (46-140 px)', 19.25, 'base'), ('small_z0', 'small letters (11-59 px)', 19.25, 'small'),
        ('small_near', 'small letters (11-59 px)', 2.0, 'small')]
FLOWS = ['raw', 'prop', 'rec_z0']


def outside(pc, kind, z):
    d = pc[(pc.source == 'bench') & pc['size'].str.startswith(kind) & (pc.z_mm == z)].set_index('size')
    return {f'outside_crop_{k.split()[1]}': 1 - d.loc[k, 'share_mean'] for k in d.index}


def main():
    R = paths.RESULTS
    t, g = pd.read_csv(R / 'small_preview.csv'), pd.read_csv(R / 'small_preview_gaps.csv')
    pc = pd.read_csv(R / 'pattern_in_crop_z_summary.csv')
    rows = []
    for s, letters, z, kind in SETS:
        row = dict(set=s, letters=letters, z_mm=z)
        for f in FLOWS:
            for m, short in [('novel_open_macro_f1', 'f1'), ('novel_unknown_rejection', 'rejection')]:
                row[f'{short}_{f}'] = t[(t.set == s) & (t.flow == f) & (t.metric == m)]['mean'].iloc[0]
                if f != 'raw':
                    x = g[(g.comparison == f'{s}: {f} - raw') & (g.metric == m)].iloc[0]
                    row[f'{short}_gap_{f}_minus_raw'] = x.diff_mean
                    row[f'{short}_gap_{f}_minus_raw_same_sign'] = int(x.same_sign)
        row.update(outside(pc, kind, z))
        rows.append(row)
    rows.append(dict(set='(pattern only)', letters='base letters (46-140 px)', z_mm=1.0, **outside(pc, 'base', 1.0)))
    out = pd.DataFrame(rows)
    out.to_csv(R / 'setup_comparison.csv', index=False, float_format='%.4f')
    pd.set_option('display.width', 250)
    print(out.T.to_string(header=False))


if __name__ == '__main__':
    main()
