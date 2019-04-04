from dataclasses import dataclass, asdict
import logging
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Entry:
    timestamp: int = 0
    fleet_evs: float = 0
    fleet_soc: float = 0
    available_evs: int = 0
    charging_evs: int = 0
    vpp_evs: int = 0
    vpp_soc: float = 0
    vpp_charging_power_kw: float = 0
    vpp_charged_kwh: float = 0
    balance_eur: float = 0
    imbalance_kw: float = 0
    rental_profits: float = 0


class Statistic:
    def __init__(self):
        self.stats = list()

    def add(self, entry):
        self.stats.append(asdict(entry))

    def write(self, filename):
        order = [
            "timestamp",
            "fleet_evs",
            "fleet_soc",
            "available_evs",
            "charging_evs",
            "vpp_evs",
            "vpp_soc",
            "vpp_charging_power_kw",
            "vpp_charged_kwh",
            "balance_eur",
            "imbalance_kw",
            "rental_profits",
        ]

        df_stats = pd.DataFrame(data=self.stats)
        df_stats = df_stats[order]
        df_stats = df_stats.round(2)
        df_stats.to_csv(filename, index=False)
        return df_stats
