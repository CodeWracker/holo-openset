"""Use of the system on hologram files: detect, treat diffraction as the flow does, embed, decide; and the two-step
demonstration (unknown letters rejected, then recognised after a few examples are enrolled)."""
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from holo_openset import paths
from holo_openset.data import embed_image, load_hologram
from holo_openset.flows import FLOWS
from holo_openset.gallery import UNKNOWN, Gallery
from holo_openset.reconstruct import autofocus, channels, normalise, reconstruct


def load_model_for(a, dev):
    from holo_openset.model import load_model
    return load_model(Path(a.model) if a.model else paths.weights(a.flow, a.rep[0], a.set), dev)[0]


def network_input(holo, flow, boxes, dev, background=None):
    """What the network of a flow receives for one hologram: the hologram itself, or its reconstruction (uint8
    [3, h, w]). Without the blank frame of the session, the hologram is divided by its own mean."""
    rec = FLOWS[flow]['rec']
    if rec is None:
        return holo
    h = torch.from_numpy(np.asarray(holo)).to(dev)
    b = torch.from_numpy(np.asarray(background)).to(dev) if background is not None else h.float().mean()
    a = normalise(h, b)
    z_af = autofocus(a)[0] if rec != 'z0' else None
    return channels(reconstruct(a, rec, z_af, boxes)).cpu().numpy()


def predict(model, flow, gallery, path, detector, dev, background=None, with_embeddings=False):
    holo = load_hologram(path) if isinstance(path, (str, Path)) else np.asarray(path)
    boxes, conf = detector(holo) if not hasattr(detector, 'ann') else detector(path)
    x = network_input(holo, flow, boxes, dev, background)
    emb = embed_image(model, x, boxes)
    res = gallery.query(emb)
    dets = [dict(box=[float(v) for v in b], det_conf=float(c), **r) for b, c, r in zip(boxes, conf, res)]
    if with_embeddings:
        for d, e in zip(dets, emb):
            d['embedding'] = e
    view = model.filtered(torch.from_numpy(np.asarray(x))[None])[0, -1].cpu().numpy()
    return holo, view, dets


def plot(holo, view, dets, gallery, ds, out, title=None):
    from holo_openset.viz import plot_prediction
    plot_prediction(holo, view, dets, gallery, ds, out, title=title)


def demo(a, dev):
    """Step 1: gallery of the seen classes; never-seen letters must come out as 'unknown'. Step 2: a few examples
    of each never-seen class are enrolled (no retraining) and the same letters must now be recognised."""
    from holo_openset.cli import _detector, _images
    from holo_openset.data import embed_annotations
    from holo_openset.protocol import classes
    ds = _images(a)
    model = load_model_for(a, dev)
    rep = a.rep[0]
    seen, unseen = classes(rep)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ann = ds.ann
    val = ann[ann.split == 'val']
    g_rows = val[val.classe.isin(seen)]
    gallery = Gallery(embed_annotations(model, ds, g_rows), g_rows.classe.to_numpy(), g_rows.image_id.to_numpy(),
                      boxes=g_rows[['x0', 'y0', 'x1', 'y1']].to_numpy())
    gallery.calibrate(a.frr)
    det = _detector(a, ds, dev)
    raw = np.load(ds.root / 'holograms.npy', mmap_mode='r')
    bg = np.load(ds.root / 'backgrounds.npy', mmap_mode='r')
    meta = pd.read_csv(ds.root / 'metadata.csv').set_index('image_id')
    test = ann[ann.split == 'test']
    pick = sorted(test[test.classe.isin(unseen)].image_id.unique())[:a.n_images]
    print(f'repetition {rep}: seen = {"".join(seen)}  unseen (never trained) = {"".join(unseen)}')
    print(f'step 1: gallery with {len(g_rows)} val patterns of the seen classes, threshold {gallery.threshold:.3f}')
    summary = []
    for step in (1, 2):
        if step == 2:
            new = val[val.classe.isin(unseen)].groupby('classe', group_keys=False).apply(
                lambda g: g.sample(min(len(g), a.shots), random_state=0))
            gallery.add(embed_annotations(model, ds, new), new.classe.to_numpy(), new.image_id.to_numpy(),
                        new[['x0', 'y0', 'x1', 'y1']].to_numpy())
            print(f'step 2: enrolled {a.shots} examples of each unseen class {"".join(unseen)} (no retraining)')
        for i in pick:
            holo = np.asarray(raw[ds.row[int(i)]])
            truth = ann[ann.image_id == i]
            d = det if not hasattr(det, 'ann') else (lambda _h, t=truth: (t[['x0', 'y0', 'x1', 'y1']].to_numpy(float),
                                                                          np.ones(len(t))))
            _, view, dets = predict(model, a.flow, gallery, holo, d, dev, background=bg[int(meta.loc[i, 'session'])])
            for x in dets:
                j = int(np.argmin(np.abs(truth[['x0', 'y0', 'x1', 'y1']].to_numpy() - np.array(x['box'])).sum(1)))
                x['true'] = truth.classe.iloc[j]
                x['true_is_unseen'] = x['true'] in unseen
            plot(holo, view, dets, gallery, ds, out / f'step{step}_{int(i):06d}.png',
                 title=f'step {step}: ' + ('gallery = seen classes only' if step == 1 else
                                           f'+{a.shots} examples of each unseen class'))
            for x in dets:
                ok = (x['decision'] == UNKNOWN) if (step == 1 and x['true_is_unseen']) else (x['decision'] == x['true'])
                summary.append(dict(step=step, image=int(i), true=x['true'], unseen=x['true_is_unseen'],
                                    decision=x['decision'], score=round(x['score'], 3), correct=bool(ok)))
            print(f'  step {step} {int(i):06d}: ' + ' '.join(
                f"{x['true']}->{'?' if x['decision'] == UNKNOWN else x['decision']}" for x in dets))
    df = pd.DataFrame(summary)
    df.to_csv(out / 'demo_summary.csv', index=False)
    for step, g in df.groupby('step'):
        u, s = g[g.unseen], g[~g.unseen]
        print(f'step {step}: seen correct {s.correct.mean():.3f} | unseen '
              + ('rejected' if step == 1 else 'recognised') + f' {u.correct.mean():.3f}')
    print(f'figures in {out}/')
