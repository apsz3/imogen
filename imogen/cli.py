import click
from imogen.imogen import run


@click.command()
@click.argument("file")
def main(file):
    run(file)
