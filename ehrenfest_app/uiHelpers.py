import os
import numpy as np  # type: ignore
import customtkinter as ctk  # type: ignore
from PIL import Image  # type: ignore


def create_grain_image(size, seed=0):
    try:
        rng = np.random.RandomState(seed)
        noise = rng.normal(loc=0.0, scale=1.0, size=size)
        noise = (noise - noise.min()) / (noise.max() - noise.min())
        noise = 0.98 + 0.012 * (noise - 0.5)
        array = (noise * 255).astype(np.uint8)
        return Image.fromarray(array, mode='L').convert('RGB')
    except Exception:
        return None


def load_translate_icon(base_dir):
    try:
        icon_path = os.path.join(base_dir, 'assets', 'translate.png')
        if not os.path.exists(icon_path):
            return None
        target_size = (24, 24)
        image = Image.open(icon_path).convert('RGBA')
        if image.size != target_size:
            try:
                image = image.resize(target_size, Image.LANCZOS)
            except Exception:
                image = image.resize(target_size)
        return ctk.CTkImage(light_image=image, dark_image=image, size=target_size)
    except Exception:
        return None


class GrainBackground:
    def __init__(self, base_image):
        self._base_image = base_image
        self._label = None
        self._image = None

    def attach(self, frame):
        if self._base_image is None:
            return
        self._label = ctk.CTkLabel(frame, text='', image=None, fg_color='transparent')
        self._label.place(relwidth=1, relheight=1)
        self._label.lower()
        frame.bind('<Configure>', self._on_resize)

    def _on_resize(self, event):
        if self._base_image is None or self._label is None:
            return
        width = max(getattr(event, 'width', self._label.winfo_width()), 1)
        height = max(getattr(event, 'height', self._label.winfo_height()), 1)
        self._update_background(width, height)

    def _update_background(self, width, height):
        if self._base_image is None or self._label is None:
            return
        try:
            resized = self._base_image.resize((width, height), Image.LANCZOS)
        except Exception:
            resized = self._base_image.resize((width, height))
        self._image = ctk.CTkImage(light_image=resized, dark_image=resized, size=(width, height))
        try:
            self._label.configure(image=self._image)
            self._label.image = self._image
        except Exception:
            pass


class HoverAnimationManager:
    def __init__(self, steps=20, delay_ms=10):
        self._states = {}
        self._step_size = 1.0 / steps if steps else 1.0
        self._delay_ms = delay_ms

    def apply(self, widget, color_start, color_end):
        state = {
            'color_start': color_start,
            'color_end': color_end,
            'current': 0.0,
            'target': 0.0,
            'running': False,
            'enabled': True,
            'is_hovered': False,
        }
        self._states[widget] = state
        self._apply_colors(widget, state)
        widget.bind('<Enter>', lambda _e, w=widget: self._on_enter(w), add='+')
        widget.bind('<Leave>', lambda _e, w=widget: self._on_leave(w), add='+')
        return widget

    def set_enabled(self, enabled):
        for widget, state in self._states.items():
            state['enabled'] = enabled
            state['target'] = 0.0
            state['current'] = 0.0
            state['running'] = False
            self._apply_colors(widget, state)

    def _on_enter(self, widget):
        state = self._states.get(widget)
        if not state:
            return
        state['is_hovered'] = True
        if state['enabled']:
            self._start_animation(widget, state, 1.0)
        else:
            self._apply_colors(widget, state)

    def _on_leave(self, widget):
        state = self._states.get(widget)
        if not state:
            return
        state['is_hovered'] = False
        if state['enabled']:
            self._start_animation(widget, state, 0.0)
        else:
            self._apply_colors(widget, state)

    def _start_animation(self, widget, state, target):
        state['target'] = target
        if state['running']:
            return
        state['running'] = True
        self._animate(widget)

    def _animate(self, widget):
        state = self._states.get(widget)
        if not state:
            return
        diff = state['target'] - state['current']
        if abs(diff) < self._step_size:
            state['current'] = state['target']
            state['running'] = False
            self._apply_color_from_state(widget, state)
            return
        if diff > 0:
            state['current'] = min(state['current'] + self._step_size, state['target'])
        else:
            state['current'] = max(state['current'] - self._step_size, state['target'])
        self._apply_color_from_state(widget, state)
        try:
            widget.after(self._delay_ms, lambda w=widget: self._animate(w))
        except Exception:
            state['running'] = False

    def _apply_colors(self, widget, state):
        if not state['enabled']:
            color = state['color_end'] if state['is_hovered'] else state['color_start']
            self._configure_colors(widget, color, color)
            return
        self._apply_color_from_state(widget, state)

    def _apply_color_from_state(self, widget, state):
        color = self._blend(state['color_start'], state['color_end'], state['current'])
        self._configure_colors(widget, color, color)

    def _configure_colors(self, widget, fg_color, hover_color):
        try:
            widget.configure(fg_color=fg_color, hover_color=hover_color)
        except Exception:
            pass

    def _blend(self, c1_hex, c2_hex, t):
        c1 = self._hex_to_rgb(c1_hex)
        c2 = self._hex_to_rgb(c2_hex)
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        return self._rgb_to_hex((r, g, b))

    def _hex_to_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, rgb):
        return '#{0:02x}{1:02x}{2:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
