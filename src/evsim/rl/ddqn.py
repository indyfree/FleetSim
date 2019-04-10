import numpy as np

from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten
from keras.optimizers import Adam

from rl.agents.dqn import DQNAgent
from rl.policy import LinearAnnealedPolicy, EpsGreedyQPolicy, BoltzmannQPolicy

from rl.callbacks import FileLogger

from rl.memory import SequentialMemory


class DDQN:
    def __init__(self, env):
        # Get the environment and extract the number of actions.
        self.env = env

        self.log_filename = "./logs/dqn_{}_log.json".format(self.env.spec.id)
        self.weights_filename = "./results/dqn_{}_weights.h5f".format(self.env.spec.id)

        # self.env.seed(123)
        np.random.seed(123)

        nb_actions = self.env.action_space.n
        nb_states = self.env.observation_space.shape

        # Next, we build a very simple model.
        model = self._build_nn(nb_states, nb_actions)

        memory = SequentialMemory(limit=50000, window_length=1)

        # policy = BoltzmannQPolicy()
        policy = LinearAnnealedPolicy(
            EpsGreedyQPolicy(),
            attr="eps",
            value_max=1.0,
            value_min=0.1,
            value_test=0.1,
            nb_steps=40000,
        )

        # Configure and compile our agent:
        # You can use every built-in Keras optimizer and even the metrics!
        self.dqn = DQNAgent(
            model=model,
            nb_actions=nb_actions,
            memory=memory,
            nb_steps_warmup=100,
            target_model_update=1e-2,
            policy=policy,
        )
        self.dqn.compile(Adam(lr=1e-2), metrics=["mae"])

    def _build_nn(self, nb_states, nb_actions):
        model = Sequential()
        model.add(Flatten(input_shape=(1,) + nb_states))
        model.add(Dense(16))
        model.add(Activation("relu"))
        model.add(Dense(16))
        model.add(Activation("relu"))
        model.add(Dense(16))
        model.add(Activation("relu"))
        model.add(Dense(nb_actions))
        model.add(Activation("linear"))
        return model

    def run(self, steps):
        callbacks = [FileLogger(self.log_filename, interval=10)]
        self.dqn.fit(
            self.env,
            callbacks=callbacks,
            nb_steps=steps,
            visualize=False,
            verbose=2,
            log_interval=1000,
        )
        # After training is done, we save the final weights.
        self.dqn.save_weights(self.weights_filename, overwrite=True)

    def test(self):
        self.dqn.load_weights(self.weights_filename)
        self.dqn.test(self.env, nb_episodes=1, visualize=False)
        self.env.save_results("./results/sim_result_ep_{}.csv".format("test"))
