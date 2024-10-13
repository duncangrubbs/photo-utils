from typing import Annotated
import typer
from utils import Utils

app = typer.Typer()


@app.command()
def utils(path: Annotated[str, typer.Option(help="Path to base photos directory")]):
    Utils(base_dir=path).update_dates_from_metadata()


@app.command()
def main():
    pass


if __name__ == "__main__":
    app()
