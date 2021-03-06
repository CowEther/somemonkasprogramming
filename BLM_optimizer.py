import os
import random
import math
import time
from BLM_agent import DQNAgent
import keras
import sys
import numpy


def define_parameters():
    params = dict()
    params['epsilon_decay_linear'] = 1 / 75
    params['learning_rate'] = 0.0005
    params['first_layer_size'] = 150   # neurons in the first layer
    params['second_layer_size'] = 150   # neurons in the second layer
    params['third_layer_size'] = 150    # neurons in the third layer
    params['episodes'] = 100
    params['memory_size'] = 2500
    params['batch_size'] = 500
    params['weights_path'] = 'weights/weights.hdf5'
    params['load_weights'] = False
    params['train'] = True
    return params


class Game:
    def __init__(self, limit_centiseconds):
        self.centiseconds = 0
        self.game_over = False
        self.combat = False
        self.limit_centiseconds = limit_centiseconds[1]
        self.player = None
        self.dummy = None

    # updates game counters
    def update(self):
        if self.combat:
            self.centiseconds += 1
            self.limit_centiseconds = max(self.limit_centiseconds - 1, 0)
        if not self.limit_centiseconds:
            self.game_over = True
            self.combat = False


class Player:
    def __init__(self, intelligence, direct_hit, critical_hit, determination, spell_speed):
        self.intelligence = intelligence[1]
        self.direct_hit = direct_hit[1]
        self.critical_hit = critical_hit[1]
        self.determination = determination[1]
        self.spell_speed = spell_speed[1]

        # Game is fetching actions and Umbral/Astral info from here
        self.available_actions = None
        self.stances = None

        self.character_tick = random.randint(0, 300)
        self.mp = 10000
        self.umbral_heart = 0

        # Casting system
        self.casting = None  # action being casted
        self.cast_time = 0  # effects are applied after this time has elapsed
        self.cast_taxed = 0  # actions maybe only be taken after this time has elapsed
        self.gcd_CD = 0  # every GCD bound action will trigger this timer.
        self.swift = 0  # swift cast instants left
        self.tripleC = 0  # triple cast instants left

        # oGCDs and others : ON is the duration, CD is the cooldown
        self.enochan_ON = False
        self.enochan_CD = 0
        self.leylines_CD = 0
        self.leylines_ON = 0
        self.triple_cast_ON = 0
        self.triple_cast_CD = 0
        self.swift_cast_ON = 0
        self.swift_cast_CD = 0
        self.sharpcast_ON = 0
        self.sharpcast_CD = 0
        self.manafont_ON = 0
        self.manafont_CD = 0
        self.transpose_ON = 0
        self.transpose_CD = 0

        # Gauge info
        self.stance = 0  # < 0 is Umbral Ice, > 0  Astral fire, 0 is neutral
        self.polyglot = 0  # amount of polyglot stacks
        self.polyglot_counter = 0  # tracks every 30seconds
        self.astral_umbral = 0

    # calculates MP tick at server tick and updates player if stance allows
    def math_mp_tick(self, game):
        mp_per_tick = 200  # base regen
        mp_mod = self.stances.get(self.stance).mp_mod
        if self.character_tick == 300:
            self.character_tick = 0
            self.mp = min(mp_per_tick * mp_mod + self.mp, 10000)
            # if mp_per_tick * mp_mod:
            # print("%6.2f You gain %d MP." % (game.centiseconds / 100, mp_per_tick * mp_mod))

            # adds 1 polyglot every 30s of active enochan
    def math_polyglot(self, game):
        if self.polyglot_counter == 3000:
            self.polyglot_counter = 0
            self.polyglot = min(self.polyglot + 1, 2)
            # print("%6.2f You gain a polyglot stack MP." % (game.centiseconds / 100))

    # updates every player counters
    def update(self):
        self.character_tick = min(self.character_tick + 1, 300)

        self.cast_time = max(self.cast_time - 1, 0)
        self.cast_taxed = max(self.cast_taxed - 1, 0)
        self.gcd_CD = max(self.gcd_CD - 1, 0)

        self.astral_umbral = max(self.astral_umbral - 1, 0)
        if not self.astral_umbral:
            self.stance = 0

        if not self.stance:  # if not in a stance, enochan is lost
            self.enochan_ON = False
        self.enochan_CD = max(self.enochan_CD - 1, 0)
        self.leylines_ON = max(self.leylines_ON - 1, 0)
        self.leylines_CD = max(self.leylines_CD - 1, 0)
        self.triple_cast_ON = max(self.triple_cast_ON - 1, 0)
        self.triple_cast_CD = max(self.triple_cast_CD - 1, 0)
        self.swift_cast_ON = max(self.swift_cast_ON - 1, 0)
        self.swift_cast_CD = max(self.swift_cast_CD - 1, 0)
        self.sharpcast_ON = max(self.sharpcast_ON - 1, 0)
        self.sharpcast_CD = max(self.sharpcast_CD - 1, 0)
        self.manafont_ON = max(self.manafont_ON - 1, 0)
        self.manafont_CD = max(self.manafont_CD - 1, 0)
        self.transpose_ON = max(self.transpose_ON - 1, 0)
        self.transpose_CD = max(self.transpose_CD - 1, 0)

        if self.enochan_ON:
            self.polyglot_counter = min(self.polyglot_counter + 1, 3000)
        else:
            self.polyglot_counter = 0
            self.umbral_heart = 0


class Dummy:
    def __init__(self):
        self.damage_taken = 0
        self.damage_received = 0

        self.dots = None
        self.character_tick = random.randint(0, 300)

    def update(self):
        self.character_tick = min(self.character_tick + 1, 300)
        for dot in self.dots:
            dot.active_time = max(dot.active_time - 1, 0)

    # calculated any dot's per tick damage in the dummy.dots list IF they have any duration left when they meet the server tick
    def math_DoTs(self, game, player):
        if self.character_tick == 300:
            self.character_tick = 0
            for dot in self.dots:
                if dot.active_time:
                    dhit_prob = math.floor(
                        550 * (player.direct_hit - 380) / 3300) / 10
                    crit_prob = math.floor(
                        200 * (player.critical_hit - 380) / 3300 + 50) / 10
                    fmattp = math.floor(
                        165 * (player.intelligence - 340) / 340) + 100
                    fdet = math.floor(
                        130 * (player.determination - 340) / 3300 + 1000)
                    fwd = math.floor(340 * 115 / 1000 + 172)
                    ftnc = 1000
                    fspd = math.floor(
                        130 * (player.spell_speed - 380) / 3300 + 1000)
                    d1 = math.floor(math.floor(math.floor(math.floor(math.floor(
                        math.floor(dot.potency * fwd) / 100) * fmattp) / 100) * fspd) / 1000)
                    d2 = math.floor(math.floor(math.floor(math.floor(math.floor(
                        math.floor(d1 * fdet) / 1000) * ftnc) / 1000) * 130) / 100) + 1
                    d3 = math.floor(math.floor(
                        d2 * random.uniform(95, 105)) / 100)
                    if random.random() <= dhit_prob / 100:
                        dh = 125
                    else:
                        dh = 100
                    if random.random() <= crit_prob / 100:
                        fcrit = math.floor(
                            200 * (player.critical_hit - 380) / 3300 + 1400)
                    else:
                        fcrit = 1000
                    damage = math.floor(math.floor(math.floor(math.floor(
                        math.floor(d3 * fcrit) / 1000) * dh) / 100) * dot.buff1)
                    self.damage_taken += damage
                    # print("%6.2f The dummy takes %d damage from %s." % (game.centiseconds / 100, damage, dot.name))


# Umbral Ice and Astral Fire class
class Stance:
    def __init__(self, fire_cost_mod, fire_dmg_mod, ice_cost_mod, ice_dmg_mod, mp_mod, stance_name):
        self.stance_name = stance_name
        self.fire_cost_mod = fire_cost_mod
        self.fire_dmg_mod = fire_dmg_mod
        self.ice_cost_mod = ice_cost_mod
        self.ice_dmg_mod = ice_dmg_mod
        self.mp_mod = mp_mod


class GCDs:
    def __init__(self, cast_delay, recast_delay, potency, cost, element, name):
        self.name = name
        self.cast_delay = cast_delay
        self.recast_delay = recast_delay
        self.potency = potency
        self.cost = cost
        self.element = element
        self.tax = 10

    # calculation of casting time and cast taxed
    # buff1 is enochan, buff2 is the speed bonus from swapping element
    def math_cast(self, player):
        fspd = math.floor(130 * (player.spell_speed - 380) / 3300 + 1000)
        gcd1 = math.floor((2000 - fspd) * self.cast_delay / 1000)
        if player.leylines_ON > 0:
            buff1 = 15
        else:
            buff1 = 0
        gcd2 = math.floor((100 - buff1) * (100 - 0) / 100)
        gcd3 = (100 - 0) / 100
        if player.stance == 3 and self.element == "ice":
            buff2 = 50
        elif player.stance == -3 and self.element == "fire":
            buff2 = 50
        else:
            buff2 = 100
        cast = math.floor(math.floor(math.ceil(gcd2 * gcd3) *
                                     gcd1 / 100) * buff2 / 100)
        if player.swift:  # 75 centiseconds is the instant cast tax
            player.swift = max(player.swift - 1, 0)
            player.cast_time = 0
            player.cast_taxed = 75
        elif player.tripleC:
            player.tripleC = max(player.tripleC - 1, 0)
            player.cast_time = 0
            player.cast_taxed = 75
        else:
            player.cast_time = cast
            player.cast_taxed = cast + self.tax

    # buff1 is enochan
    def math_GCD_CD(self, player):
        fspd = math.floor(130 * (player.spell_speed - 380) / 3300 + 1000)
        gcd1 = math.floor((2000 - fspd) * self.recast_delay / 1000)
        if player.leylines_ON > 0:
            buff1 = 15
        else:
            buff1 = 0
        gcd2 = math.floor((100 - buff1) * (100 - 0) / 100)
        gcd3 = (100 - 0) / 100
        recast = math.floor(math.ceil(gcd2 * gcd3) * gcd1 / 100)
        player.gcd_CD = recast

        # Flare and Despair take all the MP. Returns False if player can't afford it. Otherwise depletes MP
    def math_mpcost(self, player):
        stance = player.stances.get(player.stance)
        if self.name == "Despair" and player.mp > self.cost:
            mp_cost = player.mp
        elif self.name == "Despair" and player.mp < self.cost:
            return(False)
        elif self.name == "Flare" and player.mp > self.cost:  # Umbral heart on flare reduces the cast by a 3rd but I only observe round values of MP meaning it's not really 1/3.... in game observation leans me toward the below formula
            if player.umbral_heart:
                mp_cost = math.ceil((player.mp / 3) / 100 + 1) * 100
            else:
                mp_cost = player.mp
        elif self.name == "Flare" and player.mp < self.cost:
            return(False)
        elif self.element == "ice":
            mp_cost = self.cost * stance.ice_cost_mod
        # TODO MP is only removed at the end of the cast. see finish_casting function in case of interrupts.
        elif self.element == "fire":
            if player.umbral_heart and player.stance > 0:
                mp_cost = self.cost
            else:
                mp_cost = self.cost * stance.fire_cost_mod
        else:
            mp_cost = self.cost
        if player.mp - mp_cost < 0:
            return(False)
        else:
            player.mp - mp_cost
            return(True)

    def math_damage(self, game, player, dummy):
        dhit_prob = math.floor(550 * (player.direct_hit - 380) / 3300) / 10
        crit_prob = math.floor(
            200 * (player.critical_hit - 380) / 3300 + 50) / 10
        fmattp = math.floor(165 * (player.intelligence - 340) / 340) + 100
        fdet = math.floor(130 * (player.determination - 340) / 3300 + 1000)
        fwd = math.floor(340 * 115 / 1000 + 172)
        ftnc = 1000
        d1 = math.floor(math.floor(math.floor(
            self.potency * fmattp * fdet) / 100) / 1000)
        trait = 130
        d2 = math.floor(math.floor(math.floor(math.floor(math.floor(
            math.floor(d1 * ftnc) / 1000) * fwd) / 100) * trait) / 100)
        if random.random() <= dhit_prob / 100:
            dh = 125
        else:
            dh = 100
        if random.random() <= crit_prob / 100:
            fcrit = math.floor(200 * (player.critical_hit - 380) / 3300 + 1400)
        else:
            fcrit = 1000
        d3 = math.floor(math.floor(math.floor(
            math.floor(d2 * fcrit) / 1000) * dh) / 100)
        if player.enochan_ON:
            buff1 = 1.15
        else:
            buff1 = 1
        stance = player.stances.get(player.stance)
        # elemental stance damage modifiers being applied here
        if self.element == "ice":
            buff2 = stance.ice_dmg_mod
        elif self.element == "fire":
            buff2 = stance.fire_dmg_mod
        else:
            buff2 = 1
        damage_dealt = math.floor(math.floor(math.floor(math.floor(
            d3 * random.uniform(95, 105)) / 100) * buff1) * buff2)
        dummy.damage_taken += damage_dealt
        dummy.damage_received = damage_dealt
        # print("%6.2f The dummy takes %d damage from %s." % (game.centiseconds / 100, damage_dealt, self.name))


class oGCDs:
    def __init__(self, duration, recast_delay, name):
        self.name = name
        self.duration = duration
        self.cast_delay = 75
        self.recast_delay = recast_delay

    def math_cast(self, player):
        player.cast_taxed = self.cast_delay

    def math_CD(self,):
        return(self.recast_delay)


class DoTs:
    def __init__(self, potency, duration, name):
        self.name = name
        self.potency = potency
        self.duration = duration
        self.active_time = 0
        self.buff1 = 1


# initialize classes and player stance/actions
def initialize():

    game = Game(("Time limit", 39000))

    game.player = Player(("Intelligence", 4867), ("Direct_Hit", 2974),
                         ("Critical Hit", 528), ("Determination", 1915), ("Spell Speed", 3761))
    game.dummy = Dummy()

    # fire_cost, fire_damage, ice_cost, ice_damage, mp_mod, name
    stanced0 = Stance(1, 1, 1, 1, 1, "Neutral Stance")
    stancef1 = Stance(2, 1.4, 0.5, 0.9, 0, "Astral Fire I")
    stancef2 = Stance(2, 1.6, 0.25, 0.8, 0, "Astral Fire II")
    stancef3 = Stance(2, 1.8, 0, 0.7, 0, "Astral Fire III")
    stanceb1 = Stance(0.5, 0.9, 0.75, 1, 16, "Umbral Ice I")
    stanceb2 = Stance(0.25, 0.8, 0.5, 1, 23.5, "Umbral Ice II")
    stanceb3 = Stance(0, 0.7, 0, 1, 31, "Umbral Ice III")
    game.player.stances = {
        0: stanced0,
        1: stancef1,
        2: stancef2,
        3: stancef3,
        -1: stanceb1,
        -2: stanceb2,
        -3: stanceb3,
    }

    # cast_delay, recast_delay, potency, cost, element, name
    b1 = GCDs(250, 250, 180, 400, "ice", "Blizzard I")
    b2 = GCDs(200, 250, 50, 800, "ice", "Blizzard II")
    b3 = GCDs(350, 250, 240, 800, "ice", "Blizzard III")
    b4 = GCDs(280, 250, 300, 800, "ice", "Blizzard IV")
    f1 = GCDs(250, 250, 180, 800, "fire", "Fire I")
    f2 = GCDs(300, 250, 80, 1500, "fire", "Fire II")
    f3 = GCDs(350, 250, 240, 2000, "fire", "Fire III")
    f4 = GCDs(280, 250, 300, 800, "fire", "Fire IV")
    sc = GCDs(0, 250, 100, 800, "neutral", "Scathe")
    xe = GCDs(0, 250, 750, 0, "neutral", "Xenoglossy")
    fo = GCDs(250, 250, 650, 0, "neutral", "Foul")
    de = GCDs(300, 250, 380, 800, "fire", "Despair")
    t3 = GCDs(250, 250, 70, 400, "neutral", "Thunder III")
    t4 = GCDs(250, 250, 50, 800, "neutral", "Thunder IV")
    fl = GCDs(400, 250, 260, 800, "fire", "Flare")
    fr = GCDs(250, 250, 100, 1000, "ice", "Freeze")
    us = GCDs(0, 250, 0, 0, "ice", "Umbral Soul")

    # duration, recast_delay, name
    tr = oGCDs(0, 500, "Transpose")
    ma = oGCDs(0, 18000, "Manafont")
    ll = oGCDs(3000, 9000, "Ley Lines")
    en = oGCDs(0, 3000, "Enochan")
    tc = oGCDs(1500, 6000, "Triple Cast")
    sw = oGCDs(1000, 6000, "Swift Cast")

    # TODO thunder procs, IV and III, sharpcast

    # potency, duration, name
    t3_dot = DoTs(40, 2400, "Thunder III")
    t4_dot = DoTs(30, 1800, "Thunder IV")

    game.player.available_actions = [
        b1, b2, b3, b4, f1, f2, f3, f4, sc, xe, fo, de, t3, t4, fl, None, fr, us, tr, ma, ll, en, tc, sw]
    game.dummy.dots = [t3_dot, t4_dot]

    return(game)


# wastes 1 centisecond if attempting to do an action that cannot be used atm
def do_something(final_move, game):
    index = numpy.where(final_move == 1)[0][0]
    action_used = game.player.available_actions[index]
    if action_used is not None:
        if type(action_used) is GCDs:
            if action_used.math_mpcost(game.player) and not game.player.gcd_CD:
                if action_used.name == "Despair" and (game.player.stance != 3 or not game.player.enochan_ON):
                    game.player.cast_taxed = 75
                elif action_used.name == "Xenoglossy" and not game.player.polyglot > 0:
                    game.player.cast_taxed = 75
                elif action_used.name == "Foul" and not game.player.polyglot > 0:
                    game.player.cast_taxed = 75
                elif action_used.name == "Fire IV" and (game.player.stance != 3 or not game.player.enochan_ON):
                    game.player.cast_taxed = 75
                elif action_used.name == "Blizzard IV" and (game.player.stance != -3 or not game.player.enochan_ON):
                    game.player.cast_taxed = 75
                elif action_used.name == "Umbral Soul" and (not game.player.enochan_ON or not game.player.stance < 0):
                    game.player.cast_taxed = 75
                else:
                    # print("")
                    game.player.casting = action_used
                    action_used.math_cast(game.player)
                    action_used.math_GCD_CD(game.player)
                    # print("%6.2f You started casting %s." % (game.centiseconds / 100, action_used.name))
            else:
                game.player.cast_taxed = 75

        elif type(action_used) is oGCDs:
            if action_used.name == "Transpose":
                if game.player.transpose_CD:
                    game.player.cast_taxed = 75
                else:
                    action_used.math_cast(game.player)
                    game.player.transpose_CD = action_used.math_CD()
                    game.player.casting = action_used
            elif action_used.name == "Manafont":
                if game.player.manafont_CD:
                    game.player.cast_taxed = 75
                else:
                    action_used.math_cast(game.player)
                    game.player.manafont_CD = action_used.math_CD()
                    game.player.casting = action_used
            elif action_used.name == "Ley Lines":
                if game.player.leylines_CD:
                    game.player.cast_taxed = 75
                else:
                    action_used.math_cast(game.player)
                    game.player.leylines_CD = action_used.math_CD()
                    game.player.leylines_ON = action_used.duration
                    game.player.casting = action_used
            elif action_used.name == "Enochan":
                if game.player.enochan_CD:
                    game.player.cast_taxed = 75
                else:
                    action_used.math_cast(game.player)
                    game.player.enochan_CD = action_used.math_CD()
                    game.player.casting = action_used
            elif action_used.name == "Triple Cast":
                if game.player.triple_cast_CD:
                    game.player.cast_taxed = 75
                else:
                    action_used.math_cast(game.player)
                    game.player.triple_cast_CD = action_used.math_CD()
                    game.player.triple_cast_ON = action_used.duration
                    game.player.casting = action_used
            elif action_used.name == "Swift Cast":
                if game.player.swift_cast_CD:
                    game.player.cast_taxed = 75
                else:
                    action_used.math_cast(game.player)
                    game.player.swift_cast_CD = action_used.math_CD()
                    game.player.swift_cast_ON = action_used.duration
                    game.player.casting = action_used
        elif action_used is None:
            game.player.cast_taxed = 75
        # print("%6.2f You started casting %s." % (game.centiseconds / 100, action_used.name))


# Applies effects of the cast
def finish_casting(game):
    if type(game.player.casting) is GCDs:
        game.player.casting.math_damage(game, game.player, game.dummy)
        if game.player.casting.name == "Flare":
            game.player.stance = 3
            game.player.astral_umbral = 1500
            game.player.umbral_heart = 0
        elif game.player.casting.name == "Blizzard III":
            game.player.stance = -3
            game.player.astral_umbral = 1500
        elif game.player.casting.name == "Fire III":
            game.player.stance = 3
            game.player.astral_umbral = 1500
        elif game.player.casting.name == "Foul" or game.player.casting.name == "Xenoglossy":
            game.player.polyglot -= 1
        elif game.player.casting.name == "Blizzard IV":
            game.player.umbral_heart = 3
        elif game.player.casting.name == "Umbral Soul":
            game.player.stance = max(game.player.stance - 1, -3)
            game.player.umbral_heart = min(game.player.umbral_heart + 1, 3)
            game.player.astral_umbral = 1500
        elif game.player.casting.name == "Freeze":
            game.player.stance = -3
            if not game.player.umbral_heart > 1:
                game.player.umbral_heart = 1
            game.player.astral_umbral = 1500
        elif game.player.casting.name == "Thunder III":  # Dot refresh/apply and snapshot instructions are here
            index = 0
            for dot in game.dummy.dots:
                if dot.name == "Thunder III":
                    break
                else:
                    index += 1
            game.dummy.dots[index].active_time = game.dummy.dots[index].duration
            if game.player.enochan_ON:
                buff1 = 1.15
            else:
                buff1 = 1
            game.dummy.dots[index].buff1 = buff1
        elif game.player.casting.name == "Thunder IV":
            index = 0
            for dot in game.dummy.dots:
                if dot.name == "Thunder IV":
                    break
                else:
                    index += 1
            game.dummy.dots[index].active_time = game.dummy.dots[index].duration
            if game.player.enochan_ON:
                buff1 = 1.15
            else:
                buff1 = 1
            game.dummy.dots[index].buff1 = buff1
        elif game.player.casting.element == "fire" and game.player.stance >= 0:
            game.player.stance = min(game.player.stance + 1, 3)
            game.player.umbral_heart = max(game.player.umbral_heart - 1, 0)
            if game.player.casting.name != "Fire IV":
                game.player.astral_umbral = 1500
        elif game.player.casting.element == "ice" and game.player.stance <= 0:
            game.player.stance = max(game.player.stance - 1, -3)
            game.player.astral_umbral = 1500
        elif game.player.casting.element == "fire" and not game.player.stance >= 0:
            game.player.stance = 0
            game.player.astral_umbral = 0
            # print("%6.2f You lose the effect of Umbral Ice" % (game.centiseconds / 100))
        elif game.player.casting.element == "ice" and not game.player.stance <= 0:
            game.player.stance = 0
            game.player.astral_umbral = 0
            # print("%6.2f You lose the effect of Astral Fire" % (game.centiseconds / 100))

    elif type(game.player.casting) is oGCDs:
        if game.player.casting.name == "Transpose":
            if game.player.stance > 0:
                game.player.stance = -1
                game.player.astral_umbral = 1500
            elif game.player.stance < 0:
                game.player.stance = 1
                game.player.astral_umbral = 1500
            # print("%6.2f You gain the effect of Transpose" % (game.centiseconds / 100))
        elif game.player.casting.name == "Manafont":
            game.player.mp = min(game.player.mp + 3000, 10000)
            # print("%6.2f You gain 3000 MP." % (game.centiseconds / 100))
        elif game.player.casting.name == "Enochan":
            game.player.enochan_ON = True
            # print("%6.2f You gain the effect of Enochian." % (game.centiseconds / 100))
        elif game.player.casting.name == "Triple Cast":
            game.player.tripleC = 3
            # print("%6.2f You gain the effect of Triple Cast." % (game.centiseconds / 100))
        elif game.player.casting.name == "Swift Cast":
            game.player.swift = 1
            # print("%6.2f You gain the effect of Swift Cast." % (game.centiseconds / 100))
    # print("%6.2f You finished casting %s." % (game.centiseconds / 100, game.player.casting.name))
    game.player.casting = None


# TODO check for interrupts

def main():

    counter_games = 0
    record = 0

    params = define_parameters()
    agent = DQNAgent(params)
    weights_filepath = params['weights_path']
    if params['load_weights']:
        agent.model.load_weights(weights_filepath)
        # print("weights loaded")

    while counter_games < params['episodes']:
        game = initialize()
        while not game.game_over:
            # time.sleep(.01)
            # Comment above line to remove real time sim

            if not params['train']:
                agent.epsilon = 0
            else:
                # agent.epsilon is set to give randomness to actions
                agent.epsilon = 1 - \
                    (counter_games * params['epsilon_decay_linear'])

            if game.dummy.damage_taken:
                game.combat = True

            game.player.math_mp_tick(game)
            game.player.math_polyglot(game)
            game.dummy.math_DoTs(game, game.player)

            if game.player.cast_taxed:
                None
            else:

                # get old state
                state_old = agent.get_state(game)

                if random.randint(0, 1) < agent.epsilon:
                    final_move = keras.utils.to_categorical(
                        random.randint(0, 23), num_classes=24)
                else:
                    # predict action based on the old state
                    prediction = agent.model.predict(
                        state_old.reshape((1, 30)))
                    final_move = keras.utils.to_categorical(
                        numpy.argmax(prediction[0]), num_classes=24)
                do_something(final_move, game)
            if game.player.cast_time == 0 and game.player.casting is not None:
                finish_casting(game)
                state_new = agent.get_state(game)
                reward = agent.set_reward(game)
                if params['train']:
                    # train short memory base on the new action and state
                    # state, action, reward, next_state, done
                    agent.train_short_memory(
                        state_old, final_move, reward, state_new, game.game_over)
                    # store the new data into a long term memory
                    agent.remember(state_old, final_move,
                                   reward, state_new, game.game_over)

            game.update()
            game.player.update()
            game.dummy.update()

        if params['train']:
            agent.replay_new(agent.memory, params['batch_size'])
        if params['train']:
            agent.model.save_weights(params['weights_path'])
        counter_games += 1
        dps = game.dummy.damage_taken / game.centiseconds * 100
        if dps > record:
            record = dps
        print("Current amount of games is : %3d    Current record is: %.2f" %
              (counter_games, record))


if __name__ == '__main__':
    main()
