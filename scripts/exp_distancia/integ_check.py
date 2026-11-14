"""Integration runs (docs/exp_distancia/CADERNO_INTEGRACAO.md): what a merge into a csv of results/ did to it.

    python scripts/exp_distancia/integ_check.py OLD.csv NEW.csv --keys rep variant flow [--intended "flow == 'rec_afc'"]

Every field is compared as the text written in the file. Reports: keys of OLD missing from NEW; rows of OLD outside
--intended (a pandas query on NEW's columns, read as text) that are not textually identical in NEW, with the largest
absolute difference of their numeric fields; rows inside --intended that already existed (recomputed: largest
difference per column); and the number of new keys.
"""
import argparse

import numpy as np
import pandas as pd


def read(p):
    return pd.read_csv(p, dtype=str, keep_default_na=False)


def numdiff(a, b):
    """Largest |a - b| over the fields of two aligned text frames that parse as numbers (inf when a field changed
    from/to a non-number)."""
    def num(s):   # Python's float(): correctly rounded (pd.to_numeric is not, and hides 1-ulp differences)
        try:
            return float(s)
        except ValueError:
            return np.nan
    out = {}
    for c in a.columns:
        x, y = np.array([num(s) for s in a[c]]), np.array([num(s) for s in b[c]])
        same_text = (a[c].values == b[c].values)
        both_num = ~np.isnan(x) & ~np.isnan(y)
        d = np.where(same_text, 0.0, np.where(both_num, np.abs(x - y), np.inf))
        out[c] = float(d.max()) if len(d) else 0.0
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('old')
    ap.add_argument('new')
    ap.add_argument('--keys', nargs='+', required=True)
    ap.add_argument('--intended', help='pandas query selecting the rows this run was meant to write')
    a = ap.parse_args()
    old, new = read(a.old), read(a.new)
    print(f'old {len(old)} rows, new {len(new)} rows (+{len(new) - len(old)}); columns equal: '
          f'{list(old.columns) == list(new.columns)}')
    for d, n in [(old, 'old'), (new, 'new')]:
        dup = d.duplicated(a.keys).sum()
        if dup:
            print(f'WARNING {dup} duplicated keys in {n}')
    old_i, new_i = old.set_index(a.keys), new.set_index(a.keys)
    missing = old_i.index.difference(new_i.index)
    print('old keys missing from new:', len(missing), list(missing[:5]))
    cols = [c for c in old.columns if c not in a.keys and c in new.columns]
    mine = new.query(a.intended) if a.intended else new.iloc[:0]
    mine_keys = pd.MultiIndex.from_frame(mine[a.keys]) if len(a.keys) > 1 else pd.Index(mine[a.keys[0]])
    common = old_i.index.intersection(new_i.index)
    others = common.difference(mine_keys)
    o, n = old_i.loc[others, cols], new_i.loc[others, cols]
    same = (o.values == n.values).all(1)
    print(f'pre-existing rows not intended: {len(others)}, textually identical {same.sum()}, differing {(~same).sum()}')
    if (~same).any():
        d = numdiff(o[~same], n[~same])
        print('  largest |difference| of the differing ones:', max(d.values()), {k: v for k, v in d.items() if v})
        print('  differing keys (first 10):', list(o.index[~same][:10]))
    rec = common.intersection(mine_keys)
    print(f'intended rows: {len(mine)}, of which recomputed (existed before): {len(rec)}, new: {len(mine) - len(rec)}')
    if len(rec):
        d = numdiff(old_i.loc[rec, cols], new_i.loc[rec, cols])
        print('  recomputed: largest |old - new| per column:', {k: v for k, v in d.items()})
    print('new keys in total:', len(new_i.index.difference(old_i.index)))


if __name__ == '__main__':
    main()
