class SimulationController:
    def __init__(self, *, scheduler, model, animate_step, apply_panel_updates, redraw_canvas, update_status, speed_ms=500):
        self.scheduler = scheduler
        self.model = model
        self.animate_step = animate_step
        self.apply_panel_updates = apply_panel_updates
        self.redraw_canvas = redraw_canvas
        self.update_status = update_status
        self.speed_ms = speed_ms

        self.running = False
        self._waiting_for_animation = False
        self._pending_panel_update = None

    @property
    def is_running(self):
        return self.running

    def set_speed(self, speed_ms):
        self.speed_ms = max(1, int(speed_ms))

    def start(self):
        if self.running:
            return
        self.running = True
        self._waiting_for_animation = False
        self._pending_panel_update = None
        self._run_step()

    def pause(self):
        if not self.running:
            return
        self.running = False
        self._waiting_for_animation = False

    def clear_pending_updates(self):
        self._pending_panel_update = None
        self._waiting_for_animation = False

    def handle_animation_cancelled(self):
        if self._pending_panel_update is not None:
            self._pending_panel_update = None
        if self._waiting_for_animation and self.running:
            self._waiting_for_animation = False
            self.scheduler.after(self.speed_ms, self._run_step)

    def on_animation_complete(self):
        self._waiting_for_animation = False
        if self._pending_panel_update is not None:
            data = self._pending_panel_update
            self._pending_panel_update = None
            self.apply_panel_updates(data)
        self.update_status()
        self.redraw_canvas()
        if self.running:
            self.scheduler.after(self.speed_ms, self._run_step)

    def _run_step(self):
        if not self.running:
            return

        X, probs = self.model.step()
        animation_active = self.animate_step(X, self.model.N)
        history = self.model.getHistory()

        data = {
            'X': X,
            'N': self.model.N,
            'probs': probs,
            'history': history if not animation_active else history.copy(),
            'iteration': self.model.iteration,
        }

        if animation_active:
            self._pending_panel_update = data
            self._waiting_for_animation = True
        else:
            self.apply_panel_updates(data)
            self._waiting_for_animation = False
            self.scheduler.after(self.speed_ms, self._run_step)

        self.update_status()
        self.redraw_canvas()
