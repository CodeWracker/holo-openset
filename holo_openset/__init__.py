"""holo_openset: open-set recognition of interference patterns in lensless digital in-line holography.

One self-contained pipeline, from the simulated acquisition to the figures of the paper:

    simulate (sim/)  ->  reconstruct (conventional flows)  ->  train (one network per flow)  ->  evaluate
                     ->  experiments (end to end, robustness, full sensor frames, ...)  ->  paper (figures, tables)

The proposed flow: raw hologram -> learnable Fourier layer (whole image) -> crops at detected patterns -> embedding
-> nearest neighbour in a gallery -> known label or "unknown" (open set) -> unknowns grouped into candidate classes.
No numerical reconstruction and no optical parameter is used by it; the conventional flows are compared with it.
"""
__version__ = '2.0.0'
