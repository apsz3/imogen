import click
from imogen.imogen import run


@click.command()
@click.argument("file")
@click.option("--preview", "-p", is_flag=True)
def main(file, preview):
    run(file, preview=preview)
