import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk  # type: ignore
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # type: ignore
import matplotlib.pyplot as plt # type: ignore
import numpy as np # type: ignore

from .ehrenfestModel import EhrenfestModel
from .ballsPanel import BallsPanel
from .stateDiagram import StateDiagram
from .plotPanel import PlotPanel
import threading

# Maximum allowed number of balls (for performance reasons)
MAX_N = 6000

class EhrenfestApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title('Ehrenfest Model Simulation')
        self.running = False
        self.model = EhrenfestModel(N=20)
        self.speed_ms = 200

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

        # Nudge the plot panel upwards slightly
        pos = self.ax_plot.get_position()
        offset = 0.08
        new_y0 = pos.y0 + offset
        # Ensure that we don't exceed the top of the figure...
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
        ctrl = ctk.CTkFrame(root, corner_radius=10)
        ctrl.pack(fill=tk.BOTH, padx=6, pady=6)

        # Buttons frame
        btn_frame = ctk.CTkFrame(ctrl, fg_color='transparent')
        btn_frame.pack(side=tk.LEFT, padx=4, pady=(12, 4))

        # Buttons
        self.start_btn = ctk.CTkButton(btn_frame, text='▶ Start', text_color ="black", 
                                       command=self.start, fg_color="#FFFFFF",
                                       border_width=1.5, border_color="#333434",
                                       corner_radius=8, width=100, height=50)
        self.start_btn.pack(side=tk.LEFT, padx=4)
        self._apply_hover_animation(self.start_btn, "#FFFFFF", "#A3A3A3")
        
        self.pause_btn = ctk.CTkButton(btn_frame, text='⏸ Pause', text_color ="black", 
                                       command=self.pause, fg_color="#FFFFFF",
                                       border_width=1.5, border_color="#333434", 
                                       corner_radius=8, width=100, height=50)
        self.pause_btn.pack(side=tk.LEFT, padx=4)
        self._apply_hover_animation(self.pause_btn, "#FFFFFF", "#A3A3A3")
        
        self.reset_btn = ctk.CTkButton(btn_frame, text='⟳ Reset', text_color ="black",
                                       command=self.reset, fg_color="#FFFFFF",
                                       border_width=1.5, border_color="#333434",
                                       corner_radius=8, width=100, height=50)
        self.reset_btn.pack(side=tk.LEFT, padx=4)
        self._apply_hover_animation(self.reset_btn, "#FFFFFF", "#A3A3A3")

        # N control frame
        n_frame = ctk.CTkFrame(ctrl, fg_color='transparent')
        n_frame.pack(side=tk.LEFT, padx=8, pady=4)

        ctk.CTkLabel(n_frame, text='Balls (N):', font=("Segoe UI", 11, "bold")).pack(padx=8, pady=(4,2))

        n_controls = ctk.CTkFrame(n_frame, fg_color='transparent')
        n_controls.pack(padx=8, pady=(2, 8))

        # Decrement button
        n_down_btn = ctk.CTkButton(n_controls, text='−', command=lambda: self.adjust_n(-1),
                           width=20, height=20, corner_radius=4, 
                           fg_color="#333434", hover_color="#242525")
        n_down_btn.pack(side=tk.LEFT, padx=2)

        # N entry box
        self.n_var = tk.StringVar(value=str(self.model.N))
        self.n_entry = ctk.CTkEntry(n_controls, textvariable=self.n_var, width=60, height=20,
                             justify="center", corner_radius=6)
        self.n_entry.pack(side=tk.LEFT, padx=2)
        self.n_entry.bind('<FocusOut>', lambda e: self.on_n_change())
        self.n_entry.bind('<Return>', lambda e: self.on_n_change())

        # Increment button
        n_up_btn = ctk.CTkButton(n_controls, text='+', command=lambda: self.adjust_n(1),
                         width=20, height=20, corner_radius=4,
                         fg_color="#333434", hover_color="#242525")
        n_up_btn.pack(side=tk.LEFT, padx=2)

        # Speed control frame
        speed_frame = ctk.CTkFrame(ctrl, corner_radius=8, height=40)
        speed_frame.pack(side=tk.LEFT, padx=8, pady=14, fill=tk.Y)
        
        speed_label_frame = ctk.CTkFrame(speed_frame, fg_color="transparent")
        speed_label_frame.pack(padx=8)

        ctk.CTkLabel(speed_label_frame, text="Speed", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        
        self.speed_slider = ctk.CTkSlider(speed_frame, from_=2000, to=1, width=220,
                                          command=self.on_speed_change, number_of_steps=1999,
                                          button_color = "#333434", button_hover_color="#242525")
        self.speed_slider.set(self.speed_ms)
        self.speed_slider.pack(padx=8, pady=(2, 8))

        # Status label
        self.status = ctk.CTkLabel(ctrl, text='Iteration: 0    X = 0', 
                                   font=("Segoe UI", 12, "bold"))
        self.status.pack(side=tk.RIGHT, padx=16, pady=8)

        # Timelapse frame
        timelapse_frame = ctk.CTkFrame(ctrl, corner_radius=8)
        timelapse_frame.pack(side=tk.RIGHT, padx=16, pady=8)
        
        ctk.CTkLabel(timelapse_frame, text="Timelapse", font=("Segoe UI", 11, "bold")).pack(padx=8, pady=(4, 2))
        
        timelapse_controls = ctk.CTkFrame(timelapse_frame, fg_color="transparent")
        timelapse_controls.pack(padx=8, pady=(2, 2))
        
        ctk.CTkLabel(timelapse_controls, text="Iterations:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 4))
        
        self.timelapse_iters_var = tk.StringVar(value="1000")
        self.timelapse_entry = ctk.CTkEntry(timelapse_controls, textvariable=self.timelapse_iters_var, 
                                            width=100, justify="center", corner_radius=6)
        self.timelapse_entry.pack(side=tk.LEFT, padx=4)
        
        # Timelapse run button
        self.timelapse_btn = ctk.CTkButton(timelapse_controls, text='🚀 Run', 
                                           text_color="black", command=self.on_timelapse,
                                           fg_color="#FFFFFF", border_width=1.5, 
                                           border_color="#333434", corner_radius=6, 
                                           width=80, height=28)
        self.timelapse_btn.pack(side=tk.LEFT, padx=4)
        self._apply_hover_animation(self.timelapse_btn, "#FFFFFF", "#A3A3A3")
    

        # Initial draw
        self.balls_panel.update(self.model.getState(), self.model.N)
        self.state_diagram.update(self.model.getState(), self.model.N, probs=self.model.getTransitionProbabilities())
        self.plot_panel.update(self.model.getHistory(), self.model.N)
        self.canvas.draw_idle()
        
    def _apply_hover_animation(self, widget, color_start, color_end):
        def hex_to_rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

        c1 = hex_to_rgb(color_start)
        c2 = hex_to_rgb(color_end)

        steps = 20
        step_size = 1.0 / steps
        delay = 10 # ms
        
        # Initialize animation state on the widget
        if not hasattr(widget, '_anim_current'):
            widget._anim_current = 0.0 
        if not hasattr(widget, '_anim_target'):
            widget._anim_target = 0.0
        if not hasattr(widget, '_anim_running'):
            widget._anim_running = False

        def update_color():
            t = widget._anim_current
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            color = rgb_to_hex((r, g, b))
            try:
                # Update BOTH fg_color and hover_color to prevent flickering
                widget.configure(fg_color=color, hover_color=color)
            except Exception:
                pass

        def animate():
            diff = widget._anim_target - widget._anim_current
            
            # If close enough to target, snap and stop
            if abs(diff) < step_size:
                widget._anim_current = widget._anim_target
                update_color()
                widget._anim_running = False
                return

            # Move towards target
            if diff > 0:
                widget._anim_current += step_size
                if widget._anim_current > widget._anim_target: 
                    widget._anim_current = widget._anim_target
            else:
                widget._anim_current -= step_size
                if widget._anim_current < widget._anim_target: 
                    widget._anim_current = widget._anim_target
            
            update_color()
            
            if widget._anim_running:
                widget.after(delay, animate)

        def start_anim(target):
            widget._anim_target = target
            if not widget._anim_running:
                widget._anim_running = True
                animate()

        # Set initial state
        widget.configure(fg_color=color_start, hover_color=color_start)

        widget.bind("<Enter>", lambda e: start_anim(1.0), add="+")
        widget.bind("<Leave>", lambda e: start_anim(0.0), add="+")

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
        self.status.configure(text= f'Iteration: {self.model.iteration}    X = {self.model.getState()}')

    def on_n_change(self):
        try:
            raw = self.n_var.get()
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
        
    def adjust_n(self, delta):
        try:
            current = int(self.n_var.get())
        except:
            current = self.model.N
    
        new_val = current + delta
        if new_val < 1:
            new_val = 1
        if new_val > MAX_N:
            new_val = MAX_N
    
        self.n_var.set(str(new_val))
        self.on_n_change()    

    def on_speed_change(self, val=None):
        # Scale passes the current value as a string arg
        try:
            self.speed_ms = int(float(self.speed_slider.get()))
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
        self.status.configure(text = f'Iteration: {self.model.iteration}    X = {self.model.getState()}')
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
        self.timelapse_btn.configure(state=tk.DISABLED)
        self.start_btn.configure(state=tk.DISABLED)
        self.pause_btn.configure(state=tk.DISABLED)
        self.reset_btn.configure(state=tk.DISABLED)

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
                        self.timelapse_btn.configure(state=tk.NORMAL)
                        self.start_btn.configure(state=tk.NORMAL)
                        self.pause_btn.configure(state=tk.NORMAL)
                        self.reset_btn.configure(state=tk.NORMAL)
                    except Exception:
                        pass
            self.root.after(0, finish)

        t = threading.Thread(target=worker, daemon=True)
        t.start()
