"""Robustness: every flow, trained and calibrated on the base acquisition, meets test holograms recorded with ONE effect
changed (holo_openset.sim.variants; the same scenes as the base test split, with their own blank frames and their own
reconstructions: python -m holo_openset reconstruct --set variants/<name>).

Gallery, thresholds and models stay those of the base set: the embeddings of the validation patterns come from the
base set and those of the test patterns from the variant (ground-truth boxes: this isolates the front end; the
detector on the variants is measured by the oracle experiment and by e2e on the base set). 'base' is the base test
split itself.

    python -m holo_openset experiment robustness --device cuda:N [--rep ...] [--variants ...] [--flows ...]
Output: results/holo_openset/robustness.csv
"""
import numpy as np
import pandas as pd

from holo_openset import paths
from holo_openset.data import embed_annotations
from holo_openset.experiments.common import KEEP, device, fmt, model, parser, save, strict
from holo_openset.flows import FLOWS, array_name, dataset
from holo_openset.sim.variants import VARIANTS


def main(argv=None):
    ap = parser(__doc__, list(FLOWS))
    ap.add_argument('--variants', nargs='+', default=['base'] + list(VARIANTS))
    a = ap.parse_args(argv)
    dev = device(a)
    base = dataset('raw')
    ann = base.ann
    val, test = (ann.split == 'val').to_numpy(), (ann.split == 'test').to_numpy()
    ref = ann[test].reset_index(drop=True)
    for r in a.rep:
        rows = []
        for flow in a.flows:
            m = model(flow, r, dev)
            if m is None:
                continue
            emb_val = embed_annotations(m, dataset(flow), ann[val])
            for v in a.variants:
                root = paths.dataset(paths.BASE if v == 'base' else f'variants/{v}')
                if not (root / array_name(flow)).exists():
                    print('missing', root / array_name(flow), flush=True)
                    continue
                vann = pd.read_csv(root / 'annotations.csv')
                vtest = vann[vann.split == 'test'].reset_index(drop=True)
                assert (vtest[['image_id', 'x0', 'y0', 'x1', 'y1', 'classe']].values ==
                        ref[['image_id', 'x0', 'y0', 'x1', 'y1', 'classe']].values).all(), f'{v}: not the same scenes'
                emb = np.zeros((len(ann), 128), np.float32)
                emb[val] = emb_val
                emb[test] = embed_annotations(m, dataset(flow, root, ann=vann), ref)
                res = strict(m, base, r, emb)
                effect, value, _ = VARIANTS.get(v, ('base', 'base', {}))
                rows.append(dict(rep=r, variant=v, effect=effect, value=value, flow=flow,
                                 **{k: res[k] for k in KEEP if k in res}))
                print(fmt(rows[-1]), flush=True)
        save(rows, 'robustness', keys=['rep', 'variant', 'flow'])
