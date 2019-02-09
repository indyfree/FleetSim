def regular(env, fleet, timestep):
    '''
    Charge all EVs at regular prices
    '''
    for ev in fleet:
        ev.action = env.process(ev.charge_timestep(timestep))
