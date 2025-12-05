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
        self.ax.axis('off')

    def update(self, X, N=None, probs=None):
        if N is not None:
            self.N = int(N)
        self.X = int(X)
        self.probs = probs
        self.draw()

    def draw(self):
        self.ax.clear()
        self.ax.set_title('State Diagram / Markov Chain')
        subtitle = 'Simplified 3-state view. The numbers inside \n of the ovals represent the value of $X_i$.'
        try:
            self.ax.text(0.5, 0.955, subtitle, ha='center', va='top', transform=self.ax.transAxes, fontsize=9, color=self.colors.get('text', 'black'))
        except Exception:
            # Best-effort placement; ignore failures if text rendering isn't available
            pass
        self.ax.axis('off')

        xs = [0.2, 0.5, 0.8]
        # Raise the diagram slightly
        ys = 0.62
        # How far from each state's center the arrow should start/end
        # Note: use a value equal to or a little larger than the circle radius (0.08)
        # Note: too-large padding makes only the head visible
        arrow_pad = 0.08
        arrow_props = dict(arrowstyle='->', linewidth=1.0, mutation_scale=12)
        curve_left_props = dict(arrowstyle='->', linewidth=1.0, mutation_scale=12, connectionstyle='arc3,rad=-0.8')
        curve_right_props = dict(arrowstyle='->', linewidth=1.0, mutation_scale=12, connectionstyle='arc3,rad=0.8')
        
        states = [self.X - 1, self.X, self.X + 1]
        # Add state labels, using None for "out-of-bounds" states
        labels = []
        for s in states:
            if s < 0 or s > self.N:
                labels.append(None)
            else:
                labels.append(str(s))
        
        # Draw states
        for i, lab in enumerate(labels):
            if lab is None:
                continue
            
            # Determine circle color
            face = self.colors['current'] if i == 1 else self.colors['neighbor']
            
            circ = mpatches.Circle((xs[i], ys), 0.08, facecolor=face, edgecolor='k')
            self.ax.add_patch(circ)
            self.ax.text(xs[i], ys, lab, ha='center', va='center', color=self.colors['text'], fontsize=10)

        if labels[0] is not None and labels[1] is not None:
            mid = (xs[0] + xs[1]) / 2
            # Calculate probability of moving down a state
            p_down = float(self.X) / float(self.N) if self.N > 0 else 0.0
            self.ax.annotate('', xy=(xs[0] + arrow_pad, ys), xytext=(xs[1] - arrow_pad, ys), arrowprops=arrow_props)
            # Draw probability label above the arrow at the midpoint
            self.ax.text(mid + 0.01, ys + 0.04, f'{p_down:.2f}', ha='center', va='bottom', color=self.colors['text'], fontsize=9)
        
            p_from_left = (self.N - (self.X - 1)) / self.N if self.N > 0 else 0.0
            self.ax.annotate('', xy=(xs[1] - arrow_pad + 0.01, ys-0.04), xytext=(xs[0] + arrow_pad, ys-0.04), arrowprops=curve_right_props)
            # Draw probability label below the curved arrow
            self.ax.text(mid, ys - 0.18, f'{p_from_left:.2f}', ha='center', va='top', color=self.colors['text'], fontsize=9)
            
        if labels[1] is not None and labels[2] is not None:
            mid = (xs[1] + xs[2]) / 2
            # Calculate probability of moving up a state
            p_up = float(self.N - self.X) / float(self.N) if self.N > 0 else 0.0
            self.ax.annotate('', xy=(xs[2] - arrow_pad, ys), xytext=(xs[1] + arrow_pad, ys), arrowprops=arrow_props)
            # Draw probability label above the arrow at the midpoint
            self.ax.text(mid - 0.01, ys + 0.04, f'{p_up:.2f}', ha='center', va='bottom', color=self.colors['text'], fontsize=9)
            
            p_from_right = (self.X + 1) / self.N if self.N > 0 else 0.0
            self.ax.annotate('', xy=(xs[1] + arrow_pad - 0.01, ys-0.04), xytext=(xs[2] - arrow_pad, ys-0.04), arrowprops=curve_left_props)
            # Draw probability label below the curved arrow
            mid = (xs[1] + xs[2]) / 2
            self.ax.text(mid, ys - 0.18, f'{p_from_right:.2f}', ha='center', va='top', color=self.colors['text'], fontsize=9)
        
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.figure.canvas.draw_idle()
