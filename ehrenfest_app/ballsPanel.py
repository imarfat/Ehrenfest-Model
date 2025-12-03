import math
from matplotlib.patches import Circle, Rectangle # type: ignore
from matplotlib.collections import PatchCollection # type: ignore
import numpy as np # type: ignore


class BallsPanel:
    """Handles drawing balls inside Box A and Box B."""

    def __init__(self, ax, N=20):
        self.ax = ax
        self.N = N
        self.X = 0
        self.box_padding = 0.05
        self.ball_color = "#1f4d7a"
        self.ball_outline_color = "#000000"
        self.box_edge_color = "#342110"
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.scatter = None
        self.boxes_drawn = False

    def update(self, X, N=None):
        if N is not None:
            self.N = int(N)
        self.X = int(X)
        self.draw()

    def _grid_dims(self, count, w, h):
        if count == 0:
            return 0, 0
        cols = math.ceil(math.sqrt(count * w / h))
        cols = max(1, cols)
        rows = math.ceil(count / cols)
        return rows, cols

    def draw(self):
        
        left = 0.05
        mid = 0.5
        bottom = 0.05
        top = 0.85
        box_w = mid - left - 0.02
        box_h = top - bottom
        
        if not self.boxes_drawn:
            self.ax.clear()
            self.ax.set_title('The Ehrenfest Model')
            subtitle = r'A stochastic simulation of balls moving between two boxes.'
            subsubtitle = r'$X_i$ ~ number of balls in Box A at iteration $i$'
            try:
                self.ax.text(
                    0.5, 0.985, subtitle,
                    ha='center', va='top',
                    transform=self.ax.transAxes,
                    fontsize=9,
                    color='black'
                )
                self.ax.text(
                    0.5, 0.94, subsubtitle,
                    ha='center', va='top',
                    transform=self.ax.transAxes,
                    fontsize=8,
                    color='#333333'
                )
            except Exception:
                pass

    
            self.ax.axis('off')

            rectA = Rectangle((left, bottom), box_w, box_h, fill=False, linewidth=1.8, edgecolor=self.box_edge_color)
            rectB = Rectangle((mid + 0.02, bottom), box_w, box_h, fill=False, linewidth=1.8, edgecolor=self.box_edge_color)
            self.ax.add_patch(rectA)
            self.ax.add_patch(rectB)
            self.ax.text(left + box_w/2, top + 0.01, 'Box A', ha='center', va='bottom', fontsize=6, color='black')
            self.ax.text(mid + box_w/2 + 0.02, top + 0.01, 'Box B', ha='center', va='bottom', fontsize=6, color='black')
        
            self.ax.set_xlim(0, 1)
            self.ax.set_ylim(0, 1)
            self.boxes_drawn = True

        counts = [self.X, self.N - self.X]
        boxes_x = [left + 0.01, mid + 0.03]

        total = max(1, self.N)
        per_box_max = math.ceil(total)
        rows, cols = self._grid_dims(per_box_max, box_w, box_h)
        if rows == 0 or cols == 0:
            rows, cols = 1, 1
        cell_w = (box_w - 0.02) / cols
        cell_h = (box_h - 0.02) / rows
        r = 0.6 * min(cell_w, cell_h)

        # Collect ball positions
        positions = []
        for i, count in enumerate(counts):
            if count <= 0:
                continue
            bx = boxes_x[i]
            by = bottom + 0.01
            placed = 0
            for row in range(rows):
                for col in range(cols):
                    if placed >= count:
                        break
                    cx = bx + (col + 0.5) * cell_w
                    cy = by + (row + 0.5) * cell_h
                    positions.append([cx, cy])
                    placed += 1
                if placed >= count:
                    break

        if len(positions) > 0:
            positions = np.array(positions)
            if self.N <= 20:
                point_size = np.pi * (r * 300)**2
            elif self.N < 100:
                point_size = np.pi * (r * 250)**2
            elif self.N < 200:
                point_size = np.pi * (r * 200)**2
            elif self.N < 500:
                point_size = np.pi * (r * 190)**2
            elif self.N < 1500:
                point_size = np.pi * (r * 180)**2
            elif self.N < 3000:
                point_size = np.pi * (r * 160)**2
            else:
                point_size = np.pi * (r * 140)**2

            if self.scatter is None:
                self.scatter = self.ax.scatter(
                    positions[:, 0], positions[:, 1],
                    s=point_size,
                    c=self.ball_color,
                    edgecolors=self.ball_outline_color,
                    linewidths=0.9,
                    zorder=2
                )
            else:
                # Just update positions - much faster!
                self.scatter.set_offsets(positions)
                self.scatter.set_sizes([point_size])
        elif self.scatter is not None:
            # No balls to show
            self.scatter.set_offsets(np.empty((0, 2)))
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.figure.canvas.draw_idle()
