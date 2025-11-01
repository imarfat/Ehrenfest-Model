import random


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
