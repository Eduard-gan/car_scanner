import typer
from sqlalchemy import text

from db.models import Session
from logic import fetch_and_save_to_db
from providers.polovni_automobili import PolovniAutomobili
from pathlib import Path
from alembic import command
from alembic.config import Config


app = typer.Typer()


@app.command()
def make_migrations(message: str = None):
    alembic_cfg = Config(
        Path(__file__).parent.joinpath("db/alembic.ini").absolute().as_posix()
    )
    command.revision(alembic_cfg, message=message, autogenerate=True)


@app.command()
def migrate(rev_id: str = "head"):
    alembic_cfg = Config(
        Path(__file__).parent.joinpath("db/alembic.ini").absolute().as_posix()
    )
    command.upgrade(alembic_cfg, rev_id)


@app.command()
def rollback():
    alembic_cfg = Config(
        Path(__file__).parent.joinpath("alembic.ini").absolute().as_posix()
    )
    command.downgrade(alembic_cfg, revision="-1")


@app.command()
def scrap() -> None:
    session = Session()
    session.expire_on_commit = False

    for model in ('xc90', 'xc60', 'xc70'):
        print(f"********************************************* {model} ************************************************")
        new_ads, updates = fetch_and_save_to_db(session=session, provider=PolovniAutomobili(brand='volvo', model=model))

        if new_ads:
            print("NEW ADS:")
            for ad in new_ads:
                print(ad)

        if updates:
            print("UPDATED ADS:")
            for event in updates:
                print(event.get_description(session))

@app.command()
def get(query: str) -> None:
    for ad in Session().execute(text(query)).scalars():
        print(ad)


if __name__ == '__main__':
    app()
