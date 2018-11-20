import logging
from datetime import datetime
import simpy

import vppsim


class VPP:
    def __init__(self, env, name, num_evs):
        self.logger = logging.getLogger('vppsim.vpp')

        self.capacity = simpy.Container(env, init=0, capacity=vppsim.MAX_EV_CAPACITY * num_evs)
        self.env = env
        self.name = name
        # self.mon_proc = env.process(self.monitor_capacity(env))

    def log(self, message):
        self.logger.info('[%s] - %s(%.2f/%.2f) %s' % (datetime.fromtimestamp(self.env.now),
                                                   self.name, self.capacity.level,
                                                   self.capacity.capacity, message))
        self.logger.info(self.capacity.put_queue)
        self.logger.info(self.capacity.get_queue)

    def monitor_capacity(self, env):
        while True:
            self.log('Capacity')
            yield env.timeout(10 * 60)
