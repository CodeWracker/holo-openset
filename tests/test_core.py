"""Fast checks of what the results rest on; they need no data, no models and no GPU."""
import numpy as np
import torch

from holo_openset.model import FourierLayer
from holo_openset.protocol import classes
from holo_openset.reconstruct import kernel
from holo_openset.reproduce import check
from holo_openset.sim.physics import Physics, sensor_intensity
from holo_openset.sim.scene import make_scene, session

DEV = torch.device('cpu')
SMALL = dict(window=(320, 320), margin=128, reach=64, dust_density=0, sensor_dust_density=0)


def test_partitions_hold_out_five_classes():
    for r in range(1, 6):
        seen, unseen = map(set, classes(r))
        assert len(seen) == 21 and len(unseen) == 5 and not seen & unseen


def test_propagation_is_undone_by_the_opposite_distance():
    forward = kernel((32, 48), [0.01925], DEV, sign=-1)
    back = kernel((32, 48), [0.01925], DEV, sign=+1)
    assert torch.allclose(forward * back, torch.ones_like(forward), atol=1e-5)


def test_layer_starts_as_the_identity_on_any_size():
    layer = FourierLayer(mode='radial').eval()
    x = torch.randn(1, 96, 160)
    assert torch.allclose(layer(x)[0, 0], x, atol=1e-5)


def test_complex_layer_gives_three_channels():
    assert FourierLayer(mode='complex').eval()(torch.randn(2, 64, 64)).shape == (2, 3, 64, 64)


def test_simulation_repeats_from_its_seed():
    p = Physics().replace(**SMALL)
    a, b = [sensor_intensity(dict(make_scene(5, p), sensor_dust=[]), session(1, p), p, DEV).numpy() for _ in range(2)]
    assert np.array_equal(a, b)


def test_tables_of_the_paper_match_the_results():
    assert check() == 0
