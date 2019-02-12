from . import controller


def regular(env, fleet, timestep):
    '''
    Charge all EVs at regular prices
    '''

    evs = controller.dispatch(env, fleet, len(fleet))
    controller.log(env, "Charging %d EVs." % len(evs))
    controller.log(env, evs)

    for ev in evs:
        ev.action = env.process(ev.charge_timestep(timestep))
