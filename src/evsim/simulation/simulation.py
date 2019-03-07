from datetime import datetime
import logging
import numpy as np
import pandas as pd
import simpy

from evsim.controller import Controller
from evsim import data, entities

logger = logging.getLogger(__name__)


class Simulation:
    def __init__(
        self, name, charging_speed, ev_capacity, industry_tariff, strategy, save
    ):

        self.name = name
        self.charging_speed = charging_speed
        self.ev_capacity = ev_capacity
        self.industry_tariff = industry_tariff
        self.save = save

        self.controller = Controller(strategy, ev_capacity, industry_tariff)

    def start(self):
        df = data.load_car2go_trips(False)
        stats = list() if self.save else None

        env = simpy.Environment(initial_time=df.start_time.min())
        vpp = entities.VPP(
            env,
            "BALANCING",
            num_evs=len(df.EV.unique()),
            charger_capacity=self.charging_speed,
        )

        logger.info("---- STARTING SIMULATION: %s -----" % self.name)
        env.process(self.lifecycle(env, vpp, df, stats))
        env.run(until=df.end_time.max())

        if self.save:
            self.save_stats(
                stats,
                "./logs/stats-%s.csv" % self.name,
                datetime.fromtimestamp(env.now),
            )

    def lifecycle(self, env, vpp, df, stats):
        evs = {}

        # Timerange from start to end in 5 minute intervals
        # https://stackoverflow.com/a/15204235
        timeslots = (
            pd.date_range(
                datetime.utcfromtimestamp(df.start_time.min()),
                datetime.utcfromtimestamp(df.end_time.max()),
                freq="5min",
            ).astype(np.int64)
            // 10 ** 9
        )
        t0 = timeslots[0]
        for t in timeslots:
            # 1. Wait or don't time till next rental
            yield env.timeout(t - t0)  # sec
            logger.info(
                "[%s] - ---------- TIMESLOT %s ----------"
                % (datetime.fromtimestamp(env.now), datetime.fromtimestamp(env.now))
            )

            # 2. Find trips at the timeslot
            trips = df.loc[df["start_time"] == t]
            for trip in trips.itertuples():

                # 3. Add new EVs to Fleet
                if trip.EV not in evs:
                    evs[trip.EV] = entities.EV(
                        env,
                        vpp,
                        trip.EV,
                        trip.start_soc,
                        self.ev_capacity,
                        self.charging_speed,
                    )

                # 4. Start trip with EV
                ev = evs[trip.EV]
                env.process(
                    ev.drive(
                        trip.Index,
                        trip.trip_duration,  # Arrive before starting again
                        trip.start_soc - trip.end_soc,
                        trip.end_charging,
                    )
                )

            # 5. TODO: Centrally control charging
            self.controller.charge_fleet(
                env, vpp.evs.values(), self.industry_tariff, timestep=5
            )

            # 6. Save stats at each trip if enabled
            if stats is not None:
                stats.append(
                    [
                        datetime.fromtimestamp(env.now).replace(
                            second=0, microsecond=0
                        ),
                        int(len(evs)),
                        round(self._fleet_soc(evs), 2),
                        int(len(vpp.evs)),
                        round(vpp.avg_soc(), 2),
                        round(vpp.capacity(), 2),
                    ]
                )

            t0 = t

    def _fleet_soc(self, evs):
        soc = 0
        for ev in evs.values():
            soc += ev.battery.level

        return round(soc / len(evs), 2)

    def save_stats(self, stats, filename, timestamp):
        df_stats = pd.DataFrame(
            data=stats,
            columns=[
                "timestamp",
                "fleet",
                "fleet_soc",
                "ev_vpp",
                "vpp_soc",
                "vpp_capacity_kw",
            ],
        )
        df_stats = df_stats.groupby("timestamp").last()
        df_stats = df_stats.reset_index()
        df_stats.to_csv(filename, index=False)
        df_stats.to_csv("./logs/stats.csv", index=False)
