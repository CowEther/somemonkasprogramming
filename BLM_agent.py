from keras.optimizers import Adam
from keras.models import Sequential
from keras.layers.core import Dense, Dropout
import pandas
import numpy
import collections
import random


class DQNAgent(object):
    def __init__(self, params):
        self.reward = 0
        self.gamma = 0.9
        self.dataframe = pandas.DataFrame()
        self.short_memory = numpy.array([])
        self.agent_target = 1
        self.agent_predict = 0
        self.learning_rate = params['learning_rate']
        self.epsilon = 1
        self.actual = []
        self.first_layer = params['first_layer_size']
        self.second_layer = params['second_layer_size']
        self.third_layer = params['third_layer_size']
        self.memory = collections.deque(maxlen=params['memory_size'])
        self.weights = params['weights_path']
        self.load_weights = params['load_weights']
        self.model = self.network()

    def network(self):
        model = Sequential()
        model.add(Dense(output_dim=self.first_layer,
                        activation="relu", input_dim=30))
        model.add(Dense(units=self.second_layer, activation="relu",))
        model.add(Dense(units=self.third_layer, activation="relu",))
        model.add(Dense(units=24, activation="relu",))
        opt = Adam(self.learning_rate)
        model.compile(loss='mse', optimizer=opt)
        if self.load_weights:
            model.load_weights(self.weights)
        return model

    def get_state(self, game):
        state = [
            game.centiseconds,
            game.limit_centiseconds,

            game.player.character_tick,
            game.player.mp,
            game.player.umbral_heart,
            game.player.cast_time,
            game.player.cast_taxed,
            game.player.gcd_CD,
            game.player.swift,
            game.player.tripleC,
            game.player.enochan_ON,
            game.player.enochan_CD,
            game.player.leylines_ON,
            game.player.leylines_CD,
            game.player.triple_cast_ON,
            game.player.triple_cast_CD,
            game.player.swift_cast_ON,
            game.player.swift_cast_CD,
            game.player.manafont_ON,
            game.player.manafont_CD,
            game.player.transpose_ON,
            game.player.triple_cast_CD,
            game.player.stance,
            game.player.polyglot,
            game.player.polyglot_counter,
            game.player.astral_umbral,

            game.dummy.damage_taken,
            game.dummy.dots[0].duration,
            game.dummy.dots[1].duration,
            game.dummy.character_tick,
        ]

        return numpy.asarray(state)

    def set_reward(self, game):
        self.reward = game.dummy.damage_received
        game.dummy.damage_received = 0
        return self.reward

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def replay_new(self, memory, batch_size):
        if len(memory) > batch_size:
            minibatch = random.sample(memory, batch_size)
        else:
            minibatch = memory
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = reward + self.gamma * \
                    numpy.amax(self.model.predict(
                        numpy.array([next_state]))[0])
            target_f = self.model.predict(numpy.array([state]))
            target_f[0][numpy.argmax(action)] = target
            self.model.fit(numpy.array([state]),
                           target_f, epochs=1, verbose=0)

    def train_short_memory(self, state, action, reward, next_state, done):
        target = reward
        if not done:
            target = reward + self.gamma * \
                numpy.amax(self.model.predict(
                    next_state.reshape((1, 30)))[0])
        target_f = self.model.predict(state.reshape((1, 30)))
        target_f[0][numpy.argmax(action)] = target
        self.model.fit(state.reshape((1, 30)),
                       target_f, epochs=1, verbose=0)
