import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk  # type: ignore
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import numpy as np  # type: ignore
import os
import threading

from .ehrenfestModel import EhrenfestModel
from .ballsPanel import BallsPanel
from .stateDiagram import StateDiagram
from .plotPanel import PlotPanel
from .translator import Translator
from .uiHelpers import GrainBackground, HoverAnimationManager, create_grain_image, load_translate_icon
from .simulationController import SimulationController

# Maximum allowed number of balls (for UI & performance reasons)
MAX_N = 10000
# Maximum allowed timelapse iterations
MAX_TIMELAPSE_ITERS = 1000000

class EhrenfestApp:
    
    def __init__(self, root):
        self.root = root
        self.translator = Translator(language='en')
        self.language = self.translator.language
        self._info_message_key = None
        self._info_message_kwargs = {}
        self.root.title(self._t('title'))
        self.model = EhrenfestModel(N=20)
        self.speed_ms = 500
        self.hover_animator = HoverAnimationManager()
        self._grain_base_image = create_grain_image((512, 512))
        self.grain_background = GrainBackground(self._grain_base_image)
        self._translate_icon = None

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
        canvas_widget.pack(fill=tk.BOTH, expand=1, pady=(10, 0))
        
        # Enlarged plot overlay state
        self._enlarged_overlay = None
        self._enlarged_fig = None
        self._enlarged_canvas = None
        self._enlarged_ax = None
        self._enlarged_hint_label = None
        
        # Register click handler on main canvas for plot enlargement
        self.canvas.mpl_connect('button_press_event', self._on_canvas_click)

        self.controller = SimulationController(
            scheduler=self.root,
            model=self.model,
            animate_step=lambda X, N: self.balls_panel.update(X, N),
            apply_panel_updates=self._apply_panel_updates,
            redraw_canvas=self.canvas.draw_idle,
            update_status=self._update_status_label,
            speed_ms=self.speed_ms,
        )

        anim_ctrl = ctk.CTkFrame(root, fg_color='transparent', bg_color='transparent')
        anim_ctrl.pack(fill=tk.X, padx=10, pady=0)
        self.grain_background.attach(anim_ctrl)
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

        self._translate_icon = load_translate_icon(os.path.dirname(__file__))
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
        self.hover_animator.apply(self.start_btn, "#FFFFFF", "#A3A3A3")
        
        self.pause_btn = ctk.CTkButton(btn_frame, text=self._t('pause_button'), text_color ="black", 
                                       command=self.pause, fg_color="#FFFFFF",
                                       border_width=1.5, border_color="#333434", 
                                       corner_radius=8, width=100, height=50)
        self.pause_btn.pack(side=tk.LEFT, padx=4)
        self.hover_animator.apply(self.pause_btn, "#FFFFFF", "#A3A3A3")
        
        self.reset_btn = ctk.CTkButton(btn_frame, text=self._t('reset_button'), text_color ="black",
                                       command=self.reset, fg_color="#FFFFFF",
                                       border_width=1.5, border_color="#333434",
                                       corner_radius=8, width=100, height=50)
        self.reset_btn.pack(side=tk.LEFT, padx=4)
        self.hover_animator.apply(self.reset_btn, "#FFFFFF", "#A3A3A3")

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
            text='-',
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
        self.hover_animator.apply(self.timelapse_btn, "#FFFFFF", "#A3A3A3")
        
        # Superpose checkbox
        self.superpose_var = tk.BooleanVar(value=False)
        self.superpose_check = ctk.CTkCheckBox(
            timelapse_controls,
            text=self._t('superpose_checkbox'),
            variable=self.superpose_var,
            font=("Segoe UI", 9),
            width=80,
            height=24,
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=4,
            border_width=1,
            fg_color="#1f4d7a",
            hover_color="#2a6a9e",
        )
        self.superpose_check.pack(side=tk.LEFT, padx=(8, 4))
    

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
        self.root.bind('<Escape>', self._on_escape_key)
    
    def _on_space_key(self, event=None):
        """Toggle start/pause on Space"""
        # Ignore if focus is in an entry widget
        if isinstance(self.root.focus_get(), (tk.Entry, ctk.CTkEntry)):
            return
        if self.controller.is_running:
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
    
    def _on_escape_key(self, event=None):
        """Close enlarged overlay on Escape"""
        if self._enlarged_overlay is not None:
            self._close_enlarged_overlay()
            return 'break'
    
    def _on_canvas_click(self, event):
        """Handle click on the main canvas to check if plot was clicked"""
        if event.inaxes == self.ax_plot:
            self._show_enlarged_overlay()
    
    def _show_enlarged_overlay(self):
        """Show the enlarged plot overlay"""
        if self._enlarged_overlay is not None:
            return  # Already showing
        
        # Create overlay frame covering the canvas area
        canvas_widget = self.canvas.get_tk_widget()
        self._enlarged_overlay = ctk.CTkFrame(
            self.root,
            fg_color='#1a1a2e',
            corner_radius=12,
            border_width=2,
            border_color='#333'
        )
        self._enlarged_overlay.place(
            in_=canvas_widget,
            relx=0.02, rely=0.02,
            relwidth=0.96, relheight=0.96
        )
        
        # Create enlarged figure
        self._enlarged_fig = plt.Figure(figsize=(12, 7), dpi=100, facecolor='#f8f9fa')
        self._enlarged_ax = self._enlarged_fig.add_subplot(111)
        self._enlarged_ax.set_facecolor('#ffffff')
        
        # Copy the current plot state to the enlarged view
        self._sync_enlarged_plot(self._enlarged_ax)
        
        # Container frame with rounded corners for the graph
        graph_container = ctk.CTkFrame(
            self._enlarged_overlay,
            fg_color='#f8f9fa',
            corner_radius=12,
        )
        graph_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(12, 8))
        
        # Create canvas for enlarged figure inside the rounded container
        self._enlarged_canvas = FigureCanvasTkAgg(self._enlarged_fig, master=graph_container)
        enlarged_widget = self._enlarged_canvas.get_tk_widget()
        enlarged_widget.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        # Close hint label (translatable)
        self._enlarged_hint_label = ctk.CTkLabel(
            self._enlarged_overlay,
            text=self._t('enlarged_hint'),
            text_color='#888888',
            font=('Segoe UI', 9)
        )
        self._enlarged_hint_label.pack(pady=(0, 8))
        
        # Click on overlay to close
        self._enlarged_canvas.mpl_connect('button_press_event', lambda e: self._close_enlarged_overlay())
        
        self._enlarged_canvas.draw()
    
    def _sync_enlarged_plot(self, ax):
        """Sync the enlarged axes with the current plot panel state"""
        pp = self.plot_panel
        ax.grid(True, linestyle='--', alpha=0.4)
        
        # Copy superposed trajectories first (so they're in background)
        for line, fill in pp._superposed_artists:
            xs, ys = line.get_xdata(), line.get_ydata()
            if len(xs) > 0:
                ax.plot(xs, ys, '-', color='#94a3b8', lw=1, alpha=0.5, zorder=1)
        
        # Copy mean line
        ax.axhline(pp.N / 2, color='r', alpha=0.8, linestyle='--', linewidth=0.8,
                   label=pp._mean_label())
        
        # Copy data based on mode
        if pp.mode == 'realtime':
            xs, ys = pp.history_line.get_xdata(), pp.history_line.get_ydata()
            if len(xs) > 0:
                ax.plot(xs, ys, '-b', lw=1.2, label=pp.texts.get('trajectory_label', 'Trajectory'))
                ax.plot([xs[-1]], [ys[-1]], 'o', color='#fb923c', markersize=8,
                        label=pp.texts.get('current_label', 'Current value'))
        else:  # condensed
            xs, ys = pp.condensed_line.get_xdata(), pp.condensed_line.get_ydata()
            if len(xs) > 0:
                ax.plot(xs, ys, '-b', lw=1.2, label=pp.texts.get('trajectory_label', 'Trajectory'))
                # Copy fill
                paths = pp.condensed_fill.get_paths()
                if paths:
                    from matplotlib.collections import PolyCollection
                    fill = PolyCollection([p.vertices for p in paths], facecolor='C0', alpha=0.18)
                    ax.add_collection(fill)
                last_x, last_y = pp.last_point.get_data()
                if len(last_x) > 0:
                    ax.plot(last_x, last_y, 'o', color='#fb923c', markersize=8,
                            label=pp.texts.get('current_label', 'Current value'))
        
        # Set axes limits and labels
        ax.set_xlim(pp.ax.get_xlim())
        ax.set_ylim(pp.ax.get_ylim())
        title_key = 'title_realtime' if pp.mode == 'realtime' else 'title_condensed'
        ax.set_title(pp.texts.get(title_key, ''), pad=12, fontsize=14)
        ax.set_xlabel(pp.texts.get('x_label', ''), labelpad=8, fontsize=11)
        ax.set_ylabel(pp.texts.get('y_label', ''), fontsize=11)
        ax.legend(fontsize=9, loc='upper right')
    
    def _close_enlarged_overlay(self):
        """Close the enlarged plot overlay"""
        if self._enlarged_overlay is None:
            return
        
        try:
            if self._enlarged_fig is not None:
                plt.close(self._enlarged_fig)
        except Exception:
            pass
        
        try:
            self._enlarged_overlay.destroy()
        except Exception:
            pass
        
        self._enlarged_overlay = None
        self._enlarged_fig = None
        self._enlarged_canvas = None
        self._enlarged_ax = None
        self._enlarged_hint_label = None
    
    def _refresh_enlarged_overlay(self):
        """Refresh the enlarged overlay with current plot data"""
        if self._enlarged_overlay is None or self._enlarged_ax is None:
            return
        
        # Clear and redraw
        self._enlarged_ax.clear()
        self._sync_enlarged_plot(self._enlarged_ax)
        
        try:
            self._enlarged_canvas.draw_idle()
        except Exception:
            pass
        
    def _set_hover_animation_enabled(self, enabled):
        self.hover_animator.set_enabled(enabled)

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
                self.controller.handle_animation_cancelled()
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
            self.controller.handle_animation_cancelled()

    def _on_ball_animation_complete(self):
        self.controller.on_animation_complete()

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
        self.translator.toggle_language()
        self.language = self.translator.language
        self._apply_language()

    def start(self):
        if not self.controller.is_running:
            self._set_hover_animation_enabled(False)
            self._set_info_message()
            self.plot_panel.clear_superposed()
            self.controller.start()

    def pause(self):
        if self.controller.is_running:
            self.controller.pause()
            self._set_hover_animation_enabled(True)
            self._set_info_message('paused_info')

    def reset(self):
        self.balls_panel.cancel_animation()
        self.controller.handle_animation_cancelled()
        val = self._read_and_clamp_n()
        
        if val is None:
            return
        
        self._set_info_message()
        # Reset model and panels
        self.model.reset(N=val)
        self.balls_panel.update(self.model.getState(), self.model.N)
        self.state_diagram.update(self.model.getState(), self.model.N, probs=self.model.getTransitionProbabilities())
        self.plot_panel.clear_superposed()
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
        val = self._read_and_clamp_n()
        if val is None or val == self.model.N:
            return

        self.balls_panel.cancel_animation()
        self.controller.handle_animation_cancelled()

        self.model.setN(val)
        self.model.iteration = 0
        
        # Refresh panels with the new N
        self.balls_panel.update(self.model.getState(), self.model.N)
        self.state_diagram.update(self.model.getState(), self.model.N, probs=self.model.getTransitionProbabilities())
        self.plot_panel.clear_superposed()
        self.plot_panel.update(self.model.getHistory(), self.model.N)
        
        self.canvas.draw_idle()
        self._refresh_enlarged_overlay()
        
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
        self.controller.set_speed(self.speed_ms)

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
            (getattr(self, 'superpose_check', None), 'superpose_checkbox'),
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
                'superposed_label': self._t('superposed_label'),
            })
        
        # Update enlarged overlay hint and content if visible
        if self._enlarged_hint_label is not None:
            try:
                self._enlarged_hint_label.configure(text=self._t('enlarged_hint'))
            except Exception:
                pass
        self._refresh_enlarged_overlay()

    def _apply_panel_updates(self, data):
        self.state_diagram.update(data['X'], data['N'], probs=data['probs'])
        self.plot_panel.update(data['history'], data['N'])
        self._refresh_enlarged_overlay()

    def _t(self, key, **kwargs):
        return self.translator.translate(key, **kwargs)

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
        if self.controller.is_running:
            self.pause()

        self.balls_panel.cancel_animation()
        self.controller.clear_pending_updates()
        
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
            
            m = EhrenfestModel(N=N, initial=start_X)
            
            hist = m.getHistory()
            for _ in range(M):
                x, _ = m.step()
                hist.append(x)

            # Schedule plotting back on main thread
            def finish():
                try:
                    superpose = self.superpose_var.get()
                    self.plot_panel.show_condensed_time(hist, N, superpose=superpose)
                    self.canvas.draw_idle()
                    self._refresh_enlarged_overlay()
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
