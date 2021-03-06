import click
from datetime import datetime
import logging
import os
import time

from evsim.controller import Controller, strategy
from evsim.data import load
from evsim.simulation import Simulation, SimulationConfig

logger = logging.getLogger(__name__)


@click.group(name="evsim")
@click.option("--debug/--no-debug", default=False)
@click.option(
    "-n",
    "--name",
    default=str(datetime.now().strftime("%Y%m%d-%H%M%S")),
    help="Name of the Simulation.",
)
@click.option(
    "--logs/--no-logs",
    default=True,
    help="Save logs to file. Turning off improves speed.",
)
@click.pass_context
def cli(ctx, debug, name, logs):
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    ctx.obj["LOGS"] = logs
    ctx.obj["NAME"] = name

    f = logging.Formatter("%(levelname)-7s %(message)s")

    sh = logging.StreamHandler()
    sh.setFormatter(f)
    if not debug:
        sh.setLevel(logging.ERROR)
    handlers = [sh]

    if logs:
        os.makedirs("./logs", exist_ok=True)
        fh = logging.FileHandler("./logs/%s.log" % name, mode="w")
        fh.setFormatter(f)
        fh.setLevel(logging.DEBUG)
        handlers = [sh, fh]

    logging.basicConfig(
        level=logging.DEBUG, datefmt="%d.%m. %H:%M:%S", handlers=handlers
    )


@cli.command(help="Start the EV Simulation.")
@click.pass_context
@click.option(
    "-c",
    "--ev-capacity",
    default=17.6,
    help="Battery capacity of EV in kWh.",
    show_default=True,
)
@click.option(
    "-i",
    "--industry-tariff",
    default=150,
    help="Flat industry tariff, which the fleet can charge regularly.",
    show_default=True,
)
@click.option(
    "-s",
    "--charging-speed",
    default=3.6,
    help="Charging power in kW.",
    show_default=True,
)
@click.option(
    "--charging-strategy",
    type=click.Choice(["regular", "balancing", "intraday", "integrated"]),
    default="regular",
    help="Charging strategy",
    show_default=True,
)
@click.option(
    "-a",
    "--accuracy",
    type=(int, int),
    help="Prediction accuracy.",
    default=(100, 100),
    show_default=True,
)
@click.option(
    "-r",
    "--risk",
    type=(float, float),
    help="Bidding risk to account for uncertainty",
    default=(0.0, 0.0),
    show_default=True,
)
def simulate(
    ctx, ev_capacity, charging_speed, charging_strategy, industry_tariff, accuracy, risk
):
    click.echo("--- Simulation Settings: ---")
    click.echo("Debug is %s." % (ctx.obj["DEBUG"] and "on" or "off"))
    click.echo("Writing Logs to file is %s." % (ctx.obj["LOGS"] and "on" or "off"))
    click.echo("EV battery capacity is set to %skWh." % ev_capacity)
    click.echo("Charging speed is set to %skW." % charging_speed)
    click.echo("Industry electricity tariff is set to %sEUR/MWh." % industry_tariff)
    click.echo("Charging strategy is set to %s" % charging_strategy)
    click.echo("Prediction accuracy is set to (%d%%, %d%%)." % accuracy)
    click.echo("Bidding risk is set to (%.2f, %.2f)." % risk)

    if charging_strategy == "regular":
        s = strategy.regular
    elif charging_strategy == "balancing":
        s = strategy.balancing
    elif charging_strategy == "intraday":
        s = strategy.intraday
    elif charging_strategy == "integrated":
        s = strategy.integrated

    cfg = SimulationConfig(
        ctx.obj["NAME"], charging_speed, ev_capacity, industry_tariff
    )

    controller = Controller(cfg, s, accuracy=accuracy, risk=risk)
    sim = Simulation(cfg, controller)

    click.echo("--- Starting Simulation: ---")
    start = time.time()
    sim.start()

    click.echo("--- Simulation Results: ---")

    results = sim.results.sum()
    click.echo("Energy charged as VPP: %.2fMWh" % (results.charged_vpp_kwh / 1000))
    click.echo(
        "Energy charged regularly: %.2fMWh" % (results.charged_regular_kwh / 1000)
    )
    click.echo(
        "Energy that couldn't be charged (imbalance): %.2fMWh"
        % (results.imbalance_kwh / 1000)
    )
    click.echo("Total charging profits: %.2fEUR" % results.profit_eur)
    click.echo(
        "Total lost rental costs: %.2fEUR (%d rentals)"
        % (results.lost_rentals_eur, results.lost_rentals_nb)
    )
    click.echo("Elapsed time %.2f minutes" % ((time.time() - start) / 60))


@cli.group(help="(Re)build data sources.")
@click.pass_context
def build(ctx):
    click.echo("Debug is %s." % (ctx.obj["DEBUG"] and "on" or "off"))


@build.command(help="(Re)build all data sources.")
@click.option(
    "-c",
    "--ev-capacity",
    default=17.6,
    help="Battery capacity of EV in kWh.",
    show_default=True,
)
@click.option(
    "-r",
    "--ev-range",
    default=160,
    help="Maximal Range of EV in km.",
    show_default=True,
)
@click.option(
    "-s",
    "--charging-speed",
    default=3.6,
    help="Charging power in kW.",
    show_default=True,
)
def all(ev_capacity, ev_range, charging_speed):
    click.echo("Building all data sources...")
    load.rebuild(charging_speed, ev_capacity, ev_range)


@build.command(help="(Re)build car2go trip data.")
@click.option(
    "-r",
    "--ev-range",
    default=160,
    help="Maximal Range of EV in km.",
    show_default=True,
)
@click.option(
    "--infer-chargers/ --no-infer-chargers",
    default=False,
    help="Infer charging stations by GPS data.",
)
def trips(ev_range, infer_chargers):
    click.echo("Maximal EV range is set to %skm." % ev_range)
    click.echo("Building car2go trip data...")
    click.echo("Infer Chargers is %s." % (infer_chargers and "on" or "off"))
    load.car2go_trips(ev_range, infer_chargers=infer_chargers, rebuild=True)


@build.command(name="capacity", help="(Re)build car2go capacity data.")
@click.option(
    "-c", "--ev-capacity", default=17.6, help="Battery capacity of EV in kWh."
)
@click.option("-r", "--ev-range", default=160, help="Maximal Range of EV in km.")
@click.option(
    "-s",
    "--charging-speed",
    default=3.6,
    help="Charging power of charging stations in kW.",
)
@click.option("--simulate-charging/--no-simulate-charging", default=False)
def car2go_capacity(ev_capacity, ev_range, charging_speed, simulate_charging):
    click.echo("Maximal EV range is set to %skm." % ev_range)
    click.echo("EV battery capacity is set to %skWh." % ev_capacity)
    click.echo("Charging speed is set to %skW." % charging_speed)
    click.echo("Building car2go capacity data...")
    load.car2go_capacity(
        charging_speed,
        ev_capacity,
        ev_range,
        rebuild=True,
        simulate_charging=simulate_charging,
    )


@build.command(help="(Re)build intraday price data.")
def intraday_prices():
    click.echo("Rebuilding intraday price data...")
    load.intraday_prices(rebuild=True)


@build.command(help="(Re)build balancing price data.")
def balancing_prices():
    click.echo("Rebuilding balanacing price data...")
    load.balancing_prices(rebuild=True)


@cli.group(help="EV Fleet Controller")
@click.pass_context
def controller(ctx):
    cfg = SimulationConfig()
    c = Controller(cfg, strategy.intraday)
    ctx.obj["CONTROLLER"] = c
    return True


@controller.command(help="Bid at a given market")
@click.option("-p", "--price", help="Price in EUR/MWh.", type=int)
@click.option("-q", "--quantity", help="Quantity in kW.", type=int)
@click.option(
    "-t", "--timeslot", help="15-min timeslot as string e.g. '2018-01-01 08:15'."
)
@click.option(
    "--market",
    type=click.Choice(["balancing", "intraday"]),
    default="intraday",
    help="Market to bid on",
    show_default=True,
)
@click.pass_context
def bid(ctx, price, quantity, timeslot, market):
    controller = ctx.obj["CONTROLLER"]

    if market == "intraday":
        market = controller.intraday
    elif market == "balancing":
        market = controller.balancing

    try:
        ts = int(datetime.fromisoformat(timeslot).timestamp())
        result = market.bid(ts, price, quantity)
        if result:
            click.echo(
                "Succesful bid for %s at %.2fMWh/%.2fkW"
                % (datetime.fromtimestamp(result[0]), result[2], result[1])
            )
        else:
            click.echo("Bid unsuccessful! Try a higher price next time.")
    except ValueError as e:
        logger.error(e)


@controller.group(help="Predict all the things")
@click.pass_context
def predict(ctx):
    return True


@predict.command(help="Predict clearing price at the intraday market.")
@click.option(
    "-t", "--timeslot", help="15-min timeslot as string e.g. '2018-01-01 08:15'."
)
@click.option(
    "--market",
    type=click.Choice(["balancing", "intraday"]),
    default="intraday",
    help="Market to bid on",
    show_default=True,
)
@click.pass_context
def clearing_price(ctx, timeslot, market):
    controller = ctx.obj["CONTROLLER"]

    if market == "intraday":
        market = controller.intraday_market
    elif market == "balancing":
        market = controller.balancing_market

    try:
        ts = int(datetime.fromisoformat(timeslot).timestamp())
        click.echo("%.2f EUR/MWh" % market.clearing_price(ts))
    except ValueError as e:
        logger.error(e)


@predict.command(help="Predict available fleet capacity.")
@click.option(
    "-t", "--timeslot", help="5-min timeslot as string e.g. '2018-01-01 08:05'."
)
@click.pass_context
def capacity(ctx, timeslot):
    controller = ctx.obj["CONTROLLER"]

    try:
        ts = int(datetime.fromisoformat(timeslot).timestamp())
        click.echo("%.2f kW" % controller.predict_capacity(ts))
    except ValueError as e:
        logger.error(e)


@predict.command(help="Predict minimum available fleet capacity in market period.")
@click.option(
    "-t", "--timeslot", help="15-min timeslot as string e.g. '2018-01-01 08:05'."
)
@click.pass_context
def min_capacity(ctx, timeslot):
    controller = ctx.obj["CONTROLLER"]

    try:
        ts = int(datetime.fromisoformat(timeslot).timestamp())
        click.echo("%.2f kW" % controller.predict_min_capacity(ts))
    except ValueError as e:
        logger.error(e)
