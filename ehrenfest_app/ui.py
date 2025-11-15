import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # type: ignore
import matplotlib.pyplot as plt # type: ignore
import numpy as np # type: ignore

from .ehrenfestModel import EhrenfestModel
from .ballsPanel import BallsPanel
from .stateDiagram import StateDiagram
from .plotPanel import PlotPanel
import threading

# Maximum allowed number of balls (for performance reasons)
MAX_N = 10000

class EhrenfestApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Ehrenfest Model Simulation')
        self.running = False
        self.model = EhrenfestModel(N=20)
        self.speed_ms = 200

        # Matplotlib figure with gridspec
        self.fig = plt.Figure(figsize=(10, 6), dpi=100)
        
        # Subtle grainy background texture
        try:
            rng = np.random.RandomState(0)
            noise = rng.normal(loc=0.0, scale=1.0, size=(256, 256))
            # Normalize and slightly bias towards white
            noise = (noise - noise.min()) / (noise.max() - noise.min())
            noise = 0.9 + 0.06 * (noise - 0.5)
            ax_bg = self.fig.add_axes([0, 0, 1, 1], zorder=0)
            ax_bg.imshow(noise, cmap='Greys', aspect='auto', interpolation='bilinear', extent=[0, 1, 0, 1], alpha=0.1)
            ax_bg.set_axis_off()
        except Exception:
            # Continue with plain background if error occurs
            pass

        # Main gridspec layout, 2 rows, 2 columns, left column wider
        gs = self.fig.add_gridspec(2, 2, width_ratios=[1.5, 1])
        # Subplots for balls panel, state diagram, and plot panel
        self.ax_balls = self.fig.add_subplot(gs[:, 0])
        self.ax_state = self.fig.add_subplot(gs[0, 1])
        self.ax_plot = self.fig.add_subplot(gs[1, 1])

        # Nudge the plot panel upwards slightly so it sits higher overall
        pos = self.ax_plot.get_position()
        offset = 0.08
        new_y0 = pos.y0 + offset
        # We need to ensure that we don't exceed the top of the figure
        max_y0 = 0.98 - pos.height
        if new_y0 > max_y0:
            new_y0 = max_y0
        self.ax_plot.set_position([pos.x0, new_y0, pos.width, pos.height])

        # Panels
        self.balls_panel = BallsPanel(self.ax_balls, N=self.model.N)
        self.state_diagram = StateDiagram(self.ax_state, N=self.model.N)
        self.plot_panel = PlotPanel(self.ax_plot, N=self.model.N)

        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

        # Controls frame
        ctrl = ttk.Frame(root)
        ctrl.pack(fill=tk.X, padx=6, pady=4)

        # Buttons
        self.start_btn = ttk.Button(ctrl, text='Start', command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=4)
        self.pause_btn = ttk.Button(ctrl, text='Pause', command=self.pause)
        self.pause_btn.pack(side=tk.LEFT, padx=4)
        self.reset_btn = ttk.Button(ctrl, text='Reset', command=self.reset)
        self.reset_btn.pack(side=tk.LEFT, padx=4)

        # Spinbox for N
        ttk.Label(ctrl, text='N:').pack(side=tk.LEFT, padx=(12,2))
        self.n_var = tk.IntVar(value=self.model.N)
        self.n_spin = tk.Spinbox(ctrl, from_=1, to=4000, textvariable=self.n_var, width=6, command=self.on_n_change)
        self.n_spin.pack(side=tk.LEFT)
        # Ensure typed values get validated when user finishes typing
        try:
            self.n_spin.bind('<FocusOut>', lambda e: self.on_n_change())
            self.n_spin.bind('<Return>', lambda e: self.on_n_change())
        except Exception:
            pass

        # Speed control slider
        ttk.Label(ctrl, text='Speed (ms):').pack(side=tk.LEFT, padx=(12,2))
        self.speed_var = tk.IntVar(value=self.speed_ms)
        # Styling...
        style = ttk.Style()
        style.configure('Sleek.Horizontal.TScale', sliderlength=10)

        self.speed_scale = ttk.Scale(ctrl, from_=10, to=2000, orient=tk.HORIZONTAL, length=220, command=self.on_speed_change, variable=self.speed_var, style='Sleek.Horizontal.TScale')
        self.speed_scale.pack(side=tk.LEFT, padx=(0,6))
        # Label to show current speed value
        self.speed_value_label = ttk.Label(ctrl, text=f'{self.speed_ms} ms', width=8, anchor='w')
        self.speed_value_label.pack(side=tk.LEFT)

        # Status label
        self.status = ttk.Label(ctrl, text='Iteration: 0    X = 0', anchor='e')
        self.status.pack(side=tk.RIGHT, padx=(0, 6))

        # Iterations for condensed run
        self.timelapse_iters_var = tk.IntVar(value=1000)
        self.condense_label = ttk.Label(ctrl, text='Timelapse iterations:')
        self.condense_spin = tk.Spinbox(ctrl, from_=10, to=10000000, increment=10, textvariable=self.timelapse_iters_var, width=8)
        self.timelapse_btn = ttk.Button(ctrl, text='Timelapse', command=self.on_timelapse)

        self.timelapse_btn.pack(side=tk.RIGHT, padx=(0,6))
        self.condense_spin.pack(side=tk.RIGHT, padx=(0,6))
        self.condense_label.pack(side=tk.RIGHT, padx=(12,2))

        # Initial draw
        self.balls_panel.update(self.model.getState(), self.model.N)
        self.state_diagram.update(self.model.getState(), self.model.N, probs=self.model.getTransitionProbabilities())
        self.plot_panel.update(self.model.getHistory(), self.model.N)
        self.canvas.draw_idle()

    def start(self):
        if not self.running:
            self.running = True
            self._run_step()

    def pause(self):
        self.running = False

    def reset(self):
        # Reset model and panels
        self.model.reset(N=self.n_var.get())
        self.balls_panel.update(self.model.getState(), self.model.N)
        self.state_diagram.update(self.model.getState(), self.model.N, probs=self.model.getTransitionProbabilities())
        self.plot_panel.update(self.model.getHistory(), self.model.N)
        self.canvas.draw_idle()
        self.status['text'] = f'Iteration: {self.model.iteration}    X = {self.model.getState()}'

    def on_n_change(self):
        try:
            raw = self.n_spin.get()
            val = int(raw)
        except Exception:
            # If parsing fails just return without changing
            return
        # Clamp to valid range
        if val < 1:
            val = 1
        # If the user typed a value larger than MAX_N, clamp it and notify the user
        original_val = val
        if val > MAX_N:
            val = MAX_N
            try:
                self.n_var.set(val)
                # Ensure numeric text in spinbox matches
                self.n_spin.delete(0, tk.END)
                self.n_spin.insert(0, str(val))
            except Exception:
                pass
            messagebox.showwarning("Too many balls!", f"Maximum allowed N is {MAX_N}. Setting N to {MAX_N}.")
            
        # Change N and reset iteration counter
        self.model.setN(val)
        self.model.iteration = 0
        
        # Refresh panels with the new N
        self.balls_panel.update(self.model.getState(), self.model.N)
        self.state_diagram.update(self.model.getState(), self.model.N, probs=self.model.getTransitionProbabilities())
        self.plot_panel.update(self.model.getHistory(), self.model.N)
        
        self.canvas.draw_idle()
        # Update status to show reset iteration
        try:
            self.status['text'] = f'Iteration: {self.model.iteration}    X = {getattr(self.model, "X", "?")}'
        except Exception:
            pass

    def on_speed_change(self, val=None):
        # Scale passes the current value as a string arg
        try:
            self.speed_ms = int(float(self.speed_var.get()))
        except Exception:
            # Fallback if value cannot be parsed
            return
        
        try:
            self.speed_value_label['text'] = f'{self.speed_ms} ms'
        except Exception:
            pass

    def _run_step(self):
        """Performs one simulation step and schedules the next if running"""
        if not self.running:
            # Simulation paused
            return

        X, probs = self.model.step()
        # Update panels and status
        self.balls_panel.update(X, self.model.N)
        self.state_diagram.update(X, self.model.N, probs=probs)
        self.plot_panel.update(self.model.getHistory(), self.model.N)
        self.status['text'] = f'Iteration: {self.model.iteration}    X = {self.model.getState()}'
        self.canvas.draw_idle()
        # Schedule next
        self.root.after(self.speed_ms, self._run_step)

    def on_timelapse(self):
        """Starts a "timelapsed" run in a background thread, collecting history and then plotting it."""
        try:
            M = int(self.timelapse_iters_var.get())
            if M <= 0:
                return
        except Exception:
            return

        # Disable UI buttons while running
        self.timelapse_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED)
        self.reset_btn.config(state=tk.DISABLED)

        # Background thread
        def worker():
            # Make a private model copy so the running simulation doesn't disturb the UI model state.
            # Prefer the model's initial X (first history element) so timelapse begins at the true start.
            try:
                hist_src = self.model.getHistory()
                if hist_src and len(hist_src) > 0:
                    start_X = hist_src[0]
                else:
                    start_X = self.model.getState()
            except Exception:
                start_X = getattr(self.model, 'X', 0)
            N = self.model.N
            from .ehrenfestModel import EhrenfestModel as _Model  # local import inside thread
            m = _Model(N=N, initial=start_X)
            # include the initial state as the first entry so the timelapse shows X_i at t=0
            hist = m.getHistory()
            for _ in range(M):
                x, _ = m.step()
                hist.append(x)

            # schedule plotting back on main thread
            def finish():
                try:
                    # show condensed time-series in the plot panel
                    # this will create a compressed visualization that represents all iterations
                    self.plot_panel.show_condensed_time(hist, N)
                    self.canvas.draw_idle()
                finally:
                    # re-enable buttons
                    try:
                        self.timelapse_btn.config(state=tk.NORMAL)
                        self.start_btn.config(state=tk.NORMAL)
                        self.pause_btn.config(state=tk.NORMAL)
                        self.reset_btn.config(state=tk.NORMAL)
                    except Exception:
                        pass
            self.root.after(0, finish)

        t = threading.Thread(target=worker, daemon=True)
        t.start()
