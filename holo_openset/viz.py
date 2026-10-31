"""Visual explanation of a prediction.

Top row: input hologram with decisions (green = recognised class, red = unknown) | the same hologram after the
learned Fourier layer (what the network sees). Bottom rows: for each detected pattern, its hologram crop, its
Fourier-view crop and the nearest gallery pattern (hologram crop) with similarity and the acceptance threshold.
"""
import matplotlib

matplotlib.use('Agg')
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from holo_openset.gallery import UNKNOWN  # noqa: E402
from holo_openset.model import square_boxes  # noqa: E402

KNOWN_C, UNKNOWN_C = '#1b9e77', '#d95f02'


def _crop(img, box, buffer=0.25):
    img = np.asarray(img)
    img = img[-1] if img.ndim == 3 else img   # a reconstruction: its modulus channel
    x0, y0, x1, y1 = square_boxes(np.asarray(box)[None], buffer)[0]
    h, w = img.shape
    pad = int(max(0, -x0, -y0, x1 - w, y1 - h)) + 1
    p = np.pad(img, pad, mode='constant', constant_values=float(np.median(img)))
    return p[int(y0) + pad:int(y1) + pad, int(x0) + pad:int(x1) + pad]


def _norm(a):
    lo, hi = np.percentile(a, [1, 99])
    return np.clip((a - lo) / max(hi - lo, 1e-9), 0, 1)


def plot_prediction(holo, fview, dets, gallery=None, dataset=None, out=None, max_rows=8, title=None):
    n = min(len(dets), max_rows)
    fig = plt.figure(figsize=(10, 5.2 + 1.35 * n))
    gs = fig.add_gridspec(2 + n, 4, height_ratios=[4, 0.25] + [1] * n)
    for k, (img, name) in enumerate([(holo, 'input hologram'), (fview, 'what the network sees')]):
        ax = fig.add_subplot(gs[0, 2 * k:2 * k + 2])
        ax.imshow(_norm(img), cmap='gray')
        for i, d in enumerate(dets):
            c = UNKNOWN_C if d['decision'] == UNKNOWN else KNOWN_C
            x0, y0, x1, y1 = d['box']
            ax.add_patch(mpatches.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec=c, lw=1.8))
            ax.text(x0, y0 - 4, f"{i}:{'?' if d['decision'] == UNKNOWN else d['decision']}", color='white', fontsize=8,
                    bbox=dict(fc=c, ec='none', pad=1))
        ax.set_title(name, fontsize=10)
        ax.axis('off')
    thr = gallery.threshold if gallery is not None else None
    for r, d in enumerate(dets[:n]):
        row = 2 + r
        c = UNKNOWN_C if d['decision'] == UNKNOWN else KNOWN_C
        panels = [(_crop(holo, d['box']), f"#{r} hologram crop"), (_crop(fview, d['box']), 'network input')]
        if gallery is not None and dataset is not None:
            j = d['best_item']
            gimg = dataset.image(int(gallery.image_ids[j]))
            panels.append((_crop(gimg, gallery.boxes[j]), f"nearest gallery: {gallery.labels[j]}"))
        for k, (im, name) in enumerate(panels):
            ax = fig.add_subplot(gs[row, k])
            ax.imshow(_norm(im), cmap='gray')
            ax.set_title(name, fontsize=8)
            ax.axis('off')
        ax = fig.add_subplot(gs[row, 3])
        ax.axis('off')
        top = ', '.join(f'{l} {s:.2f}' for l, s in d['topk'][:3])
        ax.text(0, 0.75, f"decision: {d['decision']}", color=c, fontsize=10, weight='bold', transform=ax.transAxes)
        t_d = d.get('threshold', thr)
        ax.text(0, 0.45, f"score {d['score']:.3f}" + (f"  (threshold {t_d:.3f})" if t_d is not None else ''),
                fontsize=8, transform=ax.transAxes)
        ax.text(0, 0.15, f"top-3: {top}", fontsize=8, transform=ax.transAxes)
    if title:
        fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    if out:
        fig.savefig(out, dpi=110)
    plt.close(fig)
