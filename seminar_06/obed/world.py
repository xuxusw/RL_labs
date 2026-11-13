# Среда: кухня, чьи средние дрейфуют независимо по группам.

import random

from menu import (
    GROUPS,
    GROUP_ORDER,
    NOISE,
    REWARD_CAP,
    REWARD_FLOOR,
)


class World:
    # Состояние кухни и выдача наград.
#
    # Каждый шаг все средние сдвигаются независимым шагом гауссовского
    # блуждания и обрезаются по коридору своей группы (как в LAB2:
    # clip(mu + N(0, sigma), low, high)).

    def __init__(self, sigmas, seed):
        self.rng = random.Random(seed)
        self.sigmas = dict(zip(GROUP_ORDER, sigmas))
        self.mu = {
            group: [mean for _, mean in GROUPS[group]["dishes"]]
            for group in GROUP_ORDER
        }

    def drift(self):
        for group in GROUP_ORDER:
            sigma = self.sigmas[group]
            if sigma <= 0:
                continue
            low, high = GROUPS[group]["bounds"]
            self.mu[group] = [
                min(high, max(low, mean + self.rng.gauss(0.0, sigma)))
                for mean in self.mu[group]
            ]

    def reward(self, group, dish):
        mean = self.mu[group][dish]
        value = self.rng.gauss(mean, NOISE)
        return min(REWARD_CAP, max(REWARD_FLOOR, value))

    def best_dish(self, group):
        best = max(range(len(self.mu[group])), key=lambda i: (self.mu[group][i], -i))
        return best

    def best_sum(self):
        return sum(max(self.mu[group]) for group in GROUP_ORDER)
