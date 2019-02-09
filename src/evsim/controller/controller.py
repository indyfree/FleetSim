import logging

logger = logging.getLogger(__name__)


def charge_fleet(env, fleet, timestep, strategy):
    logger.info("Charging %d EVs" % len(fleet))
    strategy(env, fleet, timestep)
