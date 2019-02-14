from operator import attrgetter
from datetime import datetime
import logging

from evsim.data import loader


class Controller:
    def __init__(self, strategy):
        self.logger = logging.getLogger(__name__)

        self.intraday_prices = loader.load_intraday_prices()
        self.strategy = strategy

    def charge_fleet(self, env, fleet, timestep):
        """ Perform a charging operation on the fleet for a given timestep.
            Takes a a list of EVs as input and charges given its strategy.
        """

        self.strategy(env, self, fleet, timestep)

    def log(self, env, message):
        self.logger.info(
            "[%s] - %s(%s) %s"
            % (datetime.fromtimestamp(env.now), "Controller", "regular", message)
        )

    def dispatch(self, fleet, criteria, n):
        """Return n EVs from fleet according to ascending EV criteria"""
        s = sorted(fleet, key=attrgetter(criteria))
        return s[:n]
