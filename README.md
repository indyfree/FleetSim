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
  -n, --name TEXT                Name of the Simulation.
  -c, --ev-capacity FLOAT        Battery capacity of EV in kWh.  [default: 17.6]
  -r, --ev-range INTEGER         Maximal Range of EV in km.  [default: 160]
  -s, --charging-speed FLOAT     Charging power in kW.  [default: 3.6]
  --charging-strategy [regular]  Charging strategy  [default: regular]
  --stats / --no-stats           Save logs to file. Turning off improves speed.
  --help                         Show this message and exit.
```

E.g.:

``` sh
> env/bin/evsim --debug simulate --charging-speed=3.6 --ev-capacity=17.6 --name=My-Simulation --charging-strategy=regular
Debug is on.
Charging speed is set to 3.6kW.
EV battery capacity is set to 17.6kWh.
INFO    : ---- STARTING SIMULATION: My-Simulation -----
INFO    : [2016-12-01 01:00:01] - S-GO2295(32.00/100) Added to fleet!
INFO    : [2016-12-01 01:00:01] - S-GO2295(32.00/100) Starting trip 0.
INFO    : [2016-12-01 01:00:01] - S-GO2453(45.00/100) Added to fleet!
INFO    : [2016-12-01 01:00:01] - S-GO2453(45.00/100) Starting trip 1.
INFO    : [2016-12-01 01:10:01] - ---------- TIMESLOT 2016-12-01 01:10:01 ----------
INFO    : [2016-12-01 01:10:01] - S-GO2487(39.00/100) Added to fleet!
INFO    : [2016-12-01 01:10:01] - S-GO2487(39.00/100) Starting trip 2.
INFO    : [2016-12-01 01:15:00] - S-GO2453(45.00/100) End Trip 1: Drove for 15.00 minutes and consumed 3% charge.
INFO    : [2016-12-01 01:15:00] - S-GO2453(45.00/100) Adjusting battery level...
INFO    : [2016-12-01 01:15:00] - S-GO2453(42.00/100) Battery level has been decreased by 3%.
```

## Autocompletion
Activate autocompletion by sourcing the according completion file:
```sh
> source ./completion_zsh.sh
```
