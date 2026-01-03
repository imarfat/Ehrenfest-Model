import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk  # type: ignore
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # type: ignore
import matplotlib.pyplot as plt # type: ignore
import numpy as np # type: ignore
import os
from PIL import Image, ImageOps # type: ignore

from .ehrenfestModel import EhrenfestModel
from .ballsPanel import BallsPanel
from .stateDiagram import StateDiagram
from .plotPanel import PlotPanel
import threading

# Maximum allowed number of balls (for UI & performance reasons)
MAX_N = 10000
# Maximum allowed timelapse iterations
MAX_TIMELAPSE_ITERS = 1000000

LANGUAGE_TEXT = {
    'title': {
        'en': 'Ehrenfest Model Simulation',
        'hr': 'Simulacija Ehrenfestovog modela',
    },
    'anim_switch': {
        'en': 'Animate ball transfers (N ≤ 200)',
        'hr': 'Animiraj prijenose kuglica (N ≤ 200)',
    },
    'start_button': {
        'en': '▶ Start',
        'hr': '▶ Pokreni',
    },
    'pause_button': {
        'en': '⏸ Pause',
        'hr': '⏸ Pauza',
    },
    'reset_button': {
        'en': '⟳ Reset',
        'hr': '⟳ Reset',
    },
    'balls_label': {
        'en': 'Balls (N):',
        'hr': 'Kuglice (N):',
    },
    'speed_label': {
        'en': 'Speed (non-animated)',
        'hr': 'Brzina (bez animacije)',
    },
    'timelapse_heading': {
        'en': 'Timelapse',
        'hr': 'Ubrzani prikaz',
    },
    'iterations_label': {
        'en': 'Iterations:',
        'hr': 'Iteracije:',
    },
    'timelapse_run': {
        'en': '🚀 Run',
        'hr': '🚀 Pokreni',
    },
    'paused_info': {
        'en': '⏸ Simulation paused — press Start to continue',
        'hr': '⏸ Simulacija pauzirana — pritisnite Pokreni za nastavak',
    },
    'too_many_balls_title': {
        'en': 'Too many balls!',
        'hr': 'Previše kuglica!',
    },
    'too_many_balls_message': {
        'en': 'Maximum allowed N is {max_n}. Setting N to {max_n}.',
        'hr': 'Najveći dopušteni N je {max_n}. Postavljam N na {max_n}.',
    },
    'too_many_iterations_title': {
        'en': 'Too many iterations',
        'hr': 'Previše iteracija',
    },
    'too_many_iterations_message': {
        'en': 'Maximum timelapse iterations is {max_iters:,}.',
        'hr': 'Maksimalan broj iteracija ubrzanog prikaza je {max_iters:,}.',
    },
    'iteration_label': {
        'en': 'Iteration',
        'hr': 'Iteracija',
    },
    'state_label': {
        'en': 'X',
        'hr': 'X',
    },
    'balls_panel_title': {
        'en': 'The Ehrenfest Model',
        'hr': 'Ehrenfestov difuzijski model',
    },
    'balls_panel_subtitle': {
        'en': 'A stochastic simulation of balls moving between two boxes.',
        'hr': 'Simulacija nasumičnog prijenosa kuglica između dviju kutija.',
    },
    'balls_panel_subsubtitle': {
        'en': '$X_i$ ~ number of balls in Box A at iteration $i$',
        'hr': '$X_i$ ~ broj kuglica u kutiji A tijekom $i$-te iteracije',
    },
    'box_a_label': {
        'en': 'Box A',
        'hr': 'Kutija A',
    },
    'box_b_label': {
        'en': 'Box B',
        'hr': 'Kutija B',
    },
    'state_diagram_title': {
        'en': 'State Diagram / Markov Chain',
        'hr': 'Dijagram stanja / Markovljev lanac',
    },
    'state_diagram_subtitle': {
        'en': 'Simplified 3-state view. We label the states using an integer\n$n \\in \\{0, ..., N\\}$ corresponding to the number of balls in Box A.',
        'hr': 'Pojednostavljeni prikaz s 3 stanja. Stanja označavamo cijelim \nbrojem $n \\in \\{0, ..., N\\}$ koji predstavlja broj kuglica u kutiji A.',
    },
    'plot_title_realtime': {
        'en': 'Real Time Trajectory of $X_i$',
        'hr': 'Trajektorija $X_i$ u stvarnom vremenu',
    },
    'plot_title_condensed': {
        'en': 'Timelapsed Trajectory of $X_i$',
        'hr': 'Ubrzana trajektorija $X_i$',
    },
    'plot_x_label': {
        'en': 'Iteration',
        'hr': 'Iteracija',
    },
    'plot_y_label': {
        'en': '$X_i$ (balls in A)',
        'hr': '$X_i$ (kuglice u A)',
    },
    'plot_mean_label': {
        'en': 'Mean (N/2 = {value:.1f})',
        'hr': 'Srednja vrijednost (N/2 = {value:.1f})',
    },
    'plot_trajectory_label': {
        'en': 'Trajectory',
        'hr': 'Trajektorija',
    },
    'plot_current_label': {
        'en': 'Current value',
        'hr': 'Trenutna vrijednost',
    },
}

class EhrenfestApp:
    
    def __init__(self, root):
        self.root = root
        self.language = 'en'
        self._info_message_key = None
        self._info_message_kwargs = {}
        self._translate_icon = None
        self.root.title(self._t('title'))
        self.running = False
        self.model = EhrenfestModel(N=20)
        self.speed_ms = 500
        self._waiting_for_animation = False
        self._animated_widgets = []
        self._pending_panel_update = None
        self._grain_base_image = self._create_grain_image((512, 512))
        self._anim_ctrl_bg_label = None
        self._anim_ctrl_bg_image = None

        self.fig = plt.Figure(figsize=(10, 6), dpi=100)
        
        # Subtle grainy background texture
        try:
            rng = np.random.RandomState(0)
            noise = rng.normal(loc=0.0, scale=1.0, size=(256, 256))
            noise = (noise - noise.min()) / (noise.max() - noise.min())
            noise = 0.9 + 0.06 * (noise - 0.5)
            ax_bg = self.fig.add_axes([0, 0, 1, 1], zorder=0)
            ax_bg.imshow(
                noise, 
                cmap='Greys', 
                aspect='auto', 
                interpolation='bilinear', 
                extent=[0, 1, 0, 1], 
                alpha=0.1
            )
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
        self.balls_panel = BallsPanel(self.ax_balls, N=self.model.N, scheduler=self.root)
        self.balls_panel.set_animation_complete_callback(self._on_ball_animation_complete)
        self.state_diagram = StateDiagram(self.ax_state, N=self.model.N)
        self.plot_panel = PlotPanel(self.ax_plot, N=self.model.N)

        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        canvas_widget = self.canvas.get_tk_widget()
        try:
            canvas_widget.configure(highlightthickness=0, bd=0)
        except Exception:
            pass
        canvas_widget.pack(fill=tk.BOTH, expand=1)

        anim_ctrl = ctk.CTkFrame(root, fg_color='transparent', bg_color='transparent')
        anim_ctrl.pack(fill=tk.X, padx=10, pady=0)
        self._setup_anim_ctrl_background(anim_ctrl)
        self.anim_var = tk.BooleanVar(value=False)
        self.anim_switch = ctk.CTkSwitch(
            anim_ctrl,
            text=self._t('anim_switch'),
            variable=self.anim_var,
            command=self._on_animation_toggle,
            progress_color="#1f4d7a",
        )
        self.anim_switch.pack(side=tk.LEFT, padx=4, pady=8)
        self._refresh_animation_toggle_state()
        
        # Status message label
        self.info_label = ctk.CTkLabel(
            anim_ctrl,
            text="",
            font=("Segoe UI", 10),
            text_color="#555555",
            anchor="w",
            justify="left",
        )
        self.info_label.pack(side=tk.LEFT, padx=12, expand=True, fill=tk.X)
        self._set_info_message()

        self._translate_icon = self._load_translate_icon()
        self.translate_btn = ctk.CTkButton(
            anim_ctrl,
            text="",
            image=self._translate_icon,
            command=self.toggle_language,
            width=20,
            height=36,
            fg_color="transparent",
            hover=False,
            border_width=0,
            corner_radius=18,
            text_color="#111111",
            compound=tk.LEFT,
        )
        self.translate_btn.pack(side=tk.RIGHT, padx=(4, 0), pady=6)

        # Controls frame
        ctrl = ctk.CTkFrame(root, corner_radius=0)
        ctrl.pack(side=tk.BOTTOM, fill=tk.X, expand=False, padx=0, pady=0)
        try:
            top_border = tk.Frame(ctrl, height=1, background="#000000", borderwidth=0, highlightthickness=0)
            top_border.pack(fill=tk.X, side=tk.TOP)
        except Exception:
            pass

        # Buttons frame
        btn_frame = ctk.CTkFrame(ctrl, fg_color='transparent')
        btn_frame.pack(side=tk.LEFT, padx=4, pady=(12, 4))

        # Buttons
        self.start_btn = ctk.CTkButton(btn_frame, text=self._t('start_button'), text_color ="black", 
                                       command=self.start, fg_color="#FFFFFF",
                                       border_width=1.5, border_color="#333434",
                                       corner_radius=8, width=100, height=50)
        self.start_btn.pack(side=tk.LEFT, padx=4)
        self._apply_hover_animation(self.start_btn, "#FFFFFF", "#A3A3A3")
        
        self.pause_btn = ctk.CTkButton(btn_frame, text=self._t('pause_button'), text_color ="black", 
                                       command=self.pause, fg_color="#FFFFFF",
                                       border_width=1.5, border_color="#333434", 
                                       corner_radius=8, width=100, height=50)
        self.pause_btn.pack(side=tk.LEFT, padx=4)
        self._apply_hover_animation(self.pause_btn, "#FFFFFF", "#A3A3A3")
        
        self.reset_btn = ctk.CTkButton(btn_frame, text=self._t('reset_button'), text_color ="black",
                                       command=self.reset, fg_color="#FFFFFF",
                                       border_width=1.5, border_color="#333434",
                                       corner_radius=8, width=100, height=50)
        self.reset_btn.pack(side=tk.LEFT, padx=4)
        self._apply_hover_animation(self.reset_btn, "#FFFFFF", "#A3A3A3")

        # Controls button
        self.advanced_visible = False
        adv_wrapper = ctk.CTkFrame(btn_frame, fg_color='transparent', width=40, height=50)
        adv_wrapper.pack_propagate(False)
        adv_wrapper.pack(side=tk.LEFT, padx=4)
        self.advanced_btn = ctk.CTkButton(
            adv_wrapper,
            text='〉',
            text_color="black",
            command=self.toggle_advanced_controls,
            fg_color="transparent",
            border_width=0,
            corner_radius=6,
            width=40,
            height=50,
            font=("Segoe UI", 26, "bold"),
            hover=False,
        )
        self.advanced_btn.place(relx=0.5, rely=0.0, y=-2, anchor='n')

        # N control frame (initially hidden)
        self.n_frame = ctk.CTkFrame(ctrl, fg_color='transparent')

        self.n_label = ctk.CTkLabel(
            self.n_frame, 
            text=self._t('balls_label'), 
            font=("Segoe UI", 11, "bold")
        )
        self.n_label.pack(padx=8, pady=(8,0))

        n_controls = ctk.CTkFrame(self.n_frame, fg_color='transparent')
        n_controls.pack(padx=8, pady=(0, 8))

        # Decrement button
        n_down_btn = ctk.CTkButton(
            n_controls,
            text='−',
            command=lambda: self.adjust_n(-1),
            width=24,
            height=24,
            corner_radius=12,
            fg_color="transparent",
            hover_color="#e5e7eb",
            text_color="#111111",
            border_width=0
        )
        n_down_btn.pack(side=tk.LEFT)

        # N entry box
        self.n_var = tk.StringVar(value=str(self.model.N))
        self.n_entry = ctk.CTkEntry(
            n_controls, 
            textvariable=self.n_var, 
            width=60, 
            height=20,
            justify="center", 
            corner_radius=6
        )
        self.n_entry.pack(side=tk.LEFT, padx=2)
        self.n_entry.bind('<FocusOut>', lambda e: self.on_n_change())
        self.n_entry.bind('<Return>', lambda e: self.on_n_change())
        self.n_entry.bind('<MouseWheel>', self._on_n_mousewheel)

        # Increment button
        n_up_btn = ctk.CTkButton(
            n_controls,
            text='+',
            command=lambda: self.adjust_n(1),
            width=24,
            height=24,
            corner_radius=12,
            fg_color="transparent",
            hover_color="#e5e7eb",
            text_color="#111111",
            border_width=0
        )
        n_up_btn.pack(side=tk.LEFT)

        # Speed control frame (initially hidden)
        self.speed_frame = ctk.CTkFrame(ctrl, corner_radius=8, height=40, fg_color="transparent")
        
        speed_label_frame = ctk.CTkFrame(self.speed_frame, fg_color="transparent")
        speed_label_frame.pack(padx=8)

        self.speed_label = ctk.CTkLabel(
            speed_label_frame, 
            text=self._t('speed_label'), 
            font=("Segoe UI", 11, "bold")
        )
        self.speed_label.pack(side=tk.LEFT)
        
        self.speed_slider = ctk.CTkSlider(
            self.speed_frame, 
            from_=1000, 
            to=1, 
            width=220,
            command=self.on_speed_change, 
            number_of_steps=1999,
            button_color = "#333434", 
            button_hover_color="#242525"
        )
        self.speed_slider.set(self.speed_ms)
        self.speed_slider.pack(padx=8, pady=(2, 8))

        # Status label
        self.status = ctk.CTkLabel(
            ctrl, 
            text="", 
            font=("Segoe UI", 12, "bold"),
            width=120, anchor="center"
        )
        self.status.pack(side=tk.RIGHT, padx=16, pady=8)

        # Timelapse frame
        timelapse_frame = ctk.CTkFrame(ctrl, corner_radius=8)
        timelapse_frame.pack(side=tk.RIGHT, padx=16, pady=8)
        
        self.timelapse_label = ctk.CTkLabel(
            timelapse_frame, 
            text=self._t('timelapse_heading'), 
            font=("Segoe UI", 11, "bold")
        )
        self.timelapse_label.pack(padx=8, pady=(4, 2))
        
        timelapse_controls = ctk.CTkFrame(timelapse_frame, fg_color="transparent")
        timelapse_controls.pack(padx=8, pady=(2, 2))
        
        self.iterations_label = ctk.CTkLabel(
            timelapse_controls, 
            text=self._t('iterations_label'), 
            font=("Segoe UI", 9)
        )
        self.iterations_label.pack(side=tk.LEFT, padx=(0, 4))
        
        self.timelapse_iters_var = tk.StringVar(value="1000")
        self.timelapse_entry = ctk.CTkEntry(
            timelapse_controls, 
            textvariable=self.timelapse_iters_var, 
            width=100, 
            justify="center", 
            corner_radius=6
        )
        self.timelapse_entry.pack(side=tk.LEFT, padx=4)
        
        # Timelapse run button
        self.timelapse_btn = ctk.CTkButton(timelapse_controls, text=self._t('timelapse_run'), 
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
        self._update_status_label()
        self.canvas.draw_idle()
        
        # Keyboard shortcuts
        self._bind_keyboard_shortcuts()
        self._apply_language()
    
    def _bind_keyboard_shortcuts(self):
        self.root.bind('<space>', self._on_space_key)
        self.root.bind('<r>', self._on_reset_key)
        self.root.bind('<R>', self._on_reset_key)
        self.root.bind('<Up>', self._on_up_key)
        self.root.bind('<Down>', self._on_down_key)
    
    def _on_space_key(self, event=None):
        """Toggle start/pause on Space"""
        # Ignore if focus is in an entry widget
        if isinstance(self.root.focus_get(), (tk.Entry, ctk.CTkEntry)):
            return
        if self.running:
            self.pause()
        else:
            self.start()
        return 'break'
    
    def _on_reset_key(self, event=None):
        """Reset simulation on R"""
        # Ignore if focus is in an entry widget
        if isinstance(self.root.focus_get(), (tk.Entry, ctk.CTkEntry)):
            return
        self.reset()
        return 'break'
    
    def _on_up_key(self, event=None):
        """Increase N on Up arrow"""
        # Ignore if focus is in an entry widget
        if isinstance(self.root.focus_get(), (tk.Entry, ctk.CTkEntry)):
            return
        self.adjust_n(1)
        return 'break'
    
    def _on_down_key(self, event=None):
        """Decrease N on Down arrow"""
        # Ignore if focus is in an entry widget
        if isinstance(self.root.focus_get(), (tk.Entry, ctk.CTkEntry)):
            return
        self.adjust_n(-1)
        return 'break'
    
    def _on_n_mousewheel(self, event):
        if event.delta > 0:
            self.adjust_n(1) 
        elif event.delta < 0:
            self.adjust_n(-1) 
        return "break"         
        
    def _apply_hover_animation(self, widget, color_start, color_end):
        def hex_to_rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

        c1 = hex_to_rgb(color_start)
        c2 = hex_to_rgb(color_end)
        widget._anim_colors = (color_start, color_end)
        widget._hover_anim_enabled = True
        widget._is_hovered = False

        steps = 20
        step_size = 1.0 / steps
        delay = 10 # ms
        
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
            if not widget._hover_anim_enabled:
                widget._anim_running = False
                return
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
            if not widget._hover_anim_enabled:
                self._apply_hover_colors(widget)
                return
            widget._anim_target = target
            if not widget._anim_running:
                widget._anim_running = True
                animate()

        # Set initial state
        self._apply_hover_colors(widget)

        def _on_enter(_event):
            widget._is_hovered = True
            if widget._hover_anim_enabled:
                start_anim(1.0)
            else:
                self._apply_hover_colors(widget)

        def _on_leave(_event):
            widget._is_hovered = False
            if widget._hover_anim_enabled:
                start_anim(0.0)
            else:
                self._apply_hover_colors(widget)

        widget.bind("<Enter>", _on_enter, add="+")
        widget.bind("<Leave>", _on_leave, add="+")
        self._animated_widgets.append(widget)

    def _apply_hover_colors(self, widget):
        colors = getattr(widget, '_anim_colors', None)
        if not colors:
            return
        color_start, color_end = colors
        if widget._hover_anim_enabled:
            widget.configure(fg_color=color_start, hover_color=color_start)
        else:
            if getattr(widget, '_is_hovered', False):
                widget.configure(fg_color=color_end, hover_color=color_end)
            else:
                widget.configure(fg_color=color_start, hover_color=color_end)

    def _set_hover_animation_enabled(self, enabled):
        for widget in self._animated_widgets:
            colors = getattr(widget, '_anim_colors', None)
            if not colors:
                continue
            widget._hover_anim_enabled = enabled
            widget._anim_target = 0.0
            widget._anim_current = 0.0
            widget._anim_running = False
            self._apply_hover_colors(widget)

    def _refresh_animation_toggle_state(self):
        if not hasattr(self, 'anim_switch'):
            return
        if self.model.N > 200:
            was_on = self.anim_var.get()
            try:
                self.anim_switch.configure(state=tk.DISABLED)
            except Exception:
                pass
            if self.anim_var.get():
                self.anim_var.set(False)
            self.balls_panel.set_animation_enabled(False)
            if was_on:
                self._resume_after_cancelled_animation()
            return
        else:
            try:
                self.anim_switch.configure(state=tk.NORMAL)
            except Exception:
                pass
        self.balls_panel.set_animation_enabled(bool(self.anim_var.get()))

    def _on_animation_toggle(self):
        self.balls_panel.set_animation_enabled(bool(self.anim_var.get()))
        if not self.anim_var.get():
            self._resume_after_cancelled_animation()

    def _on_ball_animation_complete(self):
        self._waiting_for_animation = False
        
        if self._pending_panel_update is not None:
            data = self._pending_panel_update
            self._pending_panel_update = None
            self.state_diagram.update(data['X'], data['N'], probs=data['probs'])
            self.plot_panel.update(data['history'], data['N'])
            self.canvas.draw_idle()
        
        if self.running:
            self.root.after(self.speed_ms, self._run_step)

    def _resume_after_cancelled_animation(self):
        if self._waiting_for_animation and self.running:
            self._waiting_for_animation = False
            self.root.after(self.speed_ms, self._run_step)

    def _show_advanced_controls(self):
        """Pack and show the N controls and speed slider."""
        if self.advanced_visible:
            return
        
        try:
            self.n_frame.pack(side=tk.LEFT, padx=8, pady=4)
            self.speed_frame.pack(side=tk.LEFT, padx=8, pady=14, fill=tk.Y)
        except Exception:
            pass
        self.advanced_visible = True
        
        try:
            self.advanced_btn.configure(text='〈')
        except Exception:
            pass

    def _hide_advanced_controls(self):
        """Hide the N controls and speed slider."""
        if not self.advanced_visible:
            return
        try:
            self.n_frame.pack_forget()
            self.speed_frame.pack_forget()
        except Exception:
            pass
        self.advanced_visible = False
        
        try:
            self.advanced_btn.configure(text='〉')
        except Exception:
            pass

    def toggle_advanced_controls(self):
        """Toggle visibility of advanced controls (N and speed)."""
        if self.advanced_visible:
            self._hide_advanced_controls()
        else:
            self._show_advanced_controls()

    def toggle_language(self):
        """Toggle application language between English and Croatian."""
        new_lang = 'hr' if self.language == 'en' else 'en'
        self._set_language(new_lang)

    def start(self):
        if not self.running:
            self.running = True
            self._set_hover_animation_enabled(False)
            self._waiting_for_animation = False
            self._set_info_message()
            self._run_step()

    def pause(self):
        if self.running:
            self.running = False
            self._set_hover_animation_enabled(True)
            self._waiting_for_animation = False
            self._set_info_message('paused_info')

    def reset(self):
        self.balls_panel.cancel_animation()
        self._resume_after_cancelled_animation()
        val = self._read_and_clamp_n()
        
        if val is None:
            return
        
        self._set_info_message()
        # Reset model and panels
        self.model.reset(N=val)
        self.balls_panel.update(self.model.getState(), self.model.N)
        self.state_diagram.update(self.model.getState(), self.model.N, probs=self.model.getTransitionProbabilities())
        self.plot_panel.update(self.model.getHistory(), self.model.N)
        self.canvas.draw_idle()
        self._update_status_label()
        self._refresh_animation_toggle_state()

    def _read_and_clamp_n(self, show_warning=True):
        """Parse the N entry, clamp to [1, MAX_N], update the UI, and return the int."""
        try:
            raw = self.n_var.get()
            val = int(raw)
        except Exception:
            return None

        original_val = val
        if val < 1:
            val = 1
        if val > MAX_N:
            val = MAX_N

        if val != original_val:
            try:
                self.n_var.set(str(val))
                self.n_entry.delete(0, tk.END)
                self.n_entry.insert(0, str(val))
            except Exception:
                pass
            if show_warning and original_val > MAX_N:
                self._show_warning('too_many_balls_title', 'too_many_balls_message', max_n=MAX_N)
        return val

    def on_n_change(self):
        self.balls_panel.cancel_animation()
        self._resume_after_cancelled_animation()
        val = self._read_and_clamp_n()
        if val is None:
            return
        
        self.model.setN(val)
        self.model.iteration = 0
        
        # Refresh panels with the new N
        self.balls_panel.update(self.model.getState(), self.model.N)
        self.state_diagram.update(self.model.getState(), self.model.N, probs=self.model.getTransitionProbabilities())
        self.plot_panel.update(self.model.getHistory(), self.model.N)
        
        self.canvas.draw_idle()
        
        self._update_status_label()
        self._refresh_animation_toggle_state()
        
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
            return

    def _run_step(self):
        """Performs one simulation step and schedules the next if running"""
        if not self.running:
            # Simulation paused
            return

        X, probs = self.model.step()
        
        animation_active = self.balls_panel.update(X, self.model.N)
        
        # Lazy panel updates: defer StateDiagram and PlotPanel during animation
        if animation_active:
            # Store pending update data
            self._pending_panel_update = {
                'X': X,
                'N': self.model.N,
                'probs': probs,
                'history': self.model.getHistory().copy(),
                'iteration': self.model.iteration,
            }
            self._waiting_for_animation = True
        else:
            # No animation - update panels
            self.state_diagram.update(X, self.model.N, probs=probs)
            self.plot_panel.update(self.model.getHistory(), self.model.N)
            self._waiting_for_animation = False
            self.root.after(self.speed_ms, self._run_step)
        
        self._update_status_label()
        self.canvas.draw_idle()

    def _set_language(self, lang):
        if lang == self.language or lang not in ('en', 'hr'):
            return
        self.language = lang
        self._apply_language()

    def _apply_language(self):
        try:
            self.root.title(self._t('title'))
        except Exception:
            pass

        widget_map = [
            (getattr(self, 'anim_switch', None), 'anim_switch'),
            (getattr(self, 'start_btn', None), 'start_button'),
            (getattr(self, 'pause_btn', None), 'pause_button'),
            (getattr(self, 'reset_btn', None), 'reset_button'),
            (getattr(self, 'n_label', None), 'balls_label'),
            (getattr(self, 'speed_label', None), 'speed_label'),
            (getattr(self, 'timelapse_label', None), 'timelapse_heading'),
            (getattr(self, 'iterations_label', None), 'iterations_label'),
            (getattr(self, 'timelapse_btn', None), 'timelapse_run'),
        ]

        for widget, key in widget_map:
            if widget is None:
                continue
            try:
                widget.configure(text=self._t(key))
            except Exception:
                pass

        if self._info_message_key:
            self._set_info_message(self._info_message_key, **self._info_message_kwargs)
        else:
            self._set_info_message()
        self._apply_panel_language()
        self._update_status_label()

    def _apply_panel_language(self):
        if hasattr(self, 'balls_panel') and self.balls_panel is not None:
            self.balls_panel.set_texts({
                'title': self._t('balls_panel_title'),
                'subtitle': self._t('balls_panel_subtitle'),
                'subsubtitle': self._t('balls_panel_subsubtitle'),
                'box_a': self._t('box_a_label'),
                'box_b': self._t('box_b_label'),
            })
        if hasattr(self, 'state_diagram') and self.state_diagram is not None:
            self.state_diagram.set_texts({
                'title': self._t('state_diagram_title'),
                'subtitle': self._t('state_diagram_subtitle'),
            })
        if hasattr(self, 'plot_panel') and self.plot_panel is not None:
            self.plot_panel.set_texts({
                'title_realtime': self._t('plot_title_realtime'),
                'title_condensed': self._t('plot_title_condensed'),
                'x_label': self._t('plot_x_label'),
                'y_label': self._t('plot_y_label'),
                'mean_label': self._t('plot_mean_label'),
                'trajectory_label': self._t('plot_trajectory_label'),
                'current_label': self._t('plot_current_label'),
            })

    def _create_grain_image(self, size):
        try:
            rng = np.random.RandomState(0)
            noise = rng.normal(loc=0.0, scale=1.0, size=size)
            noise = (noise - noise.min()) / (noise.max() - noise.min())
            noise = 0.9 + 0.06 * (noise - 0.5)
            array = (noise * 255).astype(np.uint8)
            return Image.fromarray(array, mode='L').convert('RGB')
        except Exception:
            return None

    def _setup_anim_ctrl_background(self, frame):
        if self._grain_base_image is None:
            return
        self._anim_ctrl_bg_label = ctk.CTkLabel(frame, text="", image=None, fg_color='transparent')
        self._anim_ctrl_bg_label.place(relwidth=1, relheight=1)
        self._anim_ctrl_bg_label.lower()
        frame.bind("<Configure>", self._on_anim_ctrl_resize)

    def _on_anim_ctrl_resize(self, event):
        if self._grain_base_image is None or self._anim_ctrl_bg_label is None:
            return
        width = max(getattr(event, 'width', self._anim_ctrl_bg_label.winfo_width()), 1)
        height = max(getattr(event, 'height', self._anim_ctrl_bg_label.winfo_height()), 1)
        self._update_anim_ctrl_background(width, height)

    def _update_anim_ctrl_background(self, width, height):
        if self._grain_base_image is None or self._anim_ctrl_bg_label is None:
            return
        try:
            resized = self._grain_base_image.resize((width, height), Image.LANCZOS)
        except Exception:
            resized = self._grain_base_image.resize((width, height))
        self._anim_ctrl_bg_image = ctk.CTkImage(light_image=resized, dark_image=resized, size=(width, height))
        self._anim_ctrl_bg_label.configure(image=self._anim_ctrl_bg_image)
        self._anim_ctrl_bg_label.image = self._anim_ctrl_bg_image

    def _resource_path(self, relative_path):
        base_dir = os.path.dirname(__file__)
        return os.path.join(base_dir, relative_path)

    def _load_translate_icon(self):
        try:
            icon_path = self._resource_path(os.path.join('assets', 'translate.png'))
            if not os.path.exists(icon_path):
                return None
            target_size = (24, 24)
            image = Image.open(icon_path).convert('RGBA')
            if image.size != target_size:
                try:
                    image = image.resize(target_size, Image.LANCZOS)
                except Exception:
                    image = image.resize(target_size)

            return ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=target_size,
            )
        except Exception:
            return None

    def _t(self, key, **kwargs):
        template = LANGUAGE_TEXT.get(key, {}).get(self.language)
        if template is None:
            template = LANGUAGE_TEXT.get(key, {}).get('en', '')
        try:
            return template.format(**kwargs)
        except Exception:
            return template

    def _set_info_message(self, key=None, **kwargs):
        if not hasattr(self, 'info_label'):
            return
        self._info_message_key = key
        self._info_message_kwargs = kwargs if key else {}
        if not key:
            text = ""
        else:
            text = self._t(key, **kwargs)
        try:
            self.info_label.configure(text=text)
        except Exception:
            pass

    def _update_status_label(self):
        if not hasattr(self, 'status'):
            return
        iteration = getattr(self.model, 'iteration', 0)
        try:
            state = self.model.getState()
        except Exception:
            state = getattr(self.model, 'X', '?')
        text = f"{self._t('iteration_label')}: {iteration}\n{self._t('state_label')} = {state}"
        try:
            self.status.configure(text=text)
        except Exception:
            pass

    def _show_warning(self, title_key, message_key, **kwargs):
        title = self._t(title_key, **kwargs)
        message = self._t(message_key, **kwargs)
        try:
            messagebox.showwarning(title, message)
        except Exception:
            pass

    def on_timelapse(self):
        """Starts a "timelapsed" run in a background thread, collecting history and then plotting it."""
        if self.running:
            self.pause()
        
        self.balls_panel.cancel_animation()
        self._waiting_for_animation = False
        self._pending_panel_update = None
        
        try:
            M = int(self.timelapse_iters_var.get())
            if M <= 0:
                return
        except Exception:
            return

        if M > MAX_TIMELAPSE_ITERS:
            M = MAX_TIMELAPSE_ITERS
            try:
                self.timelapse_iters_var.set(str(M))
                self.timelapse_entry.delete(0, tk.END)
                self.timelapse_entry.insert(0, str(M))
            except Exception:
                pass
            self._show_warning('too_many_iterations_title', 'too_many_iterations_message', max_iters=MAX_TIMELAPSE_ITERS)

        # Disable UI buttons while running
        self.timelapse_btn.configure(state=tk.DISABLED)
        self.start_btn.configure(state=tk.DISABLED)
        self.pause_btn.configure(state=tk.DISABLED)
        self.reset_btn.configure(state=tk.DISABLED)

        # Background thread
        def worker():
            # Make a private model copy so the running simulation doesn't disturb the UI model state.
            # Get the model's initial X_i so timelapse begins at the true start.
            try:
                hist_src = self.model.getHistory()
                if hist_src and len(hist_src) > 0:
                    start_X = hist_src[0]
                else:
                    start_X = self.model.getState()
            except Exception:
                start_X = getattr(self.model, 'X', 0)
            N = self.model.N
            
            from .ehrenfestModel import EhrenfestModel as _Model  
            m = _Model(N=N, initial=start_X)
            
            hist = m.getHistory()
            for _ in range(M):
                x, _ = m.step()
                hist.append(x)

            # Schedule plotting back on main thread
            def finish():
                try:
                    self.plot_panel.show_condensed_time(hist, N)
                    self.canvas.draw_idle()
                finally:
                    # Re-enable buttons
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
