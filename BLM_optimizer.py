import random
import math
# import threading
# import pynput
# import time
import os
# from pynput import keyboard
import pygame
# import thorpy


# **** GAME Values ****
class game:
    def __init__(self, limit_milliseconds):
        self.milliseconds = 0
        self.game_over = False
        self.combat = False
        self.limit_milliseconds = limit_milliseconds

    def update_game(self, game, dummy):  # game chrono and time limit counter
        game.milliseconds += 1
        game.limit_milliseconds = max(game.limit_milliseconds - 1, 0)
        if game.limit_milliseconds == 0:
            game.game_over = True


# **** PLAYER values ****
class player:
    def __init__(self, mattp, intelligence, direct_hit, critical_hit, determination, spell_speed):
        self.mattp = mattp
        self.intelligence = intelligence
        self.direct_hit = direct_hit
        self.critical_hit = critical_hit
        self.determination = determination
        self.spell_speed = spell_speed
        self.available_actions = []
        self.casting = None
        self.casting_status = None
        self.cast_taxed = 0
        self.enochan_ON = 0
        self.enochan_CD = 0
        self.pending_enochan = 0
        self.polyglot = 0
        self.polyglot_counter = 0
        self.mp = 10000
        self.pending_mp = 0
        self.mp_tick = 200
        self.mp_regen = True
        self.stance = 0
        self.pending_stance = 0
        self.character_tick = random.randint(0, 300)
        self.gcd_cd = 0
        self.leylines_cd = 0
        self.leylines_ON = 0

    # every player chrono is decremented by 1 every cycle. some are incremented by 1 like polyglot and server ticks
    def update_player(self, player):
        player.character_tick = min(player.character_tick + 1, 300)
        if player.casting_status is not None:
            player.casting_status = max(player.casting_status - 1, 0)
        player.cast_taxed = max(player.cast_taxed - 1, 0)
        player.enochan_ON = max(player.enochan_ON - 1, 0)
        player.enochan_CD = max(player.enochan_CD - 1, 0)
        player.gcd_cd = max(player.gcd_cd - 1, 0)
        player.leylines_cd = max(player.leylines_cd - 1, 0)
        player.leylines_ON = max(player.leylines_ON - 1, 0)
        if player.stance == 0:  #
            player.enochan_ON = 0
        if player.enochan_ON > 0:
            player.polyglot_counter = min(player.polyglot_counter + 1, 3000)
        if player.enochan_ON == 0:
            player.polyglot_counter = 0

    # if server tick is met while under umbral ice, regen MP
    def math_mpregen(self, player, game):
        stance = dstance.get(player.stance)
        if player.character_tick == 300:
            player.character_tick = 0
            player.character_tick = 0
            player.mp = min(player.mp + player.mp_tick * stance.mp_mod, 10000)
            print("{:.2f}".format(game.milliseconds / 100).rjust(7) +
                  " You gain " + str(player.mp_tick * stance.mp_mod) + " MP.")

    # if 30 seconds elapsed, add 1 polyglot stack
    def math_polyglot(self, player, game):
        if player.polyglot_counter == 3000:
            player.polyglot = min(player.polyglot + 1, 2)
            print("{:.2f}".format(game.milliseconds / 100).rjust(7) +
                  "You gain a polyglot stack and you now have " + str(int(player.polyglot)) + " stacks.")
            player.polyglot_counter = 0


# **** DUMMY values ****
class dummy:
    def __init__(self):
        self.damage_taken = 0
        self.pending_damage = None
        self.character_tick = random.randint(0, 300)


# **** Astral Fire and Umbral Ice values ****
class stance:
    def __init__(self, fire_cost, fire_damage, ice_cost, ice_damage, ice_cast, fire_cast, mp_mod, name):
        self.fire_cost = fire_cost
        self.fire_damage = fire_damage
        self.ice_cost = ice_cost
        self.ice_damage = ice_damage
        self.ice_cast = ice_cast
        self.fire_cast = fire_cast
        self.mp_mod = mp_mod
        self.name = name


# fire_cost, fire_damage, ice_cost, ice_damage, ice_cast, fire_cast, mp_mod, name
default_stance = stance(1,   1,    1,   1,   1,   1,    1, "Neutral Stance")
stancef1 = stance(2, 1.4,  0.5, 0.9,   1,   1,    0, "Astral Fire I")
stancef2 = stance(2, 1.6, 0.25, 0.8,   1,   1,    0, "Astral Fire II")
stancef3 = stance(2, 1.8,    0, 0.7, 0.5,   1,    0, "Astral Fire III")
stanceb1 = stance(0.5, 0.9, 0.75,   1,   1,   1,   16, "Umbral Ice I")
stanceb2 = stance(0.25, 0.8,  0.5,   1,   1,   1, 23.5, "Umbral Ice II")
stanceb3 = stance(0, 0.7,    0,   1,   1, 0.5,   31, "Umbral Ice III")

dstance = {
    0: default_stance,
    1: stancef1,
    2: stancef2,
    3: stancef3,
    -1: stanceb1,
    -2: stanceb2,
    -3: stanceb3,
}


# Will hold damage properties
class damage():
    def __init__(self, amount, crit, dh):
        self.amount = amount
        self.crit = crit
        self.dh = dh


# Will hold DoT properties
class dot():
    def __init__(self, amount, crit, dh):
        return


# **** BLM GCDs and oGCDs ****
class blm_actions:
    def __init__(self, name, cast_delay, tax, recast_delay, potency, cost, element, gcd):
        self.name = name
        self.cast_delay = cast_delay
        self.recast_delay = recast_delay
        self.potency = potency
        self.cost = cost
        self.element = element
        self.tax = tax
        self.gcd = gcd

    def math_cast(self, action, player):
        fspd = math.floor(130 * (player.spell_speed - 380) / 3300 + 1000)
        gcd1 = math.floor((2000 - fspd) * action.cast_delay / 1000)
        if player.leylines_ON > 0:
            gcd2 = math.floor((100 - 15) * (100 - 0) / 100)
        else:
            gcd2 = math.floor((100 - 0) * (100 - 0) / 100)
        gcd3 = (100 - 0) / 100
        if player.stance == 3 and action.element == "ice":
            gcd4 = math.floor(math.floor(
                math.ceil(gcd2 * gcd3) * gcd1 / 100) * 50 / 100)
        elif player.stance == -3 and action.element == "fire":
            gcd4 = math.floor(math.floor(
                math.ceil(gcd2 * gcd3) * gcd1 / 100) * 50 / 100)
        else:
            gcd4 = math.floor(math.floor(
                math.ceil(gcd2 * gcd3) * gcd1 / 100) * 100 / 100)
        cast = gcd4
        return (cast)

    def math_cast_taxed(self, action, player):
        fspd = math.floor(130 * (player.spell_speed - 380) / 3300 + 1000)
        gcd1 = math.floor((2000 - fspd) * action.cast_delay / 1000)
        if player.leylines_ON > 0:
            gcd2 = math.floor((100 - 15) * (100 - 0) / 100)
        else:
            gcd2 = math.floor((100 - 0) * (100 - 0) / 100)
        gcd3 = (100 - 0) / 100
        if player.stance == 3 and action.element == "ice":
            gcd4 = math.floor(math.floor(
                math.ceil(gcd2 * gcd3) * gcd1 / 100) * 50 / 100)
        elif player.stance == -3 and action.element == "fire":
            gcd4 = math.floor(math.floor(
                math.ceil(gcd2 * gcd3) * gcd1 / 100) * 50 / 100)
        else:
            gcd4 = math.floor(math.floor(
                math.ceil(gcd2 * gcd3) * gcd1 / 100) * 100 / 100)
        cast_taxed = gcd4 + action.tax
        return (cast_taxed)

    def math_recast(self, action, player):
        if action.gcd:
            fspd = math.floor(130 * (player.spell_speed - 380) / 3300 + 1000)
            gcd1 = math.floor((2000 - fspd) * action.recast_delay / 1000)
            if player.leylines_ON > 0:
                gcd2 = math.floor((100 - 15) * (100 - 0) / 100)
            else:
                gcd2 = math.floor((100 - 0) * (100 - 0) / 100)
            gcd3 = (100 - 0) / 100
            gcd4 = math.floor(math.floor(
                math.ceil(gcd2 * gcd3) * gcd1 / 100) * 100 / 100)
            recast = gcd4
            return (recast)
        else:
            recast = action.recast_delay
            return (recast)

    def math_mpcost(self, action, player):
        stance = dstance.get(player.stance)
        if action.name == "Despair":
            mp_cost = action.cost
        elif action.element == "ice":
            mp_cost = action.cost * stance.ice_cost
        elif action.element == "fire":
            mp_cost = action.cost * stance.fire_cost
        else:
            mp_cost = action.cost
        return(mp_cost)

    def math_damage(self, action, player):
        damage_dealt = damage(0, False, False)
        dhit_prob = math.floor(550 * (player.direct_hit - 380) / 3300) / 10
        crit_prob = math.floor(
            200 * (player.critical_hit - 380) / 3300 + 50) / 10
        fmattp = math.floor(165 * (player.mattp - 340) / 340) + 100
        fdet = math.floor(130 * (player.determination - 340) / 3300 + 1000)
        fwd = math.floor(340 * 115 / 1000 + 172)
        ftnc = 1000
        d1 = math.floor(math.floor(math.floor(
            action.potency * fmattp * fdet) / 100) / 1000)
        trait = 130
        d2 = math.floor(math.floor(math.floor(math.floor(math.floor(
            math.floor(d1 * ftnc) / 1000) * fwd) / 100) * trait) / 100)
        if random.random() <= dhit_prob / 100:
            dh = 125
            damage_dealt.dh = True
        else:
            dh = 100
        if random.random() <= crit_prob / 100:
            fcrit = math.floor(200 * (player.critical_hit - 380) / 3300 + 1400)
            damage_dealt.crit = True
        else:
            fcrit = 1000
        d3 = math.floor(math.floor(math.floor(
            math.floor(d2 * fcrit) / 1000) * dh) / 100)
        if player.enochan_ON > 0:
            buff1 = 1.15
        else:
            buff1 = 1
        stance = dstance.get(player.stance)
        if action.element == "ice":
            buff2 = stance.ice_damage
        elif action.element == "fire":
            buff2 = stance.fire_damage
        else:
            buff2 = 1
        damage_dealt.amount = math.floor(math.floor(math.floor(math.floor(
            d3 * random.uniform(95, 105)) / 100) * buff1) * buff2)
        return(damage_dealt)


# name, cast_delay, tax, recast_delay, potency, cost, element, gcd
b1 = blm_actions("Blizzard",     250, 10,  250, 180,  400, "ice",     True)
b2 = blm_actions("Blizzard II",  200, 10,  250,  50,  800, "ice",     True)
b3 = blm_actions("Blizzard III", 350, 10,  250, 240,  800, "ice",     True)
b4 = blm_actions("Blizzard IV",  280, 10,  250, 300,  800, "ice",     True)
f1 = blm_actions("Fire",         250, 10,  250, 180,  800, "fire",    True)
f2 = blm_actions("Fire II",      300, 10,  250,  80, 1500, "fire",    True)
f3 = blm_actions("Fire III",     350, 10,  250, 240, 2000, "fire",    True)
f4 = blm_actions("Fire IV",      280, 10,  250, 300,  800, "fire",    True)
sc = blm_actions("Scathe",         0, 10,  250, 100,  800, "neutral", True)
xe = blm_actions("Xenoglossy",     0, 10,  250, 750,    0, "neutral", True)
de = blm_actions("Despair",      300, 10,  250, 380,  800, "fire",    True)
en = blm_actions("Enochan",        0, 75, 3000,   0,    0, "neutral", False)


def do_something(player, game, dummy):
    action_used = random.choice(player.available_actions)
    if action_used is not None:
        mpcost = action_used.math_mpcost(action_used, player)
        if player.mp - mpcost < 0:
            return
        elif action_used.gcd:
            if player.gcd_cd > 0:
                return
            elif action_used.name == "Despair" and player.stance != 3 and not player.enochan_ON > 0:
                return
            elif action_used.name == "Xenoglossy" and not player.polyglot > 0:
                return
            elif action_used.name == "Foul" and not player.polyglot > 0:
                return
            elif action_used.name == "Fire IV" and player.stance != 3 and not player.enochan_ON > 0:
                return
            elif action_used.name == "Blizzard IV" and player.stance != -3 and not player.enochan_ON > 0:
                return
            else:
                print("\n" + "{:.2f}".format(game.milliseconds / 100).rjust(7) +
                      " You started casting " + action_used.name + ".")
                player.casting_status = action_used.math_cast(
                    action_used, player)
                player.gcd_cd = action_used.math_recast(action_used, player)
                player.cast_taxed = action_used.math_cast_taxed(
                    action_used, player)
                player.casting = action_used
                player.pending_mp = - mpcost
                dummy.pending_damage = action_used.math_damage(
                    action_used, player)
                if action_used.name == "Blizzard III":
                    player.pending_stance = -6
                elif action_used.name == "Fire III":
                    player.pending_stance = 6
                elif action_used.element == "fire" and player.stance >= 0:
                    player.pending_stance = 1
                elif action_used.element == "fire" and player.stance < 0:
                    player.pending_stance = -player.stance
                elif action_used.element == "ice" and player.stance <= 0:
                    player.pending_stance = -1
                elif action_used.element == "ice"and player.stance > 0:
                    player.pending_stance = -player.stance
        elif not action_used.gcd:
            if action_used.name == "Enochan" and abs(player.stance) != 3:
                return
            elif action_used == "Enochan":
                player.enochan_CD = action_used.math_recast(
                    action_used, player)
                player.cast_taxed = action_used.math_cast_taxed(
                    action_used, player)
                player.casting_status = action_used.math_cast(
                    action_used, player)
                player.pending_enochan = 15
    else:
        return


def apply_pending_values(player, game, dummy):
    if player.casting is not None:
        print("{:.2f}".format(game.milliseconds / 100).rjust(7) +
              " You finished casting " + player.casting.name + ".")
    player.casting = None
    player.mp += player.pending_mp
    if player.pending_mp != 0:
        print("{:.2f}".format(game.milliseconds / 100).rjust(7) +
              " You used " + str(int(player.pending_mp)) + " MP.")
    player.pending_mp = 0
    player.stance = max(min(player.stance + player.pending_stance, 3), -3)
    if player.pending_stance != 0:
        stance = dstance.get(player.stance)
        print("{:.2f}".format(game.milliseconds / 100).rjust(7) +
              " You are now in " + stance.name + ".")
    player.pending_stance = 0
    player.enochan_ON = min(player.enochan_ON + player.pending_enochan, 15)
    player.pending_enochan = 0
    if dummy.pending_damage is not None:
        dummy.damage_taken += dummy.pending_damage.amount
        print("{:.2f}".format(game.milliseconds / 100).rjust(7) +
              " The dummy takes " + str(dummy.pending_damage.amount) + " damage. Critical hit: " + str(dummy.pending_damage.crit) + "| Direct hit : " + str(dummy.pending_damage.dh))
        dummy.pending_damage = None


def clear_screen():
    os.system("cls")


def load_player():
    sps_build = {
        "Magic Attack Power": 4867,
        "Intelligence": 4867,
        "Direct Hit": 2974,
        "Critical Hit": 528,
        "Determination": 1915,
        "Spell Speed": 3761,
    }
    selected_build = sps_build
    return (player(selected_build.get("Magic Attack Power"), selected_build.get("Intelligence"), selected_build.get(
        "Direct Hit"), selected_build.get("Critical Hit"), selected_build.get("Determination"), selected_build.get("Spell Speed")))


def load_game():
    '''one_minute = {
        "Time limit": 6000,
    }'''
    reopener = {
        "Time limit": 69000,
    }
    selected_encounter = reopener
    return(game(selected_encounter.get("Time limit")))


def load_actions(player):
    player.available_actions = [b1, b2, b3, b4,
                                f1, f2, f3, f4, sc, xe, de, None, en]
    # player.available_actions = [b1, b2, b3, b4]


def main():
    clear_screen()
    current_player = load_player()
    current_game = load_game()
    target_dummy = dummy()
    load_actions(current_player)
    pygame.init()
    while not current_game.game_over:
        # pygame.time.delay(10)
        # uncomment line 404 to remove real time sim

        ''' Order of events:
            Game updates MP and Polyglot status
            If not casting + cast tax, then player may take an action
            Action effects and damage are calculated at the end of the cast
            game and player status are updated at the end of the cycle. game status only if in combat
        '''

        current_player.math_mpregen(current_player, current_game)
        current_player.math_polyglot(current_player, current_game)
        if current_player.cast_taxed > 0:
            None
        else:
            do_something(current_player, current_game, target_dummy)
        if current_player.casting_status is not None:
            # Add action being casted to player.casting, math values here instead of player.pending_X
            if current_player.casting_status == 0:
                apply_pending_values(
                    current_player, current_game, target_dummy)
        if target_dummy.damage_taken != 0:
            current_game.combat = True
        if current_game.combat:
            current_game.update_game(current_game, target_dummy)
        current_player.update_player(current_player)
    print("{:.2f}".format(current_game.milliseconds / 100).rjust(7) +
          " Your DPS is: " + "{:.2f}".format(target_dummy.damage_taken / current_game.milliseconds * 100))
    pygame.quit()


main()
