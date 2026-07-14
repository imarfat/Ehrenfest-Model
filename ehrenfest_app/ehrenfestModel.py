import math
import random
import statistics
import sys


def _configure_stdout_utf8():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass


def print_simulation_statistics(N, M, initial=None, rng=None):
    """
    Run an Ehrenfest simulation for M iterations with N balls and print
    summary statistics comparing empirical and theoretical relative spread.
    """
    N = int(N)
    M = int(M)
    if N <= 0:
        raise ValueError("N must be a positive integer.")
    if M < 0:
        raise ValueError("M must be a non-negative integer.")

    model = EhrenfestModel(N=N, initial=initial, rng=rng)
    for _ in range(M):
        model.step()

    history = model.getHistory()
    x_bar = statistics.mean(history)
    sigma_hat = statistics.stdev(history) if len(history) > 1 else 0.0
    empirical_rel_std = sigma_hat / x_bar if x_bar != 0 else float("nan")
    theoretical_rel_std = 1 / math.sqrt(N)

    if theoretical_rel_std != 0 and not math.isnan(empirical_rel_std):
        rel_diff_pct = abs(empirical_rel_std - theoretical_rel_std) / theoretical_rel_std * 100
    else:
        rel_diff_pct = float("nan")

    _configure_stdout_utf8()
    print(f"N = {N}, M = {M}")
    print(f"X_bar (mean of state history) = {x_bar:.6f}")
    print(f"sigma_hat (standard deviation of state history) = {sigma_hat:.6f}")
    print(f"sigma_hat/X_bar (empirical relative standard deviation) = {empirical_rel_std:.6f}")
    print(f"1/sqrt(N) (theoretical relative standard deviation) = {theoretical_rel_std:.6f}")
    print(f"Relative difference = {rel_diff_pct:.2f}%")

    return {
        "N": N,
        "M": M,
        "x_bar": x_bar,
        "sigma_hat": sigma_hat,
        "empirical_rel_std": empirical_rel_std,
        "theoretical_rel_std": theoretical_rel_std,
        "relative_difference_pct": rel_diff_pct,
        "history": history,
    }


class EhrenfestModel:
    """Simulation core for the Ehrenfest model."""

    def __init__(self, N=20, initial=None, rng=None):
        self.N = int(N)
        if initial is None:
            # Random initial distribution
            self.X = random.randint(0, self.N)
        else:
            self.X = int(initial)
        self.iteration = 0
        self.history = [self.X]
        self.rng = rng if rng is not None else random

    def step(self):
        """
        Perform one step: pick a ball uniformly and move to the other box.
        Returns the new X value and a tuple of transition probabilities (p_up, p_down).
        """
        # Probability of moving a ball to box A (increasing X_i)
        p_up = (self.N - self.X) / self.N
        # Probability of moving a ball to box B (decreasing X_i)
        p_down = self.X / self.N

        if self.rng.random() < p_up:
            self.X += 1
        else:
            self.X -= 1

        self.iteration += 1
        self.history.append(self.X)
        return self.X, (p_up, p_down)

    def reset(self, N=None, initial=None):
        """Reset the simulation. Optionally set a new N and/or initial X."""
        if N is not None:
            self.N = int(N)
        if initial is None:
            self.X = random.randint(0, self.N)
        else:
            self.X = int(initial)
        self.iteration = 0
        self.history = [self.X]

    def setN(self, N):
        self.N = int(N)
        # Clamp X to [0, N]
        self.X = max(0, min(self.X, self.N))
        self.history = [self.X]

    def getState(self):
        return self.X

    def getHistory(self):
        return list(self.history)

    def getTransitionProbabilities(self):
        return ((self.N - self.X) / self.N, self.X / self.N)
