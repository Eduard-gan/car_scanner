import typer
from sqlalchemy import text

from db.models import Session
from logic import fetch_and_save_to_db
from providers.polovni_automobili import PolovniAutomobili

app = typer.Typer()


@app.command()
def scrap() -> None:
    session = Session()
    session.expire_on_commit = False

    new_ads, updates = fetch_and_save_to_db(session=session, provider=PolovniAutomobili(brand='volvo', model='xc90'))

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
