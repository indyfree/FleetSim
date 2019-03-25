from dataclasses import dataclass
from datetime import datetime
import logging
import pandas as pd
import simpy

from . import Account
from evsim import entities
from evsim.data import load

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SimulationConfig:
    name: str = str(datetime.now().strftime("%Y%m%d-%H%M%S"))
    charging_power: float = 3.6
    ev_capacity: float = 17.6
    industry_tariff: float = 150
    save_stats: bool = False


class Simulation:
    def __init__(self, cfg, controller):

        self.cfg = cfg

        self.account = Account()
        self.controller = controller

        self.trips = load.car2go_trips(False)
        self.stats = list()

        self.env = simpy.Environment(initial_time=self.trips.start_time.min())
        self.vpp = entities.VPP(
            self.env, "VPP", len(self.trips.EV.unique()), cfg.charging_power
        )

        self.done = False

        # Pass references to controller
        self.controller.env = self.env
        self.controller.account = self.account
        self.controller.vpp = self.vpp

        # Start lifecycle
        self.env.process(self.lifecycle())

    def start(self):
        logger.info("---- STARTING SIMULATION: %s -----" % self.cfg.name)
        while not self.done:
            self.step()

        logger.info("---- RESULTS: %s -----" % self.cfg.name)
        logger.info("Energy charged as VPP: %.2fMWh" % (self.vpp.total_charged / 1000))
        logger.info(
            "Energy that couldn't be charged : %.2fMWh" % (self.vpp.imbalance / 1000)
        )
        logger.info("Total balance: %.2fEUR" % self.account.balance)

        if self.cfg.save_stats is True:
            self.save_stats("./logs/stats-%s.csv" % self.cfg.name)

    def step(self, risk=None, minutes=5):
        if risk:
            self.controller.risk = risk

        if self.env.peek() > self.trips.end_time.max():
            self.done = True
        else:
            self.env.run(until=(self.env.now + (60 * minutes)))

        return self.account.balance, self.done

    def lifecycle(self):
        evs = {}

        # Timerange from start to end in 5 minute intervals
        timeslots = pd.date_range(
            datetime.utcfromtimestamp(self.trips.start_time.min()),
            datetime.utcfromtimestamp(self.trips.end_time.max()),
            freq="5min",
        )
        for _ in timeslots:
            logger.info(
                "[%s] - ---------- TIMESLOT %s ----------"
                % (
                    datetime.fromtimestamp(self.env.now),
                    datetime.fromtimestamp(self.env.now),
                )
            )

            # 1. Allocate consumption plan
            self.vpp.commited_capacity = self.controller.planned_kw(self.env.now)

            # 2. Find trips at the timeslot
            starting_trips = self.trips.loc[self.trips["start_time"] == self.env.now]
            for trip in starting_trips.itertuples():

                # 3. Add EVs to Fleet
                if trip.EV not in evs:
                    evs[trip.EV] = entities.EV(
                        self.env,
                        self.vpp,
                        trip.EV,
                        trip.start_soc,
                        self.cfg.ev_capacity,
                        self.cfg.charging_power,
                    )

                # 4. Start trip with EV
                ev = evs[trip.EV]
                self.env.process(
                    ev.drive(
                        trip.Index,
                        trip.trip_duration,
                        trip.start_soc - trip.end_soc,
                        trip.end_charging,
                        trip.trip_price,
                        account=self.account,
                        refuse=self.controller.refuse_rentals,
                    )
                )

            # NOTE: Wait 1 sec later let all trips start first
            yield self.env.timeout(1)

            # 5. Save simulation stats if enabled
            if self.cfg.save_stats:
                self.stats.append(
                    [
                        self.env.now - 1,
                        int(len(evs)),
                        round(self._fleet_soc(evs), 2),
                        int(len(self.vpp.evs)),
                        round(self.vpp.avg_soc(), 2),
                        round(self.vpp.capacity(), 2),
                        round(self.vpp.total_charged, 2),
                        round(self.account.balance, 2),
                        round(self.vpp.imbalance, 2),
                    ]
                )

            # 6. Centrally control charging
            self.controller.charge_fleet(self.env.now - 1)

            # 7. Wait 5 min timestep
            yield self.env.timeout((5 * 60) - 1)

    def _fleet_soc(self, evs):
        if len(evs) == 0:
            return 0

        soc = 0
        for ev in evs.values():
            soc += ev.battery.level

        return round(soc / len(evs), 2)

    def save_stats(self, filename):
        df_stats = pd.DataFrame(
            data=self.stats,
            columns=[
                "timestamp",
                "fleet",
                "fleet_soc",
                "ev_vpp",
                "vpp_soc",
                "vpp_capacity_kw",
                "vpp_charged_kwh",
                "balance_eur",
                "imbalance_kw",
            ],
        )
        df_stats = df_stats.groupby("timestamp").last()
        df_stats = df_stats.reset_index()
        df_stats.to_csv(filename, index=False)
        df_stats.to_csv("./logs/stats.csv", index=False)
