import math
import numpy as np  # type: ignore
from matplotlib.ticker import MaxNLocator  # type: ignore


DEFAULT_TEXTS = {
    'title': r'Empirical distribution of $X_i$ vs $\mathrm{Bin}(N, 1/2)$',
    'x_label': 'State n (balls in A)',
    'y_label': 'Relative frequency',
    'empirical_label': 'Simulation (L = {L:,})',
    'binomial_label': r'Theoretical $\mathrm{Bin}(N,\, 1/2)$',
}


def _binomial_pmf(N):
    """Numerically stable PMF for Bin(N, 1/2) over k = 0..N."""
    ks = np.arange(N + 1)
    log_pmf = np.array([
        math.lgamma(N + 1) - math.lgamma(k + 1) - math.lgamma(N - k + 1)
        for k in ks
    ]) - N * math.log(2.0)
    return np.exp(log_pmf)


def draw_histogram(ax, history, N, texts=None):
    """Render the empirical distribution of a history sequence against Bin(N, 1/2).

    ax        : matplotlib Axes (will be cleared).
    history   : iterable of X_i values in {0, ..., N}.
    N         : total number of particles.
    texts     : optional dict overriding labels (see DEFAULT_TEXTS).
    """
    merged = dict(DEFAULT_TEXTS)
    if texts:
        merged.update({k: v for k, v in texts.items() if isinstance(v, str)})

    ax.clear()
    if N <= 0:
        ax.set_title(merged['title'])
        return

    data = np.asarray(list(history), dtype=int)
    data = data[(data >= 0) & (data <= N)]
    L = int(data.size)

    centers = np.arange(N + 1)
    pmf = _binomial_pmf(N)

    if L == 0:
        freq = np.zeros_like(pmf)
    else:
        edges = np.arange(-0.5, N + 1.5)
        counts, _ = np.histogram(data, bins=edges)
        total = counts.sum()
        freq = counts / total if total > 0 else counts.astype(float)

    empirical_label = merged['empirical_label']
    try:
        empirical_label = empirical_label.format(L=L)
    except Exception:
        pass

    ax.bar(
        centers, freq,
        width=0.9,
        color='#1f4d7a', alpha=0.75,
        edgecolor='white', linewidth=0.4,
        label=empirical_label,
        zorder=2,
    )
    ax.plot(
        centers, pmf,
        marker='o', linestyle='-',
        color='#e53935', markersize=4, linewidth=1.2,
        label=merged['binomial_label'],
        zorder=3,
    )

    ymax = max(float(freq.max() if freq.size else 0.0), float(pmf.max())) * 1.15
    if ymax <= 0:
        ymax = 1.0
    ax.set_xlim(-0.5, N + 0.5)
    ax.set_ylim(0.0, ymax)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=10))
    ax.set_title(merged['title'], pad=12, fontsize=14)
    ax.set_xlabel(merged['x_label'], labelpad=8, fontsize=11)
    ax.set_ylabel(merged['y_label'], fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.4, axis='y')
    ax.legend(fontsize=9, loc='best')
