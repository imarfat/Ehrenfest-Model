import math
from matplotlib.patches import Circle, Rectangle # type: ignore
from matplotlib.collections import PatchCollection # type: ignore


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
        self.ax.clear()
        self.ax.set_title('The Ehrenfest Model')
        subtitle = r'A stochastic simulation of balls moving between two boxes.'
        subsubtitle = r'$X_i$ ~ number of balls in Box A at iteration $i$'
        try:
            # main title / subtitle
            self.ax.text(
                0.5, 0.985, subtitle,
                ha='center', va='top',
                transform=self.ax.transAxes,
                fontsize=9,
                color='black'
            )
            # subsubtitle: smaller, muted, placed just below the subtitle
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

        left = 0.05
        mid = 0.5
        right = 0.95
        bottom = 0.05
        top = 0.85
        box_w = mid - left - 0.02
        box_h = top - bottom

        rectA = Rectangle((left, bottom), box_w, box_h, fill=False, linewidth=1.8, edgecolor=self.box_edge_color)
        rectB = Rectangle((mid + 0.02, bottom), box_w, box_h, fill=False, linewidth=1.8, edgecolor=self.box_edge_color)
        self.ax.add_patch(rectA)
        self.ax.add_patch(rectB)
        self.ax.text(left + box_w/2, top + 0.01, 'Box A', ha='center', va='bottom', fontsize=6, color='black')
        self.ax.text(mid + box_w/2 + 0.02, top + 0.01, 'Box B', ha='center', va='bottom', fontsize=6, color='black')

        counts = [self.X, self.N - self.X]
        boxes_x = [left + 0.01, mid + 0.03]

        total = max(1, self.N)
        per_box_max = math.ceil(total)
        rows, cols = self._grid_dims(per_box_max, box_w, box_h)
        if rows == 0 or cols == 0:
            rows, cols = 1, 1
        cell_w = (box_w - 0.02) / cols
        cell_h = (box_h - 0.02) / rows
        r = 0.35 * min(cell_w, cell_h)

        # Build Circle patches and add them as a single PatchCollection for better performance
        patches = []
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
                    # place rows starting at the bottom and building upward
                    cy = by + (row + 0.5) * cell_h
                    patches.append(Circle((cx, cy), r))
                    placed += 1
                if placed >= count:
                    break

        if patches:
            coll = PatchCollection(patches, facecolor=self.ball_color, edgecolor=self.ball_outline_color, linewidths=0.9, zorder=2)
            self.ax.add_collection(coll)

        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.figure.canvas.draw_idle()
