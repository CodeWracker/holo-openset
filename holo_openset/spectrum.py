"""FFT of an image of any size at the speed of a nearby good size.

An FFT is fast when the side of the image splits into small primes. The sensor of the bench does not: its height,
2748 = 2 x 2 x 3 x 229, costs 2.3 times more on a CPU core than 2750 = 2 x 5 x 5 x 5 x 11. So the transforms run on the
image extended, by repeating its last rows and columns, to the next good size, and the result is cropped back. A
640 x 640 window is left as it is.
"""
import torch
from scipy.fft import next_fast_len


def fast_shape(shape):
    return tuple(next_fast_len(n, real=False) for n in shape)


def fast_pad(x):
    """x [..., h, w] -> extended to fast_shape((h, w)) (x itself when it already has that size)."""
    h, w = x.shape[-2:]
    H, W = fast_shape((h, w))
    if H > h:
        x = torch.cat([x, x[..., -1:, :].expand(*x.shape[:-2], H - h, w)], -2)
    if W > w:
        x = torch.cat([x, x[..., :, -1:].expand(*x.shape[:-1], W - w)], -1)
    return x
