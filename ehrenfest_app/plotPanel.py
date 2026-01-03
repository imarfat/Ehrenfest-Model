import math
import numpy as np # type: ignore
from matplotlib.collections import PolyCollection # type: ignore
from matplotlib.ticker import FuncFormatter, MaxNLocator, MultipleLocator # type: ignore


class PlotPanel:
    def __init__(self, ax, N=20):
        self.ax = ax
        self.N = N
        self.history = []
        self.mode = 'realtime'
        self.texts = {
            'title_realtime': r'Real Time Trajectory of $X_i$',
            'title_condensed': r'Timelapsed Trajectory of $X_i$',
            'x_label': 'Iteration',
            'y_label': r'$X_i$ (balls in A)',
            'mean_label': 'Mean (N/2 = {value:.1f})',
            'trajectory_label': 'Trajectory',
            'current_label': 'Current value',
        }
        self.ax.grid(True, linestyle='--', alpha=0.4)

        self.mean_line = self.ax.axhline(
            self.N / 2, color='r', alpha=0.8,
            linestyle='--', linewidth=0.5,
            label=self._mean_label()
        )
        (self.history_line,) = self.ax.plot([], [], '-b', lw=1, label=self.texts['trajectory_label'])
        (self.last_point,) = self.ax.plot([], [], 'o', color='#fb923c', label=self.texts['current_label'])

        (self.condensed_line,) = self.ax.plot([], [], '-b', lw=1, visible=False)
        self.condensed_fill = PolyCollection([], facecolor='C0', alpha=0.18)
        self.condensed_fill.set_visible(False)
        self.ax.add_collection(self.condensed_fill)

        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, max(1, self.N))
        self.ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        self.ax.xaxis.set_major_locator(MultipleLocator(1))
        self.ax.xaxis.set_major_formatter(FuncFormatter(self._format_tick_value))
        self.legend = None
        self._apply_texts()

    def _mean_label(self):
        template = self.texts.get('mean_label', 'Mean (N/2 = {value:.1f})')
        try:
            return template.format(value=self.N / 2)
        except Exception:
            return template

    def _set_mode(self, mode):
        self.mode = mode
        is_realtime = mode == 'realtime'
        self.history_line.set_visible(is_realtime)
        self.condensed_line.set_visible(not is_realtime)
        self.condensed_fill.set_visible(not is_realtime)
        
        if is_realtime:
            self.ax.grid(True, linestyle='--', alpha=0.4)
        else:
            self.ax.grid(True, linestyle='--', alpha=0.3)
        self._apply_texts()

    def update(self, history, N=None):
        if N is not None:
            self.N = int(N)
        self.history = list(history)
        self._set_mode('realtime')
        self._update_mean_line()
        self._update_realtime_plot()

    def _update_realtime_plot(self):
        if not self.history:
            self.history_line.set_data([], [])
            self.last_point.set_data([], [])
            self.ax.set_xlim(0, 1)
            self.ax.set_ylim(0, max(1, self.N))
            return

        x = np.arange(len(self.history))
        y = np.asarray(self.history)
        self.history_line.set_data(x, y)
        self.last_point.set_data([x[-1]], [y[-1]])

        xmin = 0
        xmax = x[-1] + 1
        self.ax.set_xlim(xmin, xmax)
        self.ax.set_ylim(0, max(1, self.N))
        self._update_xticks(xmax - xmin)
        self.ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    def _update_xticks(self, x_range):
        x_range = max(1, float(x_range))
        target_ticks = 6
        rough_step = max(1.0, x_range / target_ticks)
        magnitude = 10 ** math.floor(math.log10(rough_step))
        for multiplier in (1, 2, 5, 10):
            step = magnitude * multiplier
            if x_range / step <= target_ticks:
                break
        self.ax.xaxis.set_major_locator(MultipleLocator(step))

    def _update_mean_line(self):
        y = self.N / 2.0
        self.mean_line.set_ydata([y, y])
        self.mean_line.set_label(self._mean_label())
        self._refresh_legend()

    def show_condensed_time(self, history, N, target_points=800):
        self.N = int(N)
        hist = np.asarray(history, dtype=float)
        L = len(hist)
        self._set_mode('condensed')
        self._update_mean_line()

        if L == 0:
            self.condensed_line.set_data([], [])
            self.condensed_fill.set_verts([])
            self.last_point.set_data([], [])
            return

        if L <= target_points:
            xs = np.arange(L, dtype=float)
            means = hist
            mins = hist
            maxs = hist
        else:
            bins = min(target_points, L)
            counts = np.full(bins, L // bins, dtype=int)
            remainder = L % bins
            counts[:remainder] += 1
            indices = np.cumsum(counts)
            start = 0
            xs = []
            means = []
            mins = []
            maxs = []
            
            for end in indices:
                segment = hist[start:end]
                if segment.size == 0:
                    continue
                xs.append((start + end - 1) / 2.0)
                means.append(segment.mean())
                mins.append(segment.min())
                maxs.append(segment.max())
                start = end
                
            xs = np.asarray(xs)
            means = np.asarray(means)
            mins = np.asarray(mins)
            maxs = np.asarray(maxs)

        self.condensed_line.set_data(xs, means)
        verts = self._build_fill_between(xs, mins, maxs)
        self.condensed_fill.set_verts([verts] if len(verts) else [])
        
        if xs.size > 0:
            self.last_point.set_data([xs[-1]], [means[-1]])
        else:
            self.last_point.set_data([], [])
            
        self.ax.set_xlim(0, max(1, L))
        self._update_xticks(max(1, L))
        self.ax.set_ylim(0, max(1, self.N))
        self.ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    def _build_fill_between(self, xs, mins, maxs):
        if xs.size == 0:
            return np.empty((0, 2))
        upper = np.column_stack([xs, maxs])
        lower = np.column_stack([xs[::-1], mins[::-1]])
        return np.vstack([upper, lower])

    def _format_tick_value(self, value, _pos):
        value = int(round(value))
        abs_val = abs(value)
        if abs_val >= 1_000_000:
            formatted = f"{value / 1_000_000:.1f}".rstrip('0').rstrip('.')
            return f"{formatted}M"
        if abs_val >= 1_000:
            formatted = f"{value / 1_000:.1f}".rstrip('0').rstrip('.')
            return f"{formatted}K"
        return str(value)

    def set_texts(self, texts):
        if not isinstance(texts, dict):
            return
        updated = False
        for key in (
            'title_realtime',
            'title_condensed',
            'x_label',
            'y_label',
            'mean_label',
            'trajectory_label',
            'current_label',
        ):
            if key in texts and isinstance(texts[key], str):
                if self.texts.get(key) != texts[key]:
                    self.texts[key] = texts[key]
                    updated = True
        if updated:
            self._apply_texts()

    def _apply_texts(self):
        title_key = 'title_realtime' if self.mode == 'realtime' else 'title_condensed'
        self.ax.set_title(self.texts.get(title_key, ''), pad=12)
        self.ax.set_xlabel(self.texts.get('x_label', ''), labelpad=5)
        self.ax.set_ylabel(self.texts.get('y_label', ''))
        if self.history_line is not None:
            self.history_line.set_label(self.texts.get('trajectory_label', ''))
        if self.last_point is not None:
            self.last_point.set_label(self.texts.get('current_label', ''))
        if self.mean_line is not None:
            self.mean_line.set_label(self._mean_label())
        self._refresh_legend()

    def _refresh_legend(self):
        handles = [h for h in (self.history_line, self.last_point, self.mean_line) if h is not None]
        if not handles:
            return
        self.legend = self.ax.legend(handles=handles, fontsize=7)
