#!/usr/bin/env python

import simpy

from vppsim.entities import EV, VPP
from vppsim import loader

# PHYSICAL CONSTANTS
MAX_EV_CAPACITY = 16.5  # kWh
MAX_EV_RANGE = 20       # km
CHARGING_SPEED = 3.6    # 3.6 kWh per hour


def main():
    df = loader.load()
    sim_start_time = df.start_time.min()
    num_evs = len(df.EV.unique())

    env = simpy.Environment(sim_start_time)
    vpp = VPP(env, 1, num_evs)
    env.process(lifecycle(env, vpp, df))

    print('Starting Simulation...')
    env.run()


def lifecycle(env, vpp, df):
    evs = {}
    previous = df.iloc[0,:]

    for rental in df.itertuples():

        # Wait until next rental
        yield env.timeout(rental.start_time - previous.start_time)  # sec

        if rental.EV not in evs:
            print('\n ---------- NEW EV %d ----------' % rental.Index)
            evs[rental.EV] = EV(env, vpp, rental.EV, rental.start_soc)

        ev = evs[rental.EV]
        env.process(ev.drive(env, rental.Index, rental.trip_duration,
                             rental.start_soc - rental.end_soc,
                             rental.start_soc, rental.end_charging))
        previous = rental


if __name__ == '__main__':
    main()
