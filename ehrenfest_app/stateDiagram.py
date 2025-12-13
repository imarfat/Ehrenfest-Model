import matplotlib.patches as mpatches # type: ignore


class StateDiagram:
    def __init__(self, ax, N=20):
        self.ax = ax
        self.N = N
        self.X = 0
        self.colors = {
            'current': '#fb923c',
            'neighbor': '#e5e7eb',
            'text': '#111827'
        }
        self._xs = [0.2, 0.5, 0.8]
        self._y = 0.62
        self._arrow_pad = 0.08
        self._setup_static_elements()

    def _setup_static_elements(self):
        self.ax.set_title('State Diagram / Markov Chain')
        subtitle = ('Simplified 3-state view. We label the states using an integer\n'
                    r'$n \in \{0, ..., N\}$ corresponding to the number of balls in Box A.'
        )
        try:
            self.subtitle = self.ax.text(
                0.5, 0.955, subtitle,
                ha='center', va='top', transform=self.ax.transAxes,
                fontsize=9, color=self.colors.get('text', 'black')
            )
        except Exception:
            self.subtitle = None
        self.ax.axis('off')

        self.circles = []
        self.labels = []
        
        for x in self._xs:
            circ = mpatches.Circle((x, self._y), 0.08, edgecolor='k', facecolor=self.colors['neighbor'])
            circ.set_visible(False)
            self.ax.add_patch(circ)
            txt = self.ax.text(x, self._y, '', ha='center', va='center', color=self.colors['text'], fontsize=10)
            txt.set_visible(False)
            self.circles.append(circ)
            self.labels.append(txt)

        arrow_style = dict(arrowstyle='->', linewidth=1.0, mutation_scale=12)
        self.arrow_center_to_left = mpatches.FancyArrowPatch(
            (self._xs[1] - self._arrow_pad, self._y),
            (self._xs[0] + self._arrow_pad, self._y),
            **arrow_style
        )
        self.arrow_left_to_center = mpatches.FancyArrowPatch(
            (self._xs[0] + self._arrow_pad, self._y - 0.04),
            (self._xs[1] - self._arrow_pad + 0.01, self._y - 0.04),
            connectionstyle='arc3,rad=0.8', **arrow_style
        )
        self.arrow_center_to_right = mpatches.FancyArrowPatch(
            (self._xs[1] + self._arrow_pad, self._y),
            (self._xs[2] - self._arrow_pad, self._y),
            **arrow_style
        )
        self.arrow_right_to_center = mpatches.FancyArrowPatch(
            (self._xs[2] - self._arrow_pad, self._y - 0.04),
            (self._xs[1] + self._arrow_pad - 0.01, self._y - 0.04),
            connectionstyle='arc3,rad=-0.8', **arrow_style
        )

        self.arrows = [
            self.arrow_center_to_left,
            self.arrow_left_to_center,
            self.arrow_center_to_right,
            self.arrow_right_to_center,
        ]
        for arrow in self.arrows:
            arrow.set_visible(False)
            self.ax.add_patch(arrow)

        self.prob_text_left_above = self.ax.text(
            (self._xs[0] + self._xs[1]) / 2 + 0.01,
            self._y + 0.04,
            '', ha='center', va='bottom', color=self.colors['text'], fontsize=9
        )
        self.prob_text_left_below = self.ax.text(
            (self._xs[0] + self._xs[1]) / 2,
            self._y - 0.18,
            '', ha='center', va='top', color=self.colors['text'], fontsize=9
        )
        self.prob_text_right_above = self.ax.text(
            (self._xs[1] + self._xs[2]) / 2 - 0.01,
            self._y + 0.04,
            '', ha='center', va='bottom', color=self.colors['text'], fontsize=9
        )
        self.prob_text_right_below = self.ax.text(
            (self._xs[1] + self._xs[2]) / 2,
            self._y - 0.18,
            '', ha='center', va='top', color=self.colors['text'], fontsize=9
        )
        
        for txt in (
            self.prob_text_left_above,
            self.prob_text_left_below,
            self.prob_text_right_above,
            self.prob_text_right_below,
        ):
            txt.set_visible(False)

        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)

    def update(self, X, N=None, probs=None):
        if N is not None:
            self.N = int(N)
        self.X = int(X)
        self.probs = probs
        self._update_artists()

    def _update_artists(self):
        states = [self.X - 1, self.X, self.X + 1]
        
        for idx, state in enumerate(states):
            valid = 0 <= state <= self.N
            self.circles[idx].set_visible(valid)
            self.labels[idx].set_visible(valid)
            
            if not valid:
                continue
            
            face = self.colors['current'] if idx == 1 else self.colors['neighbor']
            self.circles[idx].set_facecolor(face)
            self.labels[idx].set_text(str(state))

        has_left = all(0 <= s <= self.N for s in states[:2])
        has_right = all(0 <= s <= self.N for s in states[1:])

        self.arrow_center_to_left.set_visible(has_left)
        self.arrow_left_to_center.set_visible(has_left)
        self.prob_text_left_above.set_visible(has_left)
        self.prob_text_left_below.set_visible(has_left)
        
        if has_left and self.N > 0:
            p_down = float(self.X) / float(self.N)
            p_from_left = (self.N - (self.X - 1)) / self.N
            self.prob_text_left_above.set_text(self._format_prob(p_down))
            self.prob_text_left_below.set_text(self._format_prob(p_from_left))

        self.arrow_center_to_right.set_visible(has_right)
        self.arrow_right_to_center.set_visible(has_right)
        self.prob_text_right_above.set_visible(has_right)
        self.prob_text_right_below.set_visible(has_right)
        
        if has_right and self.N > 0:
            p_up = float(self.N - self.X) / float(self.N)
            p_from_right = (self.X + 1) / self.N
            self.prob_text_right_above.set_text(self._format_prob(p_up))
            self.prob_text_right_below.set_text(self._format_prob(p_from_right))

    def _format_prob(self, value):
        places = 3 if self.N >= 1000 else 2
        return f'{value:.{places}f}'
