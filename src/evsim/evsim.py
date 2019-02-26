import click
from datetime import datetime
import logging
import os
import time

from evsim.controller import Controller, strategy
from evsim.data import loader
from evsim.simulation import Simulation

logger = logging.getLogger(__name__)


@click.group(name="evsim")
@click.option("--debug/--no-debug", default=False)
@click.option(
    "--logs/--no-logs",
    default=True,
    help="Save logs to file. Turning off improves speed.",
)
@click.pass_context
def cli(ctx, debug, logs):
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    ctx.obj["LOGS"] = logs

    f = logging.Formatter("%(levelname)-7s %(message)s")

    sh = logging.StreamHandler()
    sh.setFormatter(f)
    if not debug:
        sh.setLevel(logging.ERROR)
    handlers = [sh]

    if logs:
        os.makedirs("./logs", exist_ok=True)
        fh = logging.FileHandler(
            "./logs/%s.log" % str(datetime.now().strftime("%Y%m%d-%H%M%S"))
        )
        fh.setFormatter(f)
        fh.setLevel(logging.DEBUG)
        handlers = [sh, fh]

    logging.basicConfig(
        level=logging.DEBUG, datefmt="%d.%m. %H:%M:%S", handlers=handlers
    )


@cli.command(help="Start the EV Simulation.")
@click.pass_context
@click.option(
    "-n",
    "--name",
    default=str(datetime.now().strftime("%Y%m%d-%H%M%S")),
    help="Name of the Simulation.",
)
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
@click.option(
    "--charging-strategy",
    type=click.Choice(["regular", "balancing", "intraday"]),
    default="regular",
    help="Charging strategy",
    show_default=True,
)
@click.option(
    "--stats/--no-stats",
    default=True,
    help="Save logs to file. Turning off improves speed.",
)
def simulate(
    ctx, name, ev_capacity, ev_range, charging_speed, charging_strategy, stats
):
    click.echo("Debug is %s." % (ctx.obj["DEBUG"] and "on" or "off"))
    click.echo("Writing Logs to file is %s." % (ctx.obj["LOGS"] and "on" or "off"))
    click.echo("Maximal EV range is set to %skm." % ev_range)
    click.echo("EV battery capacity is set to %skWh." % ev_capacity)
    click.echo("Charging speed is set to %skW." % charging_speed)

    if charging_strategy == "regular":
        s = strategy.regular
    elif charging_strategy == "balancing":
        s = strategy.balancing
    elif charging_strategy == "intraday":
        s = strategy.intraday

    sim = Simulation(name, charging_speed, ev_capacity, s, stats)
    start = time.time()
    sim.start()
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
    loader.rebuild(charging_speed, ev_capacity, ev_range)


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
    loader.load_car2go_trips(ev_range, infer_chargers, rebuild=True)


@build.command(help="(Re)build car2go capacity data.")
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
def capacity(ev_capacity, ev_range, charging_speed, simulate_charging):
    click.echo("Maximal EV range is set to %skm." % ev_range)
    click.echo("EV battery capacity is set to %skWh." % ev_capacity)
    click.echo("Charging speed is set to %skW." % charging_speed)
    click.echo("Building car2go capacity data...")
    loader.load_car2go_capacity(
        charging_speed,
        ev_capacity,
        ev_range,
        rebuild=True,
        simulate_charging=simulate_charging,
    )


@build.command(help="(Re)build intraday price data.")
def intraday_prices():
    click.echo("Rebuilding intraday price data...")
    loader.load_intraday_prices(rebuild=True)


@build.command(help="(Re)build balancing price data.")
def balancing_prices():
    click.echo("Rebuilding balanacing price data...")
    loader.load_balancing_prices(rebuild=True)


@cli.group(help="EV Fleet Controller")
@click.pass_context
def controller(ctx):
    c = Controller(strategy.regular)
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
        result = market.bid(timeslot, price, quantity)
        if result:
            click.echo(result)
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
        market = controller.intraday
    elif market == "balancing":
        market = controller.balancing

    try:
        click.echo("%.2f EUR/MWh" % controller.predict_clearing_price(market, timeslot))
    except ValueError as e:
        logger.error(e)


@predict.command(help="Predict available fleet capacity.")
@click.option(
    "-t", "--timeslot", help="5-min timeslot as string e.g. '2018-01-01 08:05'."
)
@click.pass_context
def available_capacity(ctx, timeslot):
    controller = ctx.obj["CONTROLLER"]

    try:
        click.echo(
            "%.2f kW"
            % controller.predict_available_capacity(controller.fleet_capacity, timeslot)
        )
    except ValueError as e:
        logger.error(e)
