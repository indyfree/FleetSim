from operator import attrgetter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def charge_fleet(env, fleet, timestep, strategy):
    """
        Perform a charging operation on the fleet for a given timestep.
        Takes a charging strategy and a list of EVs as input.
    """

    strategy(env, fleet, timestep)


def log(env, message):
    logger.info(
        "[%s] - %s(%s) %s"
        % (datetime.fromtimestamp(env.now), "Controller", "regular", message)
    )


def dispatch(env, fleet, n):
    s = sorted(fleet, key=attrgetter("battery.level"))
    return s[:n]
