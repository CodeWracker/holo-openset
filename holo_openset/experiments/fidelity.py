"""Fidelity of each reconstruction to the object (PSNR of the modulus against the amplitude of the letters, after the
best affine fit, test split of the base set), the twin-image removal traced pass by pass, and the error of the blind
autofocus against the true distance of each hologram.

    python -m holo_openset experiment fidelity --device cuda:N [--n 800]
Output: results/holo_openset/fidelity.json
"""
from holo_openset import paths
from holo_openset.experiments.common import device, parser
from holo_openset.reconstruct import fidelity


def main(argv=None):
    ap = parser(__doc__)
    ap.add_argument('--n', type=int, default=None)
    a = ap.parse_args(argv)
    dev = device(a)
    paths.RESULTS.mkdir(parents=True, exist_ok=True)
    print(fidelity(paths.dataset(paths.BASE), dev, a.n, paths.RESULTS / 'fidelity.json'))
