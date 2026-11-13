# Прогоны: команды характеров против кухни.

import random
import sys

from agents import AGENTS
from menu import GROUPS, GROUP_ORDER
from world import World

# Сдвиг для генератора агентов: чтобы он не совпадал с сидом мира
SEED_OFFSET = 7919


def parse_agent(spec):
    # Строка 'имя[:avg|alpha]' -> (класс агента, шаг обновления).
    name, _, step = spec.partition(":")
    name = name.strip().lower()
    if name not in AGENTS:
        sys.exit("нет такого характера: %s (есть: %s)"
                 % (name, ", ".join(sorted(set(AGENTS)))))
    step = step.strip().lower() or "alpha"
    if step not in ("avg", "alpha"):
        sys.exit("после двоеточия — avg или alpha, а не «%s»" % step)
    return AGENTS[name], step


def describe(spec):
    agent_cls, step = parse_agent(spec)
    return "%s(%s)" % (agent_cls.__name__.replace("Agent", "").lower(), step)


def make_team(specs, seed):
    rng = random.Random(seed + SEED_OFFSET)
    team = {}
    for group, spec in zip(GROUP_ORDER, specs):
        agent_cls, step = parse_agent(spec)
        team[group] = agent_cls(len(GROUPS[group]["dishes"]), step)
    return team, rng


def run_team(world, specs, days, seed, log=0):
    # Одна команда на одном мире. Возвращает словарь статистики.
    team, rng = make_team(specs, seed)
    total = 0.0
    regret = 0.0
    best_hits = {group: 0 for group in GROUP_ORDER}
    for day in range(1, days + 1):
        world.drift()
        day_sum = 0.0
        for group in GROUP_ORDER:
            agent = team[group]
            dish = agent.choose(rng)
            reward = world.reward(group, dish)
            agent.update(dish, reward)
            total += reward
            day_sum += reward
            if dish == world.best_dish(group):
                best_hits[group] += 1
        regret += world.best_sum() - day_sum
        if log and day % log == 0:
            print("  день %4d | доход %7.2f | потолок %5.2f"
                  % (day, total, world.best_sum()))
    share = {g: best_hits[g] / days for g in GROUP_ORDER}
    return {"total": total, "share": share, "regret": regret}


def selftest():
    # Каждая стратегия делает 20 шагов на маленьком мире — без ошибок.
    for name in ("завсегдатай", "пятница", "любопытный", "тянущийся", "оптимист"):
        for step in ("alpha", "avg"):
            world = World([0.05] * 4, seed=1)
            specs = ["%s:%s" % (name, step)] * 4
            run_team(world, specs, days=20, seed=1)
    print("selftest: ok — все 5 стратегий × 2 шага обновления, 20 дней, без ошибок")


def ask(prompt):
    # Ввод с подсказкой; если ввода нет (файл, пайп) — выходим по-человечески.
    try:
        return input(prompt)
    except EOFError:
        sys.exit("\nНет ввода: --play запускают в терминале, где можно набирать цифры.")


def read_bet():
    if not sys.stdin.isatty():
        return None
    answer = input("Ставка: кто победит? [1/2/Enter — без ставки]: ").strip()
    return answer if answer in ("1", "2") else None


def duel(args):
    team1, team2 = args.duel[0].split(","), args.duel[1].split(",")
    for specs in (team1, team2):
        if len(specs) != len(GROUP_ORDER):
            sys.exit("в команде %d характеров: %s"
                     % (len(GROUP_ORDER), ", ".join(GROUP_ORDER)))
    print("Команда 1: %s" % " · ".join(describe(s) for s in team1))
    print("Команда 2: %s" % " · ".join(describe(s) for s in team2))
    print("σ по группам: %s | дней: %d | сид: %d"
          % (", ".join("%s %.2f" % (g, s) for g, s in zip(GROUP_ORDER, args.sigma)),
             args.days, args.seed))
    bet = read_bet()

    # Одна кухня на обе команды: одинаковые сиды мира и агентов,
    # чтобы сравнение было честным — различие только в стратегиях.
    world1 = World(args.sigma, args.seed)
    world2 = World(args.sigma, args.seed)
    result1 = run_team(world1, team1, args.days, args.seed, args.log)
    result2 = run_team(world2, team2, args.days, args.seed, args.log)

    print()
    header = "%-10s %22s %22s" % ("группа", "команда 1", "команда 2")
    print(header)
    print("доля лучшего:")
    for group in GROUP_ORDER:
        print("%-10s %21.0f%% %21.0f%%"
              % (group, result1["share"][group] * 100, result2["share"][group] * 100))
    print("%-10s %22.2f %22.2f" % ("доход", result1["total"], result2["total"]))
    print("%-10s %22.2f %22.2f" % ("regret", result1["regret"], result2["regret"]))
    if abs(result1["total"] - result2["total"]) < 1e-9:
        winner = None
        print("\nНичья.")
    else:
        winner = "1" if result1["total"] > result2["total"] else "2"
        print("\nПобедила команда %s." % winner)
    if bet:
        if winner is None:
            print("Ставка %s — ничья, ставка не сыграла." % bet)
        else:
            print("Ставка %s — %s." % (bet, "угадал" if bet == winner else "не угадал"))


def play(args):
    rng = random.Random(args.seed)
    world = World(args.sigma, rng.randrange(10 ** 6))
    opponent = None
    if getattr(args, "vs", None):
        opp_specs = [args.vs] * len(GROUP_ORDER)
        opponent, opp_rng = make_team(opp_specs, args.seed + 31)
        print("Соперник: %s" % describe(args.vs))
    total = 0.0
    opp_total = 0.0
    best_hits = {group: 0 for group in GROUP_ORDER}
    history = {group: [[] for _ in GROUPS[group]["dishes"]] for group in GROUP_ORDER}
    ceiling = sum(GROUPS[group]["bounds"][1] for group in GROUP_ORDER)
    for day in range(1, args.days + 1):
        world.drift()
        print("\n== день %d ==" % day)
        for group in GROUP_ORDER:
            dishes = GROUPS[group]["dishes"]
            for i, (name, _) in enumerate(dishes):
                entries = history[group][i]
                mean = sum(entries) / max(1, len(entries))
                print("  %d — %-10s (моё среднее: %.2f)" % (i + 1, name, mean))
            while True:
                try:
                    dish = int(ask("%s? [1-%d] " % (group, len(dishes)))) - 1
                    assert 0 <= dish < len(dishes)
                    break
                except (ValueError, AssertionError):
                    print("  цифрой от 1 до %d" % len(dishes))
            reward = world.reward(group, dish)
            history[group][dish].append(reward)
            total += reward
            if dish == world.best_dish(group):
                best_hits[group] += 1
            print("  удовольствие: %.2f" % reward)
            if opponent is not None:
                agent = opponent[group]
                opp_dish = agent.choose(opp_rng)
                opp_reward = world.reward(group, opp_dish)
                agent.update(opp_dish, opp_reward)
                opp_total += opp_reward
    print("\nИтого: доход %.2f из потолка ~%.2f" % (total, args.days * ceiling))
    for group in GROUP_ORDER:
        print("  %-10s лучшее блюдо: %3.0f%% дней"
              % (group, best_hits[group] / args.days * 100))
    if opponent is not None:
        print("Соперник набрал %.2f." % opp_total)
        if abs(opp_total - total) < 1e-9:
            print("Ничья.")
        elif opp_total > total:
            print("Победил соперник.")
        else:
            print("Победил человек.")
