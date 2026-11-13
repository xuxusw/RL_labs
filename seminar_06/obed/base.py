# Базовый агент многорукого бандита.

import knobs


class BanditAgent:
    # Ведёт счётчики и оценки; выбор блюда — в подклассах.
#
    # Параметр step задаёт правило обновления оценки:
    # "avg" — честное среднее (шаг 1/n), "alpha" — постоянный шаг.

    def __init__(self, n_arms, step="alpha"):
        if step not in ("avg", "alpha"):
            raise ValueError("step должен быть 'avg' или 'alpha'")
        self.step = step
        self.n_arms = n_arms
        self.q = [0.0] * n_arms
        self.n = [0] * n_arms
        self.t = 0

    def choose(self, rng):
        raise NotImplementedError

    def update(self, arm, reward):
        self.t += 1
        self.n[arm] += 1
        if self.n[arm] == 1:
            self.q[arm] = reward
            return
        # шаг: 1/n — честное среднее; alpha — постоянный, не зависит от числа проб
        step = 1.0 / self.n[arm] if self.step == "avg" else knobs.ALPHA
        self.q[arm] += step * (reward - self.q[arm])

    def greedy_arm(self):
        return max(range(self.n_arms), key=lambda i: (self.q[i], -i))
