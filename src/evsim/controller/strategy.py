from . import controller


def regular(env, controller, fleet, timestep):
    ''' Charge all EVs at regular prices'''

    evs = controller.dispatch(fleet, criteria="battery.level", n=len(fleet) - 5)
    controller.log(env, "Charging %d EVs." % len(evs))
    controller.log(env, evs)

    for ev in evs:
        ev.action = env.process(ev.charge_timestep(timestep))
