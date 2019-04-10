from dataclasses import dataclass
from datetime import datetime
import logging
import pandas as pd
import simpy

from . import Statistic, SimEntry, ResultEntry
from evsim import entities
from evsim.data import load

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SimulationConfig:
    name: str = str(datetime.now().strftime("%Y%m%d-%H%M%S"))
    charging_power: float = 3.6
    ev_capacity: float = 17.6
    industry_tariff: float = 150


class Simulation:
    def __init__(self, cfg, controller):

        self.cfg = cfg

        self.stats = Statistic()
        self.results = Statistic()

        self.controller = controller

        self.trips = load.car2go_trips(False)

        self.env = simpy.Environment(initial_time=self.trips.start_time.min())
        self.vpp = entities.VPP(
            self.env, "VPP", len(self.trips.EV.unique()), cfg.charging_power
        )

        self.done = False

        # Pass references to controller
        self.controller.env = self.env
        self.controller.vpp = self.vpp

        # Start lifecycle
        self.env.process(self.lifecycle())

    def start(self):
        logger.info("---- STARTING SIMULATION: %s -----" % self.cfg.name)
        while not self.done:
            self.step()

        logger.info("---- RESULTS: %s -----" % self.cfg.name)

        results = self.results.sum()
        logger.info("Energy charged as VPP: %.2fMWh" % (results.charged_vpp_kwh / 1000))
        logger.info(
            "Energy charged regularly: %.2fMWh" % (results.charged_regular_kwh / 1000)
        )
        logger.info(
            "Energy that couldn't be charged (imbalance): %.2fMWh"
            % (results.imbalance_kwh / 1000)
        )
        logger.info("Total charging profits: %.2fEUR" % results.profit_eur)
        logger.info(
            "Total lost rental costs: %.2fEUR (%d rentals)"
            % (results.lost_rentals_eur, results.lost_rentals_nb)
        )

        self.stats.write("./logs/stats-%s.csv" % self.cfg.name)
        self.results.write("./results/%s.csv" % self.cfg.name)

    def step(self, risk=None, minutes=5):
        if risk:
            self.controller.risk = risk

        if self.env.peek() > self.trips.end_time.max():
            self.done = True
        else:
            self.env.run(until=(self.env.now + (60 * minutes)))

        return self.controller.account.balance, self.done

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
                        account=self.controller.account,
                        refuse=self.controller.refuse_rentals,
                    )
                )

            # NOTE: Wait 1 sec later let all trips start first
            yield self.env.timeout(1)

            # 5. Save simulation stats
            self.stats.add(
                SimEntry(
                    timestamp=self.env.now - 1,
                    fleet_evs=len(evs),
                    fleet_soc=self._fleet_soc(evs),
                    available_evs=self._fleet_available(evs),
                    charging_evs=self._fleet_charging(evs),
                    vpp_soc=self.vpp.avg_soc(),
                    vpp_evs=len(self.vpp.evs),
                    vpp_charging_power_kw=self.vpp.capacity(),
                )
            )

            # 6. Centrally control charging
            p, vpp, r, i = self.controller.charge_fleet(self.env.now - 1)

            # NOTE: Think of other way to pass rental costs back from EV
            lost_rentals_eur = self.controller.account.lost_rental_eur
            lost_rentals_nb = self.controller.account.lost_rental_nb
            self.controller.account.lost_rental_reset()

            rb, ri = self.controller.risk
            self.results.add(
                ResultEntry(
                    timestamp=self.env.now - 1,
                    profit_eur=p,
                    lost_rentals_eur=lost_rentals_eur,
                    lost_rentals_nb=lost_rentals_nb,
                    charged_regular_kwh=r,
                    charged_vpp_kwh=vpp,
                    imbalance_kwh=i,
                    risk_bal=rb,
                    risk_intr=ri,
                )
            )

            # 7. Wait 5 min timestep
            yield self.env.timeout((5 * 60) - 1)

    def _fleet_soc(self, evs):
        if len(evs) == 0:
            return 0

        soc = 0
        for ev in evs.values():
            soc += ev.battery.level

        return soc / len(evs)

    def _fleet_available(self, evs):
        if len(evs) == 0:
            return 0
        available = 0
        for ev in evs.values():
            if ev.available:
                available += 1
        return available

    def _fleet_charging(self, evs):
        if len(evs) == 0:
            return 0
        charging = 0
        for ev in evs.values():
            if ev.charging:
                charging += 1
        return charging
