import click
from datetime import datetime
import logging

from evsim import simulation
from evsim.data import loader

@click.group(name='evsim')
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, debug):
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug

@cli.command()
@click.pass_context
@click.option(
    "-n",
    "--name",
    default=str(datetime.now().strftime("%Y%m%d-%H%M%S")),
    help="Name of the Simulation.",
)
@click.option("-c", "--ev-capacity", default=17.6, help="Battery capacity of EV in kWh.")
@click.option("-s", "--charging-speed", default=3.6, help="Capacity of chargers in kW.")
@click.option("--max-ev-range", default=160, help="Maximal range in km of EV when fully charged.")
def simulate(ctx, name, ev_capacity, charging_speed, max_ev_range):
    click.echo('Debug is %s' % (ctx.obj['DEBUG'] and 'on' or 'off'))
    click.echo('Simulate')
    simulation.start(name, ev_capacity, charging_speed, max_ev_range)
