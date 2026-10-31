"""One look for every figure: the categorical palette in a fixed order (each flow keeps its colour everywhere),
thin marks, recessive axes, one y-axis per panel."""
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from holo_openset import paths  # noqa: E402

INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e4e3df'
COLORS = {  # entity -> colour, never by rank
    'raw': '#7d7b75', 'learned': '#2a78d6', 'complex': '#eb6834', 'wiener': '#1baf7a', 'rec_z0': '#6250d6',
    'rec_af': '#e87ba4', 'rec_edf': '#008300', 'rec_twin': '#e34948', 'oracle_pixel': '#eda100',
}
LABELS = {'raw': 'hologram crops', 'learned': 'learned layer (real)', 'complex': 'learned layer (complex)',
          'wiener': 'Wiener filter', 'rec_z0': 'reconstruction at $z_0$', 'rec_af': 'autofocus',
          'rec_edf': 'per-object focus', 'rec_twin': 'autofocus + twin removal', 'oracle_pixel': 'pixel oracle'}
SHORT = {'raw': 'crops', 'learned': 'layer', 'complex': 'complex', 'wiener': 'Wiener', 'rec_z0': 'rec. $z_0$',
         'rec_af': 'autofocus', 'rec_edf': 'per-object', 'rec_twin': 'twin-free', 'oracle_pixel': 'pixel oracle'}
ORDER = ['raw', 'learned', 'complex', 'wiener', 'rec_z0', 'rec_af', 'rec_edf', 'rec_twin']
KNOWN, UNKNOWN = '#2a78d6', '#eb6834'


def setup():
    plt.rcParams.update({
        'font.size': 8, 'axes.titlesize': 8, 'axes.labelsize': 8, 'legend.fontsize': 7, 'xtick.labelsize': 7,
        'ytick.labelsize': 7, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK, 'xtick.color': MUTED,
        'ytick.color': MUTED, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6,
        'axes.spines.top': False, 'axes.spines.right': False, 'lines.linewidth': 1.4, 'lines.markersize': 4,
        'legend.frameon': False, 'figure.dpi': 150, 'savefig.dpi': 300, 'font.family': 'DejaVu Sans',
        'image.cmap': 'gray', 'axes.titlelocation': 'left'})


def save(fig, name):
    paths.PAPER.mkdir(parents=True, exist_ok=True)
    fig.savefig(paths.PAPER / f'{name}.pdf', bbox_inches='tight', pad_inches=0.02)
    fig.savefig(paths.PAPER / f'{name}.png', bbox_inches='tight', pad_inches=0.02, dpi=200)
    plt.close(fig)
    print('wrote', paths.PAPER / f'{name}.pdf')


def show(ax, img, title=None, lo=1, hi=99, cmap='gray', vmin=None, vmax=None):
    """An image stretched to its own percentiles (or to vmin/vmax), no ticks."""
    img = np.asarray(img, np.float32)
    if vmin is None:
        vmin, vmax = np.percentile(img, [lo, hi])
    ax.imshow(img, cmap=cmap, vmin=vmin, vmax=vmax, interpolation='nearest')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    if title:
        ax.set_title(title, loc='center', fontsize=6.5, pad=2)


def panel(ax, letter):
    ax.text(-0.02, 1.02, f'({letter})', transform=ax.transAxes, fontsize=8, fontweight='bold', va='bottom',
            ha='right', color=INK)
