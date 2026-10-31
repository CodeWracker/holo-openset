"""Gallery = labelled embeddings + an acceptance threshold. This is what makes the system OPEN:

* a query is compared (cosine similarity) with every gallery embedding; its score is the maximum similarity;
* score >= threshold  -> the query is the label of its nearest gallery item;
* score <  threshold  -> "unknown" (nothing like it is enrolled);
* adding a new class never requires retraining: enroll a few examples of it and it is recognised.

The threshold is calibrated with GENUINE pairs only (target false-rejection rate), so it makes no assumption
about what unknown patterns look like: gallery images are split in two halves (even / odd image ids); each crop
of one half is matched against the other half, and the threshold is the `frr` quantile of those genuine scores.

Per-class thresholds: classes the network was trained on are very compact, classes enrolled later are less so, and
a single global threshold rejects almost every newly enrolled class. Each class c therefore gets
    t_c = min(t_global, frr-quantile of the leave-one-image-out max similarity among the examples of c),
i.e. never stricter than the global threshold; a class with examples from a single image keeps t_global.
"""
import json

import numpy as np

UNKNOWN = 'unknown'


class Gallery:
    def __init__(self, embeddings, labels, image_ids=None, threshold=None, meta=None, boxes=None):
        self.embeddings = np.asarray(embeddings, np.float32)
        self.labels = np.asarray(labels).astype(str)
        self.image_ids = np.asarray(image_ids if image_ids is not None else np.arange(len(self.labels)))
        self.boxes = np.asarray(boxes if boxes is not None else np.zeros((len(self.labels), 4)), np.float32)
        self.threshold = threshold
        self.meta = meta or {}

    # ---------------------------------------------------------------- persistence
    def save(self, path):
        np.savez_compressed(path, embeddings=self.embeddings, labels=self.labels, image_ids=self.image_ids,
                            boxes=self.boxes,
                            threshold=np.float32(np.nan if self.threshold is None else self.threshold),
                            meta=json.dumps(self.meta))

    @classmethod
    def load(cls, path):
        z = np.load(path, allow_pickle=False)
        t = float(z['threshold'])
        return cls(z['embeddings'], z['labels'], z['image_ids'], None if np.isnan(t) else t, json.loads(str(z['meta'])),
                   z['boxes'])

    # ---------------------------------------------------------------- enrollment / calibration
    def add(self, embeddings, labels, image_ids=None, boxes=None):
        self.embeddings = np.concatenate([self.embeddings, np.asarray(embeddings, np.float32)])
        self.labels = np.concatenate([self.labels, np.asarray(labels).astype(str)])
        ids = image_ids if image_ids is not None else np.full(len(labels), -1)
        self.image_ids = np.concatenate([self.image_ids, np.asarray(ids)])
        b = boxes if boxes is not None else np.zeros((len(labels), 4))
        self.boxes = np.concatenate([self.boxes, np.asarray(b, np.float32)])
        if self.threshold is not None:
            self.class_thresholds()

    def class_thresholds(self, frr=None):
        frr = self.meta.get('frr_target', 0.05) if frr is None else frr
        out = {}
        for c in np.unique(self.labels):
            i = np.where(self.labels == c)[0]
            s = self.embeddings[i] @ self.embeddings[i].T
            s[self.image_ids[i][:, None] == self.image_ids[i][None, :]] = -2
            g = s.max(1)
            g = g[g > -2]
            out[str(c)] = float(min(self.threshold, np.quantile(g, frr))) if len(g) else float(self.threshold)
        self.meta['class_thresholds'] = out
        return out

    def calibrate(self, frr=0.05):
        """Genuine-only threshold: even-image half as gallery, odd-image half as queries."""
        ids = np.unique(self.image_ids)
        even = np.isin(self.image_ids, ids[::2])
        g, q = np.where(even)[0], np.where(~even)[0]
        q = q[np.isin(self.labels[q], self.labels[g])]
        if len(q) == 0 or len(g) == 0:
            raise ValueError('need at least two images per class to calibrate the threshold')
        s = self.embeddings[q] @ self.embeddings[g].T
        same = self.labels[q][:, None] == self.labels[g][None, :]
        genuine = np.where(same, s, -2).max(1)
        self.threshold = float(np.quantile(genuine, frr))
        self.meta['frr_target'] = frr
        self.class_thresholds(frr)
        return self.threshold

    # ---------------------------------------------------------------- queries
    def query(self, q_emb, k=5):
        """Returns, per query: decision (label or 'unknown'), score, top-k labels and similarities.
        Top-k is computed over classes (best item of each class), which is what one wants to display."""
        q_emb = np.asarray(q_emb, np.float32).reshape(-1, self.embeddings.shape[1])
        sims = q_emb @ self.embeddings.T
        classes = np.unique(self.labels)
        per_class = np.stack([sims[:, self.labels == c].max(1) for c in classes], 1)
        order = np.argsort(-per_class, 1)[:, :k]
        out = []
        for i in range(len(q_emb)):
            top = [(str(classes[j]), float(per_class[i, j])) for j in order[i]]
            score = top[0][1]
            t = self.threshold_of(top[0][0])
            accept = t is None or score >= t
            out.append(dict(decision=top[0][0] if accept else UNKNOWN, score=score, nearest=top[0][0], topk=top,
                            threshold=t, best_item=int(np.argmax(sims[i]))))
        return out

    def threshold_of(self, label):
        return self.meta.get('class_thresholds', {}).get(str(label), self.threshold)

    def summary(self):
        lab, cnt = np.unique(self.labels, return_counts=True)
        return dict(n=int(len(self.labels)), classes={str(a): int(b) for a, b in zip(lab, cnt)},
                    threshold=self.threshold, **self.meta)
