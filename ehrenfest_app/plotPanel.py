import matplotlib.pyplot as plt # type: ignore
from matplotlib.ticker import MaxNLocator, MultipleLocator # type: ignore
import numpy as np # type: ignore

class PlotPanel:
    def __init__(self, ax, N=20):
        self.ax = ax
        self.N = N
        self.history = []
        self.line = None
        self.ax.set_title(r'Trajectory of $X_i$')
        self.ax.set_xlabel('Iteration')
        self.ax.set_ylabel(r'$X_i$ (balls in A)')
        self.ax.grid(True, linestyle='--', alpha=0.4)

    def update(self, history, N=None):
        if N is not None:
            self.N = int(N)
        self.history = list(history)
        self.draw()

    def draw(self):
        self.ax.clear()
        self.ax.set_title(r'Real Time Trajectory of $X_i$', pad=12)
        self.ax.set_xlabel('Iteration', labelpad=5)
        self.ax.set_ylabel(r'$X_i$ (balls in A)')
        self.ax.grid(True, linestyle='--', alpha=0.4)
        if len(self.history) == 0:
            self.ax.figure.canvas.draw_idle()
            return
        x = list(range(len(self.history)))
        y = self.history
        self.ax.plot(x, y, '-b', lw=1)
        # Highlight most recent point
        self.ax.plot(x[-1], y[-1], 'o', color='#fb923c')
        xmin = 0
        xmax = x[-1] + 1
        self.ax.set_xlim(xmin, xmax)
        self.ax.set_ylim(0, max(1, self.N))
        # Adaptive integer step for x ticks so gaps grow smoothly
        x_range = max(1, int(xmax - xmin))
        target_ticks = 6
        raw_step = max(1, int(round(x_range / float(target_ticks))))
        preferred_steps = [1, 2, 5, 10, 20, 25, 50, 100, 200, 500, 1000]
        step = next((s for s in preferred_steps if s >= raw_step), preferred_steps[-1])
        self.ax.xaxis.set_major_locator(MultipleLocator(step))
        # y ticks remain integer-only
        self.ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        self.ax.figure.canvas.draw_idle()

    

    def show_condensed_time(self, history, N, target_points=800):
        """Render a condensed time-series that represents a long history compactly.

        Approach:
        - If history length <= target_points, draw normally.
        - Otherwise split the history into `target_points` buckets and for each bucket
          compute min, max, and mean. Plot the mean as a thin line and shade between
          min/max to show variability inside a bucket.
        """

        self.N = int(N)
        hist = np.asarray(history, dtype=float)
        L = len(hist)
        self.ax.clear()
        self.ax.set_title(r'Timelapsed Trajectory of $X_i$', pad=12)
        self.ax.set_xlabel('Iteration', labelpad=5)
        self.ax.set_ylabel(r'$X_i$ (balls in A)')
        self.ax.grid(True, linestyle='--', alpha=0.3)

        if L == 0:
            self.ax.figure.canvas.draw_idle()
            return

        if L <= target_points:
            x = np.arange(L)
            self.ax.plot(x, hist, '-b', lw=1)
            self.ax.plot(x[-1], hist[-1], 'o', color='#fb923c')
            xmin = 0
            xmax = max(1, L - 1)
            self.ax.set_xlim(xmin, xmax)
            self.ax.set_ylim(0, max(1, self.N))
            self.ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            self.ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            self.ax.figure.canvas.draw_idle()
            return

        # bucketize into approximately target_points windows
        bins = min(target_points, L)
        # compute start/end indices for each bin
        counts = np.full(bins, L // bins, dtype=int)
        remainder = L % bins
        counts[:remainder] += 1
        indices = np.cumsum(counts)
        start = 0
        means = []
        mins = []
        maxs = []
        xs = []
        for i, end in enumerate(indices):
            seg = hist[start:end]
            if seg.size == 0:
                continue
            means.append(seg.mean())
            mins.append(seg.min())
            maxs.append(seg.max())
            # place x at the mid-iteration of the bucket
            xs.append((start + end - 1) / 2.0)
            start = end

        xs = np.asarray(xs)
        means = np.asarray(means)
        mins = np.asarray(mins)
        maxs = np.asarray(maxs)

        # plot mean line and shaded envelope between min and max
        self.ax.plot(xs, means, '-b', lw=1)
        self.ax.fill_between(xs, mins, maxs, color='C0', alpha=0.18)
        # highlight last bucket's last value
        self.ax.plot(xs[-1], means[-1], 'o', color='#fb923c')

        self.ax.set_xlim(0, L)
        self.ax.set_ylim(0, max(1, self.N))
        self.ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        self.ax.figure.canvas.draw_idle()
