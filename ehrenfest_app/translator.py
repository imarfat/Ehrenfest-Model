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
    'superpose_checkbox': {
        'en': 'Superpose',
        'hr': 'Superponiraj',
    },
    'superposed_label': {
        'en': 'Previous runs',
        'hr': 'Prethodni pokusi',
    },
    'enlarged_hint': {
        'en': 'Click anywhere or press Esc to close',
        'hr': 'Kliknite bilo gdje ili pritisnite Esc za zatvaranje',
    },
}

class Translator:
    def __init__(self, language='en'):
        self.language = language

    def set_language(self, lang):
        if lang not in ('en', 'hr'):
            return False
        if lang == self.language:
            return False
        self.language = lang
        return True

    def toggle_language(self):
        next_lang = 'hr' if self.language == 'en' else 'en'
        self.language = next_lang
        return self.language

    def translate(self, key, **kwargs):
        template = LANGUAGE_TEXT.get(key, {}).get(self.language)
        if template is None:
            template = LANGUAGE_TEXT.get(key, {}).get('en', '')
        try:
            return template.format(**kwargs)
        except Exception:
            return template
