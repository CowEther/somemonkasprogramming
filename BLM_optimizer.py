from random import randint
from random import random


class game:
    def __init__(self):
        self.available_actions = []
        self.rotation = []
        self.score = 0
        self.encounter = 390
        self.chrono = 0
        value = 3 * random()
        self.preserver_tick = value
        self.postserver_tick = value
        self.mp_regen = 200


class blm_GCDs:
    def __init__(self, name, cast, recast, potency, cost):
        self.name = name
        self.cast = cast
        self.recast = recast
        self.potency = potency
        self.cost = cost
        self.clipping = 0.75


class stance:
    def __init__(self, fire_cost, fire_damage, ice_cost, ice_damage, ice_cast, fire_cast):
        self.fire_cost = fire_cost
        self.fire_damage = fire_damage
        self.ice_cost = ice_cost
        self.ice_damage = ice_damage
        self.ice_cast = ice_cast
        self.fire_cast = fire_cast


class gauge:
    def __init__(self):  # astral fire is positive, umbral ice is negative
        self.stance = 0
        self.polyglot = 0
        self.mp = 10000


dmodifiers = {
    "Astral Fire regen": 0,
    "Umbral Ice 1 regen": 16,
    "Umbral Ice 2 regen": 23.5,
    "Umbral Ice 3 regen": 31,
    "Enochian": 0.85,
    "Leylines": 1.15,
    "MP cap": 10000,
    "MP floor": 0,
}

current_game = game()
default_stance = stance(1, 1, 1, 1, 1, 1)
current_gauge = gauge()

stancef1 = stance(2, 1.4, 0.5, 0.9, 1, 1)
stancef2 = stance(2, 1.6, 0.25, 0.8, 1, 1)
stancef3 = stance(2, 1.8, 0, 0.7, 0.5, 1)
stanceb1 = stance(0.5, 0.9, 0.75, 1, 1, 1)
stanceb2 = stance(0.25, 0.8, 0.5, 1, 1, 1)
stanceb3 = stance(0, 0.7, 0, 1, 1, 0.5)

b1 = blm_GCDs("Blizzard", 2.5, 2.5, 180, 400)
b2 = blm_GCDs("Blizzard II", 2, 2.5, 50, 800)
b3 = blm_GCDs("Blizzard III", 3.5, 2.5, 240, 800)
b4 = blm_GCDs("Blizzard IV", 2.8, 2.5, 300, 800)
f1 = blm_GCDs("Fire", 2.5, 2.5, 180, 800)
f2 = blm_GCDs("Fire II", 3, 2.5, 80, 1500)
f3 = blm_GCDs("Fire III", 3.5, 2.5, 240, 2000)
f4 = blm_GCDs("Fire IV", 2.8, 2.5, 300, 800)
sc = blm_GCDs("Scathe", 0, 2.5, 100, 800)
xe = blm_GCDs("Xenoglossy", 0, 2.5, 750, 0)
de = blm_GCDs("Despair", 3, 2.5, 380, 800)


def reset_abilities():
    b1 = blm_GCDs("Blizzard", 2.5, 2.5, 180, 400)
    b2 = blm_GCDs("Blizzard II", 2, 2.5, 50, 800)
    b3 = blm_GCDs("Blizzard III", 3.5, 2.5, 240, 800)
    b4 = blm_GCDs("Blizzard IV", 2.8, 2.5, 300, 800)
    f1 = blm_GCDs("Fire", 2.5, 2.5, 180, 800)
    f2 = blm_GCDs("Fire II", 3, 2.5, 80, 1500)
    f3 = blm_GCDs("Fire III", 3.5, 2.5, 240, 2000)
    f4 = blm_GCDs("Fire IV", 2.8, 2.5, 300, 800)
    sc = blm_GCDs("Scathe", 0, 2.5, 100, 800)
    xe = blm_GCDs("Xenoglossy", 0, 2.5, 750, 0)
    de = blm_GCDs("Despair", 3, 2.5, 380, 800)
    current_game.available_actions = [
        b1, b2, b3, b4, f1, f2, f3, f4, sc, xe, de]
    current_game.unavailable_actions = []


'''def mp_tick():
    if current_game.postserver_tick - current_game.preserver_tick >= 3:
        current_game.preserver_tick += 3
        if current_gauge.stance == 0:
            current_gauge.mp = max(
                min(current_gauge.mp + current_game.mp_regen, dmodifiers.get("MP cap")), dmodifiers.get("MP floor"))
        if current_gauge.stance > 0:
            current_gauge.mp = max(
                min(current_gauge.mp + current_game.mp_regen * dmodifiers.get("Astral Fire regen"), dmodifiers.get("MP cap")), dmodifiers.get("MP floor"))
        else:
            if current_gauge.stance == -1:
                current_gauge.mp = max(
                    min(current_gauge.mp + current_game.mp_regen * dmodifiers.get("Umbral Ice 1 regen"), dmodifiers.get("MP cap")), dmodifiers.get("MP floor"))
            if current_gauge.stance == -2:
                current_gauge.mp = max(
                    min(current_gauge.mp + current_game.mp_regen * dmodifiers.get("Umbral Ice 2 regen"), dmodifiers.get("MP cap")), dmodifiers.get("MP floor"))
            if current_gauge.stance == -3:
                current_gauge.mp = max(
                    min(current_gauge.mp + current_game.mp_regen * dmodifiers.get("Umbral Ice 3 regen"), dmodifiers.get("MP cap")), dmodifiers.get("MP floor"))'''


def pop_available_actions(action):
    current_game.available_actions.remove(action)


def apply_modifiers(current_stance):
    for action in current_game.available_actions:
        if action == f1 or action == f2 or action == f3 or action == f4:
            action.cost = action.cost * current_stance.fire_cost
            action.potency = action.potency * current_stance.fire_damage
            action.cast = action.cast * current_stance.fire_cast
        if action == b1 or action == b2 or action == b3 or action == b4:
            action.cost = action.cost * current_stance.ice_cost
            action.potency = action.potency * current_stance.ice_damage
            action.cast = action.cast * current_stance.ice_cast


def check_conditions():
    reset_abilities()
    if current_gauge.stance != 3:
        pop_available_actions(f4)
    if current_gauge.stance != -3:
        pop_available_actions(b4)
    if current_gauge.polyglot == 0:
        pop_available_actions(xe)
    if current_gauge.stance == 1:
        apply_modifiers(stancef1)
    if current_gauge.stance == 2:
        apply_modifiers(stancef2)
    if current_gauge.stance == 3:
        apply_modifiers(stancef3)
    if current_gauge.stance == -1:
        apply_modifiers(stanceb1)
    if current_gauge.stance == -2:
        apply_modifiers(stanceb2)
    if current_gauge.stance == -3:
        apply_modifiers(stanceb3)
    else:
        apply_modifiers(default_stance)
    for x in current_game.available_actions:
        if current_gauge.mp - x.cost < 0:
            pop_available_actions(str(x))


def pick_ability():
    length = len(current_game.available_actions)
    index = randint(0, length - 1)
    action_used = current_game.available_actions[index]
    current_game.rotation.append(action_used)
    current_gauge.mp -= action_used.cost
    effective_cast = action_used.cast + action_used.clipping
    time_elapsed = max(effective_cast, action_used.recast)
    current_game.chrono += time_elapsed
    current_game.encounter -= time_elapsed


# def check_penalties():


def score():
    for action in current_game.rotation:
        print(action.name + "was used and did" + action.potency + "potency.")


def main():
    reset_abilities()
    while current_game.encounter > 0:
        # mp_tick()
        check_conditions()
        pick_ability()
    # check_penalties()
    score()


main()
