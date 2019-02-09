import logging

logger = logging.getLogger(__name__)

def dispatch_charging(env, vpp):
    logger.info("Dispatch charging: %s" % vpp.evs.keys())
    for _, ev in vpp.evs.items():
        ev.action = env.process(ev.charge_timestep(5))
