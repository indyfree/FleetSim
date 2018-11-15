#!/usr/bin/env python

import simpy

from vppsim.entities import EV, VPP
from vppsim import loader

# SIMULATION CONSTANTS
MAX_EV_CAPACITY = 16.5  # kWh
MAX_EV_RANGE = 20       # km
CHARGING_SPEED = 3.6    # 3.6 kWh per hour
RUNTIME = 2000
NUM_EVS = 1

# PHYSICAL CONSTANTS
MAX_EV_CAPACITY = 16.5  # kWh
MAX_EV_RANGE = 20       # km
CHARGING_SPEED = 3.6    # 3.6 kWh per hour


def main():
    df = loader.load()

    env = simpy.Environment(df.start_time.min())
    vpp = VPP(env, 1, NUM_EVS)
    env.process(lifecycle(env, vpp, df))
    print('Starting Simulation...')
    env.run()


def lifecycle(env, vpp, df):

    evs = {}

    prev_time = df.start_time.min()

    # TODO: Use itetuples for speed improvement
    for i, rental in df.iterrows():

        yield env.timeout(rental.start_time - prev_time)  # sec

        print('\n ---------- RENTAL %d ----------' % i)
        if rental.EV not in evs:
            print('%s has been added to the fleet' % rental.EV)
            evs[rental.EV] = EV(env, vpp, rental.EV, rental.start_soc)

        ev = evs[rental.EV]

        yield env.process(ev.drive(env, rental.trip_duration,
                                   (rental.start_soc - rental.end_soc) * MAX_EV_CAPACITY / 100))

        if ev.action.triggered:
            if bool(rental.end_charging):
                ev.action = env.process(ev.charge(env))
            else:
                ev.action = env.process(ev.idle(env))


if __name__ == '__main__':
    main()
