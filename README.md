[![CircleCI](https://circleci.com/gh/indyfree/FleetSim.svg?style=svg)](https://circleci.com/gh/indyfree/FleetSim) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
# FleetSim
_An event-based electric vehicle fleet charging simulation to create virtual power plants in smart sustainable markets._
## Requirements
- python 3.6 or higher
- GNU make

## Installation

This project is intended to run on Mac or Linux.
On Windows it should also work via the [Linux Subsystem](https://docs.microsoft.com/en-us/windows/wsl/install-win10).

### Clone the Repository

```bash
> git clone https://github.com/indyfree/evsim
```

### Install required Packages
Installs virtual environment and dependencies with `pip`:

```bash
> make requirements
```

## Run Jupyter Notebooks

``` bash
> make jupyter
```

## Preprocess the Data
*Note:* Not all the data are freely accessible. Contact me if you need access.

```bash
> evsim build --help
Usage: evsim build [OPTIONS] COMMAND [ARGS]...

  (Re)build data sources.

Options:
  --help  Show this message and exit.

Commands:
  all               (Re)build all data sources.
  balancing-prices  (Re)build balancing price data.
  intraday-prices   (Re)build intraday price data.
  mobility-demand   (Re)build mobility demand data.
  trips             (Re)build car2go trip data.
```


## Run the simulation
Available parameters:

```bash
> evsim simulate --help
Usage: evsim simulate [OPTIONS]

  Start the EV Simulation.

Options:
  -c, --ev-capacity FLOAT           Battery capacity of EV in kWh.  [default:
                                    17.6]
  -i, --industry-tariff INTEGER     Flat industry tariff, which the fleet can
                                    charge regularly.  [default: 150]
  -s, --charging-speed FLOAT        Charging power in kW.  [default: 3.6]
  --charging-strategy               [regular|balancing|intraday|integrated]
                                    Charging strategy  [default: regular]
  -a, --accuracy <INTEGER INTEGER>  Prediction accuracy.  [default: 100, 100]
  -r, --risk <FLOAT FLOAT>...       Bidding risk [default: 0.0, 0.0]
```

E.g.:

```
> evsim --name=intraday --debug simulate --charging-strategy=intraday
--- Simulation Settings: ---
Debug is on.
Writing Logs to file is on.
Maximal EV range is set to 160km.
EV battery capacity is set to 17.6kWh.
Charging speed is set to 3.6kW.
Industry electricity tariff is set to 250EUR/MWh.
Refusing rentals is set to off.
--- Starting Simulation: ---
INFO    ---- STARTING SIMULATION: intraday -----
INFO    [2017-02-23 00:00:00] - ---------- TIMESLOT 2017-02-23 00:00:00 ----------
INFO    [2017-02-23 00:00:00] - S-GO2459(78.00/100) Added to fleet!
INFO    [2017-02-23 00:00:00] - S-GO2450(66.00/100) Added to fleet!
INFO    [2017-02-23 00:00:00] - S-GO2293(99.00/100) Added to fleet!
INFO    [2017-02-23 00:00:00] - Controller(intraday) Bought 18.00 kW for -37.90 EUR/MWh for 15-min timeslot 2017-02-23 00:30:00
INFO    [2017-02-23 00:00:00] - Controller(intraday) Charge 1.30 EUR cheaper than with industry tariff. Current balance: 1.30 EUR.
INFO    [2017-02-23 00:00:00] - Controller(intraday) Consumption plan for 2017-02-23 00:00:00: 0.00kW, required EVs: 0.
INFO    [2017-02-23 00:00:00] - Controller(intraday) Charging 0/0 EVs from consumption plan.
INFO    [2017-02-23 00:00:00] - Controller(intraday) Charging 0/0 EVs regulary.
INFO    [2017-02-23 00:00:00] - S-GO2459(78.00/100) Starting trip 0.
INFO    [2017-02-23 00:00:00] - S-GO2450(66.00/100) Starting trip 1.
INFO    [2017-02-23 00:00:00] - S-GO2293(99.00/100) Starting trip 2.
...
INFO    [2017-02-23 07:45:00] - ---------- TIMESLOT 2017-02-23 07:45:00 ----------
INFO    [2017-02-23 07:45:00] - S-GO2555(100.00/100) Added to fleet!
INFO    [2017-02-23 07:45:00] - Controller(intraday) Bought 54.00 kW for 36.00 EUR/MWh for 15-min timeslot 2017-02-23 08:15:00
INFO    [2017-02-23 07:45:00] - Controller(intraday) Charge 2.89 EUR cheaper than with industry tariff. Current balance: 137.73 EUR.
INFO    [2017-02-23 07:45:00] - Controller(intraday) Consumption plan for 2017-02-23 07:45:00: 61.20kW, required EVs: 17.
INFO    [2017-02-23 07:45:00] - Controller(intraday) Charging 18/20 EVs from consumption plan.
INFO    [2017-02-23 07:45:00] - Controller(intraday) Charging 2/20 EVs regulary.
INFO    [2017-02-23 07:45:00] - S-GO2333(95.00/100) Starting trip 382.
INFO    [2017-02-23 07:45:00] - S-GO2651(88.93/100) Starting trip 383.
INFO    [2017-02-23 07:45:00] - BALANCING(68.4kW/61.2kW) Removed EV S-GO2651 from VPP.
INFO    [2017-02-23 07:45:00] - BALANCING(64.8kW/61.2kW) Removed EV S-GO2463 from VPP.
INFO    [2017-02-23 07:45:00] - S-GO2651(88.93/100) Charging interrupted! Customer wants to rent car
INFO    [2017-02-23 07:45:00] - S-GO2463(95.36/100) Charging interrupted! Customer wants to rent car
```

## Autocompletion
Activate autocompletion by sourcing the according completion file:
```sh
> source ./completion_zsh.sh
```
