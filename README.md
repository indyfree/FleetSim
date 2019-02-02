[![CircleCI](https://circleci.com/gh/indyfree/evsim.svg?style=svg)](https://circleci.com/gh/indyfree/evsim) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
# Electric Vehicle Virtual Power Plant Simulation

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
*Note:* Not all the data are freely accesseble. Contact me if you need access.

```bash
> env/bin/evsim build --help

Usage: evsim build [OPTIONS] COMMAND [ARGS]...

  (Re)build all data sources.

Options:
  --help  Show this message and exit.

Commands:
  balancing-prices  (Re)build balancing price data.
  intraday-prices   (Re)build intraday price data.
  mobility-demand   (Re)build mobility demand data.
  trips             (Re)build car2go trip data.
```


## Run the simulation
Available parameters:

```bash
> env/bin/evsim --help
Usage: evsim [OPTIONS] COMMAND [ARGS]...

Options:
  --debug / --no-debug
  -s, --charging-speed FLOAT  Charging power of charging stations in kW.
  -c, --ev-capacity FLOAT     Battery capacity of EV in kWh.
  -r, --ev-range INTEGER      Maximal Range of EV in km.
  --help                      Show this message and exit.

Commands:
  build     (Re)build all data sources.
  simulate  Start the EV Simulation.

```

E.g.:

``` sh
> env/bin/evsim --debug --charging-speed 3.6 --ev-capacity 17.6 simulate --name My-Simulation                                                                                                ~/uni/evsim master 2+
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

