"""Class splits of the five repetitions: 21 seen classes for training, 5 never seen (data/partitions)."""
import json
import random

from holo_openset.paths import PARTITIONS

REPS = (1, 2, 3, 4, 5)


def classes(rep):
    """-> (seen, unseen), sorted lists of letters."""
    seen = json.load(open(PARTITIONS / f'r{rep}_seen_classes.json'))['classes']
    unseen = json.load(open(PARTITIONS / f'r{rep}_unseen_classes.json'))['classes']
    return sorted(seen), sorted(unseen)


def held_out_seen(rep, n=5):
    """Seen classes left out of the calibration twin of repetition `rep`: the twin is trained on the others, and these
    play the role of novel classes on VALIDATION data, to choose the clustering cut of discovery without ever touching
    the unseen classes."""
    return sorted(random.Random(1000 + rep).sample(classes(rep)[0], n))
