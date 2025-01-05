import click
from imogen.imogen import run
import logging


@click.command()
@click.argument("file")
@click.option("--preview", "-p", is_flag=True)
@click.option("--verbose", "-v", is_flag=True)
def main(file, preview, verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    run(file, preview=preview)
