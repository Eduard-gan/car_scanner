import typer
from sqlalchemy import text

from db.models import Session
from logic import fetch_and_save_to_db
from providers.polovni_automobili import PolovniAutomobili
from providers.autosocout24_ch import AutoScout24Ch
from providers.autosocout24_de import AutoScout24De
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

    shitstring = """
GET /webapp/v13/vehicles?priceto=10000&make=81&model=581&sort=price_desc&vehtyp=10 HTTP/1.1
Host: www.autoscout24.ch
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0
Accept: */*
Accept-Language: ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3
Accept-Encoding: gzip, deflate, br
Content-Language: de
X-Split-Campaigns: Sorting_Algorithm,control;
X-Split-Key: d2fa637b-17c6-400e-8dc8-e16026991071
x-topCarRef: 10425568
x-client-version: 3.171.2
Authorization: 
Signature: e1bbfa5d1331f.GZbY0Dcy8O.1685274971006.747
Connection: keep-alive
Referer: https://www.autoscout24.ch/de/autos/volvo--xc90?priceto=10000&make=81&model=581&sort=price_desc&vehtyp=10
Cookie: cf_clearance=WcbqyWDChsNFN3qrVpV__EaDIpMRpT.XdL5_..ptVv0-1685274049-0-250; aspi_guid2=c3da5a72-2f30-4286-a172-0eec889fdd22; OptanonConsent=isGpcEnabled=0&datestamp=Sun+May+28+2023+13%3A40%3A55+GMT%2B0200+(%D0%A6%D0%B5%D0%BD%D1%82%D1%80%D0%B0%D0%BB%D1%8C%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202209.1.0&isIABGlobal=false&hosts=&consentId=504f7b3a-197f-403c-8d90-c29a74ffc3e1&interactionCount=1&landingPath=NotLandingPage&groups=C0003%3A1%2CC0001%3A1%2CC0004%3A1%2CC0002%3A1%2CSTACK42%3A1&geolocation=RS%3BVO&AwaitingReconsent=false; OptanonAlertBoxClosed=2023-05-28T00:09:38.079Z; eupubconsent-v2=CPseOXAPseOXAAcABBENDGCsAP_AAH_AAAQ4Jdtf_X__b2_r-_7_f_t0eY1P9_7__-0zjhfdl-8N3f_X_L8X52M7vF36tq4KuR4ku3LBIUdlHPHcTVmw6okVryPsbk2cr7NKJ7PEmnMbO2dYGH9_n1_z-ZKY7___f__z_v-v________7-3f3__5___-__e_V__9zfn9_____9vP___9v-_9__________3_79_7_H9-f_87gl2ASYatxAF2ZY4E20YRQogRhWEhVAoAKKAYWiAwgdXBTsrgJ9YRIAUAoAnAiBDgCjJgEAAAkASEQASBHggEAAEAgABAAqEQgAY2AQWAFgIBAAKA6FijFAEIEhBkRERCmBAVIkFBPZUIJQf6GmEIdZYAUGj_ioQEayBisCISFg5DgiQEvFkgeYo3yAEYAUAolQrUUnpoCFjM2AAA.f_gAD_gAAAAA; DG_splitIoId_as24=d2fa637b-17c6-400e-8dc8-e16026991071; _ga_RJ1PWF7TNC=GS1.1.1685274056.3.1.1685274084.0.0.0; _ga=GA1.2.1602843914.1685232579; FPLC=%2BW6qlUplsMuQ4k7sQWEJfhsV18fjK4d8Y%2F3ntYFwZ2Cw7p5mT7zjvifIomrxjZw%2FfPJ2wNwnYeBS0PT8HDrQSPcu%2FrYLhkreWMIStaO8HDD4bmTvclcbOW%2Bk3DBmmA%3D%3D; FPID=FPID2.2.Wa2saKFnQKWChysSbk7hwsEj6PN2kNpMCruuVMhvpt4%3D.1685232579; FPAU=1.2.574827245.1685232579; _fbp=fb.1.1685232578688.340526519; ce.tracking-opt-in=true; dakt_2_dnt=false; ce.guid=2f4c55eb-635a-4022-be37-fa93b134d50a; ce.sid=6b624dfb-8d28-481b-83b8-5fadc252d299; _gid=GA1.2.2003917635.1685232579; _hjSessionUser_325941=eyJpZCI6Ijc3OTlkMGM4LWNiN2YtNTU0Yy05ZWMyLWE3MGE3MzIzZTZlOCIsImNyZWF0ZWQiOjE2ODUyMzI1Nzk0NzUsImV4aXN0aW5nIjp0cnVlfQ==; cto_bundle=Xm6JD19tc0phdlByRTM1THY5cVclMkZOYVklMkJUb09Obm1pJTJCU3ByanpEa2hKSXZpQW1FbVhJZ0F6SWtFTEE0UlJqaUxhdmxqSDBTU2JBQm53ZVkyZFExSnBvdHN4MGhMSmJOSTdYaHV6V0dxRSUyQiUyRnJoRjZER3FTWW5XT1VoRlhPU0RvUzZTMlgxN0hrZmhpVTRtYmtua1FZaVliclF3JTNEJTNE; .tvref=10425568; .datakey=4f89fcf9-5462-4887-8c76-fca17af97624; dakt_2_uuid=6258fd2fd0a03841a44f6f822ec61142; dakt_2_uuid_ts=1685232597376; dakt_2_version=2.1.64; _iz_uh_ps_=%7B%22vi%22%3Anull%2C%22pv%22%3A3%2C%22lv%22%3A%222023-05-28T11%3A41%3A23.144Z%22%2C%22pr%22%3A%222023-05-28T10%3A16%3A37.593Z%22%2C%22si%22%3A%5B%7B%22i%22%3A%22iwhfhguq%22%2C%22c%22%3A1%2C%22m%22%3Afalse%2C%22s%22%3A0%2C%22l%22%3Anull%7D%2C%7B%22i%22%3A%22irhrudyuli%22%2C%22c%22%3A-1%2C%22m%22%3Afalse%2C%22s%22%3A0%2C%22l%22%3Anull%7D%2C%7B%22i%22%3A%22ahyeliru%22%2C%22c%22%3A-1%2C%22m%22%3Afalse%2C%22s%22%3A0%2C%22l%22%3Anull%7D%5D%7D; __gads=ID=2adae266c64de3a9:T=1685268916:RT=1685274056:S=ALNI_MZe0pN-3y-RriZQKlnpl8dyz7Z8Og; __gpi=UID=00000c28f5bcd33a:T=1685268916:RT=1685274056:S=ALNI_MatXW4D7vRG8VEkiiDIyDh-x093hw; __cf_bm=cFnBnDNbtWAghxp8KIUAQ.wSw1szzL3309nviMPlYbg-1685274053-0-AfEluSfcgxcBnmVJtPUe/6F4wNG8SeVDfW8w9VgNaidAHSFIRjy4Ag3i9y5F0dPefRa6pWjUnjHVlXyFt3kmh6U=; _cfuvid=jr0S795tGh2lxxzxbm6EejCrPj0xazQeFsiWzdOU6gk-1685274053712-0-604800000; BIGipServerpool_autoweb_http=1744835594.20480.0000; _dd_s=logs=1&id=ee33f75d-4b71-495b-91d0-1100833cdb26&created=1685274054882&expire=1685275870261; requestHeaders={%22x-topCarRef%22:%2210425568%22}; AS24ApiAuth=null; BIGipServerpool_autowebapp_http=1862341642.20480.0000; dakt_2_session_id=51136edfd7f7a0947fb79a1865e4a4a4; _uetsid=efbd5d00fceb11edbbb1fd58eace668a; _uetvid=efbd7b30fceb11edab3fbf6475c1f651; _hjIncludedInSessionSample_325941=0; _hjSession_325941=eyJpZCI6ImQwZTVlMDA2LTM1MzMtNDliMi04OTExLTkwODIxNmE4MDczMCIsImNyZWF0ZWQiOjE2ODUyNzQwNTczNzgsImluU2FtcGxlIjpmYWxzZX0=; _hjAbsoluteSessionInProgress=0; _iz_sd_ss_=%7B%22np%22%3A2%2C%22se%22%3A%222023-05-28T11%3A41%3A11.994Z%22%2C%22ru%22%3A%22%22%2C%22ss%22%3Anull%7D; _gat_UA-2620016-1=1
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
"""

    for model in ('xc90', 'xc60', 'xc70'):
        for provider in (
                AutoScout24Ch(brand='volvo', model=model, shitstring=shitstring),
                AutoScout24De(brand='volvo', model=model),
                PolovniAutomobili(brand='volvo', model=model),
        ):
            print(f"***********************{provider.__class__.__name__}: {model}***********************")
            new_ads, updates = fetch_and_save_to_db(session=session, provider=provider)

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
