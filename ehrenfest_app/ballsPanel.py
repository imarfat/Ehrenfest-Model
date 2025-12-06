import math
from matplotlib.lines import Line2D # type: ignore
import numpy as np # type: ignore


class BallsPanel:
    """Handles drawing balls inside Box A and Box B with optional animations."""

    def __init__(self, ax, N=20, scheduler=None):
        self.ax = ax
        self.scheduler = scheduler
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
        self.box_edges = {'A': {}, 'B': {}}
        self.box_labels = {'A': None, 'B': None}
        self.base_box_top = 0.85
        self.base_box_bottom = 0.05
        self.anim_box_top = 0.74
        self.anim_box_bottom = 0.16
        self.box_top = self.base_box_top
        self.box_bottom = self.base_box_bottom
        self.box_gap = 0.02
        self.prev_X = None
        self.current_positions = {'A': [], 'B': []}
        self.point_size = 30

        # Animation state
        self.user_animation_enabled = False
        self.animation_allowed = False
        self.animating = False
        self.anim_circle = None
        self.anim_path = []
        self.anim_index = 0
        self.animation_after_id = None
        self.animation_complete_cb = None
        self.animation_interval_ms = 1
        self.frames_per_tick = 2

    def set_animation_enabled(self, enabled: bool):
        self.user_animation_enabled = bool(enabled)
        self.animation_allowed = self.user_animation_enabled and self.N <= 200
        self._update_box_bounds()
        
        if not self.animation_allowed:
            self.cancel_animation()
            
        self._update_box_top_visibility()
        self.force_redraw()

    def set_animation_complete_callback(self, callback):
        self.animation_complete_cb = callback

    def cancel_animation(self):
        if self.animation_after_id and self.scheduler is not None:
            try:
                self.scheduler.after_cancel(self.animation_after_id)
            except Exception:
                pass
        self.animation_after_id = None
        
        if self.anim_circle is not None:
            self.anim_circle.set_visible(False)
            
        if self.animating and self.current_positions:
            self._update_scatter(self.current_positions)
            
        self.animating = False
        self.anim_path = []
        self.anim_index = 0
        self.ax.figure.canvas.draw_idle()

    def _grid_dims(self, count, w, h):
        if count == 0:
            return 0, 0
        cols = math.ceil(math.sqrt(count * w / h))
        cols = max(1, cols)
        rows = math.ceil(count / cols)
        return rows, cols

    def update(self, X, N=None):
        prev_positions = self._clone_positions(self.current_positions)
        prev_X = self.prev_X

        if N is not None:
            self.N = int(N)
        self.X = int(X)

        self.animation_allowed = self.user_animation_enabled and self.N <= 200
        self._update_box_bounds()
        self._update_box_top_visibility()

        positions = self._draw_and_collect_positions()
        self.current_positions = positions

        animation_started = self._maybe_start_animation(prev_positions, positions, prev_X, self.X)
        if not animation_started:
            self._update_scatter(positions)

        self.prev_X = self.X
        return animation_started

    def _draw_and_collect_positions(self):
        self._update_box_bounds()
        left = 0.05
        mid = 0.5
        bottom = self.box_bottom
        top = self.box_top
        box_w = mid - left - self.box_gap
        box_h = top - bottom

        self.box_top = top
        self.box_bottom = bottom

        if not self.boxes_drawn:
            self.ax.clear()
            self.scatter = None
            self.anim_circle = None
            self.box_edges = {'A': {}, 'B': {}}
            self.box_labels = {'A': None, 'B': None}
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

            self._create_box_outline('A', left, bottom, box_w, box_h, 'Box A')
            self._create_box_outline('B', mid + self.box_gap, bottom, box_w, box_h, 'Box B')
            self.ax.set_xlim(0, 1)
            self.ax.set_ylim(0, 1)
            self.boxes_drawn = True
            self._update_box_top_visibility()

        counts = [self.X, self.N - self.X]
        boxes_x = [left + 0.01, mid + 0.03]

        total = max(1, self.N)
        per_box_max = math.ceil(total)
        rows, cols = self._grid_dims(per_box_max, box_w, box_h)
        
        if rows == 0 or cols == 0:
            rows, cols = 1, 1
            
        usable_w = max(0.001, box_w - 0.02)
        usable_h = max(0.001, box_h - 0.02)
        cell_w = usable_w / cols
        spacing_scale = self._vertical_spacing_scale()
        effective_h = max(0.001, usable_h * spacing_scale)
        cell_h = effective_h / rows
        
        if spacing_scale < 1.0:
            vertical_padding = 0.0
        else:
            vertical_padding = max(0.0, (usable_h - effective_h) / 2)

        positions = {'A': [], 'B': []}
        
        for i, count in enumerate(counts):
            if count <= 0:
                continue
            bx = boxes_x[i]
            by = bottom + 0.01 + vertical_padding
            placed = 0
            
            for row in range(rows):
                for col in range(cols):
                    if placed >= count:
                        break
                    cx = bx + (col + 0.5) * cell_w
                    cy = by + (row + 0.5) * cell_h
                    box_key = 'A' if i == 0 else 'B'
                    positions[box_key].append([cx, cy])
                    placed += 1
                if placed >= count:
                    break

        self.point_size = self._compute_point_size(cell_w, cell_h)
        return positions

    def _compute_point_size(self, cell_w, cell_h):
        r = 0.6 * min(cell_w, cell_h)
        if self.N <= 20:
            return np.pi * (r * 300)**2
        if self.N < 100:
            return np.pi * (r * 250)**2
        if self.N < 200:
            return np.pi * (r * 200)**2
        if self.N < 500:
            return np.pi * (r * 190)**2
        if self.N < 1500:
            return np.pi * (r * 180)**2
        if self.N < 3000:
            return np.pi * (r * 160)**2
        return np.pi * (r * 140)**2

    def _create_box_outline(self, key, x0, y0, w, h, label):
        lines = {}
        coords = {
            'left': ((x0, y0), (x0, y0 + h)),
            'right': ((x0 + w, y0), (x0 + w, y0 + h)),
            'bottom': ((x0, y0), (x0 + w, y0)),
            'top': ((x0, y0 + h), (x0 + w, y0 + h)),
        }
        
        for edge, ((x1, y1), (x2, y2)) in coords.items():
            line = Line2D([x1, x2], [y1, y2], color=self.box_edge_color, linewidth=1.8)
            self.ax.add_line(line)
            lines[edge] = line
            
        self.box_edges[key] = lines
        label_text = self.ax.text(x0 + w / 2, y0 + h + 0.01, label, ha='center', va='bottom', fontsize=6, color='black')
        self.box_labels[key] = label_text

    def _update_box_top_visibility(self):
        visible = not (self.animation_allowed)
        
        for edges in self.box_edges.values():
            top_line = edges.get('top')
            if top_line is not None:
                top_line.set_visible(visible)
                
        for label in self.box_labels.values():
            if label is not None:
                label.set_visible(visible)
                
        self.ax.figure.canvas.draw_idle()

    def force_redraw(self):
        # Rebuild static geometry to reflect new bounds.
        self.boxes_drawn = False
        positions = self._draw_and_collect_positions()
        self.current_positions = positions
        self._update_scatter(positions)

    def _update_box_bounds(self):
        if self.animation_allowed:
            self.box_top = self.anim_box_top
            self.box_bottom = self.anim_box_bottom
        else:
            self.box_top = self.base_box_top
            self.box_bottom = self.base_box_bottom

    def _update_scatter(self, positions):
        flattened = self._flatten_positions(positions)
        if flattened.size == 0:
            if self.scatter is not None:
                self.scatter.set_offsets(np.empty((0, 2)))
            self.ax.figure.canvas.draw_idle()
            return

        if self.scatter is None:
            self.scatter = self.ax.scatter(
                flattened[:, 0],
                flattened[:, 1],
                s=self.point_size,
                c=self.ball_color,
                edgecolors=self.ball_outline_color,
                linewidths=0.9,
                zorder=2,
            )
        else:
            self.scatter.set_offsets(flattened)
            self.scatter.set_sizes([self.point_size])
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.figure.canvas.draw_idle()

    def _flatten_positions(self, positions):
        if not positions:
            return np.empty((0, 2))
        combined = positions.get('A', []) + positions.get('B', [])
        if not combined:
            return np.empty((0, 2))
        return np.array(combined)

    def _clone_positions(self, positions):
        return {
            'A': [coords[:] for coords in positions.get('A', [])],
            'B': [coords[:] for coords in positions.get('B', [])],
        }

    def _maybe_start_animation(self, prev_positions, new_positions, prev_X, new_X):
        if not self.animation_allowed or prev_X is None:
            return False
        delta = new_X - prev_X
        if abs(delta) != 1:
            return False
        
        from_box = 'A' if delta < 0 else 'B'
        to_box = 'A' if from_box == 'B' else 'B'
        start_candidates = prev_positions.get(from_box) or []
        end_candidates = new_positions.get(to_box) or []
        
        if not start_candidates or not end_candidates:
            return False

        start_pos = start_candidates[-1]
        end_pos = end_candidates[-1]

        if self.animating:
            self.cancel_animation()

        display_positions = self._clone_positions(new_positions)
        display_positions[to_box] = display_positions[to_box][:-1]
        self._update_scatter(display_positions)

        self._start_animation(start_pos, end_pos)
        return True

    def _start_animation(self, start_pos, end_pos):
        if self.scheduler is None:
            return
        
        self.anim_path = self._build_animation_path(start_pos, end_pos)
        if not self.anim_path:
            return
        
        self.anim_index = 0
        self.animating = True

        if self.anim_circle is None:
            self.anim_circle = self.ax.scatter(
                [start_pos[0]],
                [start_pos[1]],
                s=self.point_size,
                c=self.ball_color,
                edgecolors=self.ball_outline_color,
                linewidths=0.9,
                zorder=3,
            )
        else:
            self.anim_circle.set_offsets([start_pos])
            self.anim_circle.set_sizes([self.point_size])
            self.anim_circle.set_visible(True)

        self.ax.figure.canvas.draw_idle()
        self._schedule_next_frame()

    def _schedule_next_frame(self):
        if not self.animating or self.scheduler is None:
            return
        self.animation_after_id = self.scheduler.after(self.animation_interval_ms, self._advance_animation)

    def _advance_animation(self):
        if not self.animating:
            return
        
        for _ in range(self.frames_per_tick):
            if self.anim_index >= len(self.anim_path):
                self._finish_animation()
                return
            pos = self.anim_path[self.anim_index]
            if self.anim_circle is not None:
                self.anim_circle.set_offsets([pos])
            self.anim_index += 1
            
        self.ax.figure.canvas.draw_idle()
        self._schedule_next_frame()

    def _finish_animation(self):
        if self.anim_circle is not None:
            self.anim_circle.set_visible(False)
            
        self.animating = False
        self.animation_after_id = None
        self.anim_path = []
        self.anim_index = 0
        self._update_scatter(self.current_positions)
        
        if callable(self.animation_complete_cb):
            try:
                self.animation_complete_cb()
            except Exception:
                pass

    def _build_animation_path(self, start_pos, end_pos):
        exit_y = min(0.98, self.box_top + 0.08)
        path_points = []
        key_points = [
            start_pos,
            (start_pos[0], exit_y),
            (end_pos[0], exit_y),
            end_pos,
        ]
        steps_per_segment = 14
        ease = self._ease_in_out
        
        for idx in range(len(key_points) - 1):
            p0 = key_points[idx]
            p1 = key_points[idx + 1]
            for step in range(steps_per_segment):
                t = (step + 1) / steps_per_segment
                t = ease(t)
                x = p0[0] + (p1[0] - p0[0]) * t
                y = p0[1] + (p1[1] - p0[1]) * t
                path_points.append((x, y))
                
        return path_points

    @staticmethod
    def _ease_in_out(t):
        # Smoothstep easing for less abrupt motion
        return t * t * (3 - 2 * t)

    def _vertical_spacing_scale(self):
        if self.animation_allowed and self.N == 6:
            return 0.7
        if (not self.animation_allowed) and self.N in (8, 9):
            return 0.7
        return 1.0
