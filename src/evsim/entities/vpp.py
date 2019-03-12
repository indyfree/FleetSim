from datetime import datetime
import logging


class VPP:
    def __init__(self, env, name, num_evs, charger_capacity):
        self.logger = logging.getLogger(__name__)

        self.env = env
        self.evs = dict()
        self.name = name
        self.charger_capacity = charger_capacity

        self.commited_capacity = 0
        self.imbalance = 0
        self.total_charged = 0

    def log(self, message):
        self.logger.info(
            "[%s] - %s(%.1fkW/%.1fkW) %s"
            % (
                datetime.fromtimestamp(self.env.now),
                self.name,
                self.capacity(),
                self.commited_capacity,
                message,
            )
        )

    def log_EVs(self):
        self.log("Number EVs: %d, Mean SoC: %.1f" % (len(self.evs), self.avg_soc()))
        self.log(list(self.evs.values()))

    def socs(self):
        s = list()
        for _, v in self.evs.items():
            s.append(round(v.battery.level, 2))

        return s

    def add(self, ev):
        if ev.name not in self.evs:
            self.evs[ev.name] = ev
            self.log("Adding EV '%s' to VPP." % ev.name)
            self.log_EVs()
        else:
            raise ValueError("'%s' is already allocated to VPP." % ev.name)

    def avg_soc(self):
        if len(self.evs) > 0:
            return sum(self.socs()) / len(self.evs)
        else:
            return 0

    def capacity(self):
        return len(self.evs) * self.charger_capacity

    def contains(self, ev):
        if ev.name in self.evs:
            return True

        return False

    def remove(self, ev):
        if ev.name in self.evs:
            del self.evs[ev.name]
            self.log("Removed EV %s from VPP." % ev.name)
        else:
            raise ValueError("%s was not allocated to VPP." % ev.name)
