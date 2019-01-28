import click
from datetime import datetime
import logging
import os

from evsim import simulation
from evsim.data import loader


@click.group(name="evsim")
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def cli(ctx, debug):
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug


@cli.command()
@click.pass_context
@click.option(
    "-n",
    "--name",
    default=str(datetime.now().strftime("%Y%m%d-%H%M%S")),
    help="Name of the Simulation.",
)
@click.option(
    "-c", "--ev-capacity", default=17.6, help="Battery capacity of EV in kWh."
)
@click.option("-s", "--charging-speed", default=3.6, help="Capacity of chargers in kW.")
@click.option(
    "--max-ev-range", default=160, help="Maximal range in km of EV when fully charged."
)
def simulate(ctx, name, ev_capacity, charging_speed, max_ev_range):
    os.makedirs("./logs", exist_ok=True)

    fh = logging.FileHandler('./logs/simulation.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(name)-10s: %(levelname)-7s %(message)s'))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%d.%m. %H:%M:%S",
        handlers=[logging.StreamHandler(), fh],
    )

    click.echo("Debug is %s" % (ctx.obj["DEBUG"] and "on" or "off"))
    click.echo("Simulate")
    simulation.start(name, ev_capacity, charging_speed, max_ev_range)


@cli.group()
@click.pass_context
def build(ctx):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%d.%m. %H:%M:%S",
        handlers=[logging.StreamHandler()],
    )


@build.command()
@click.pass_context
def all(ctx):
    loader.rebuild()


@build.command()
@click.pass_context
def trips(ctx):
    loader.load_car2go_trips(rebuild=True)


@build.command()
@click.pass_context
def mobility_demand(ctx):
    loader.load_car2go_capacity(rebuild=True)


@build.command()
@click.pass_context
def intraday_prices(ctx):
    loader.load_intraday_prices(rebuild=True)


@build.command()
@click.pass_context
def balancing_prices(ctx):
    loader.load_balancing_data(rebuild=True)
