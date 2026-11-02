"""The compared flows: the same network and training recipe, fed with a different treatment of the hologram.

  raw       crops of the hologram (no treatment of diffraction)
  learned   the learnable Fourier layer, one real weight per radius (the proposed method; no optical parameter)
  complex   the learnable Fourier layer with one complex weight per radius (real part, imaginary part, modulus)
  wiener    a fixed Wiener filter of the absorption part, C / (C^2 + eps), in place of the layer (lambda, z0, pixel)
  rec_z0    numerical back-propagation at the nominal distance z0 (a calibrated set-up: what the bench does)
  rec_af    back-propagation at the distance found by the blind autofocus of each hologram (114 reconstructions)
  rec_edf   each object at the distance at which it is sharpest (per-object focus; needs boxes)
  rec_twin  autofocus + iterative twin-image removal (the complete conventional reconstruction)
"""
from holo_openset import paths
from holo_openset.data import Array, Dataset

FLOWS = {
    'raw': dict(mode='none', fourier='learned', rec=None),
    'learned': dict(mode='radial', fourier='learned', rec=None),
    'complex': dict(mode='complex', fourier='learned', rec=None),
    'wiener': dict(mode='radial', fourier='wiener', rec=None),
    # the phase of the propagation: one scalar calibrated on the holograms (the proposed method)
    'prop': dict(mode='prop', fourier='learned', rec=None),
    'prop0': dict(mode='prop', fourier='learned', rec=None, train=dict(alpha_init=0.0, lr_alpha=3e-5)),
    'bank': dict(mode='bank', fourier='learned', rec=None, train=dict(n_dist=5)),
    'prop_jit': dict(mode='prop', fourier='learned', rec=None, train=dict(alpha_jitter=0.05)),
    'bank_jit': dict(mode='bank', fourier='learned', rec=None, train=dict(n_dist=5, alpha_jitter=0.05)),
    'bank_wide': dict(mode='bank', fourier='learned', rec=None,
                      train=dict(n_dist=7, alpha_spread=0.12, alpha_jitter=0.12)),
    # the width of the stack against the jitter (ablation); bank_w3 is the variant of the paper
    'bank_w1': dict(mode='bank', fourier='learned', rec=None, train=dict(n_dist=7, alpha_spread=0.08, alpha_jitter=0.08)),
    'bank_w2': dict(mode='bank', fourier='learned', rec=None, train=dict(n_dist=9, alpha_spread=0.12, alpha_jitter=0.12)),
    'bank_w3': dict(mode='bank', fourier='learned', rec=None, train=dict(n_dist=7, alpha_spread=0.12, alpha_jitter=0.05)),
    'rec_z0': dict(mode='none', fourier='learned', rec='z0'),
    'rec_af': dict(mode='none', fourier='learned', rec='af'),
    'rec_edf': dict(mode='none', fourier='learned', rec='edf'),
    'rec_twin': dict(mode='none', fourier='learned', rec='twin'),
}
HOLOGRAM_FLOWS = ['raw', 'learned', 'complex', 'wiener', 'prop', 'prop0', 'bank', 'prop_jit', 'bank_jit', 'bank_wide', 'bank_w1', 'bank_w2', 'bank_w3']
LABELS = {'raw': 'hologram crops', 'learned': 'learned layer', 'complex': 'complex layer', 'wiener': 'Wiener filter',
          'prop': 'learned propagation', 'prop0': 'learned propagation, from the identity',
          'bank': 'learned focal stack', 'prop_jit': 'learned propagation, distance jitter',
          'bank_jit': 'learned focal stack, distance jitter', 'bank_wide': 'learned focal stack, 7 distances over 12 %',
          'rec_z0': 'reconstruction at z0', 'rec_af': 'autofocus', 'rec_edf': 'per-object focus',
          'rec_twin': 'autofocus + twin removal', 'oracle_pixel': 'pixel oracle'}


def array_name(flow):
    rec = FLOWS[flow]['rec']
    return 'holograms.npy' if rec is None else f'rec_{rec}.npy'


def dataset(flow, root=None, ann=None):
    """The images a flow receives, for a set (default: the base set)."""
    return Dataset(root or paths.dataset(paths.BASE), array_name(flow), ann=ann)


def aux_scenes(flow, rep, root=None, cal=False):
    """(images, boxes) of the auxiliary training scenes of repetition rep, as the flow receives them."""
    root = root or paths.dataset(paths.BASE)
    name = f'r{rep}_cal' if cal else f'r{rep}'
    rec = FLOWS[flow]['rec']
    images = root / 'aux' / (f'{name}_images.npy' if rec is None else f'{name}_rec_{rec}.npy')
    return images, root / 'aux' / f'{name}_boxes.csv'


__all__ = ['FLOWS', 'HOLOGRAM_FLOWS', 'LABELS', 'array_name', 'dataset', 'aux_scenes', 'Array']
