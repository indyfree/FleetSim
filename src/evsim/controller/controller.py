from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def charge_fleet(env, fleet, timestep, strategy):
    log(env, strategy, "Charging %d EVs." % len(fleet))
    strategy(env, fleet, timestep)


def log(env, strategy, message):
    logger.info(
        "[%s] - %s(%s) %s"
        % (datetime.fromtimestamp(env.now), "Controller", strategy.__name__, message)
    )
