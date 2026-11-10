import math
import random

from environment import CHANNELS


class Agent:

    def __init__(self, mode="greedy", epsilon=0.1, alpha=None, c=2.0, eta=0.1,
                 start_q=0.0, seed=None):
        self.mode = mode
        self.epsilon = epsilon
        self.alpha = alpha
        self.c = c
        self.eta = eta
        self.start_q = start_q
        self.rng = random.Random(seed)
        self.reset()

    def reset(self):
        self.q = {c: self.start_q for c in CHANNELS}
        self.n = {c: 0 for c in CHANNELS}
        self.h = {c: 0.0 for c in CHANNELS}
        self.turn = 0
        self.baseline = 0.0

    def update(self, channel, reward):
        self.turn += 1
        self.n[channel] += 1
        if self.n[channel] == 1:
            self.q[channel] = reward
        else:
            step = self.alpha if self.alpha is not None else 1.0 / self.n[channel]
            self.q[channel] += step * (reward - self.q[channel])
            # raise NotImplementedError("Agent.update")
        if self.mode == "gradient":
            self.gradient_update(channel, reward)

    def preferences(self):
        top = max(self.h.values())
        exps = {c: math.exp(self.h[c] - top) for c in CHANNELS}
        total = sum(exps.values())
        return {c: exps[c] / total for c in CHANNELS}
        # raise NotImplementedError("Agent.preferences")

    def choose(self):
        if self.mode == "eps" and self.rng.random() < self.epsilon:
            return self.rng.choice(CHANNELS)
        if self.mode == "gradient":
            weights = self.preferences()
            return self.rng.choices(CHANNELS, weights=[weights[c] for c in CHANNELS])[0]
        if self.mode == "ucb":
            return self.ucb_choice()
        return self.greedy_choice()

    def greedy_choice(self):
        top = max(self.q.values())
        return [c for c in CHANNELS if self.q[c] == top][0]

    def ucb_choice(self):
        for c in CHANNELS:
            if self.n[c] == 0:
                return c
        return max(CHANNELS, key=self.ucb_score)

    def ucb_score(self, channel):
        return self.q[channel] + self.c * math.sqrt(math.log(self.turn) / self.n[channel])
        # raise NotImplementedError("Agent.ucb_score")

    def gradient_update(self, channel, reward):
        self.baseline += (reward - self.baseline) / self.turn
        weights = self.preferences()
        for c in CHANNELS:
            bonus = 1.0 if c == channel else 0.0
            self.h[c] += self.eta * (reward - self.baseline) * (bonus - weights[c])
