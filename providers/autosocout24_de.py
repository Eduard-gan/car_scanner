import json
from datetime import datetime
from time import sleep

import requests

from . import Provider, AdInfo, Ad


class AutoScout24DeAdInfo(AdInfo):
    data: dict

    def __init__(self, data: dict) -> None:
        self.data = data

    @property
    def url(self) -> str:
        return f"https://autoscout24.de{self.data['url']}"

    @property
    def renewed_at(self) -> datetime:
        raise NotImplementedError

    @property
    def id(self) -> str:
        return self.data['id']  # TODO Тестим тут все атрибуты

    @property
    def title(self) -> str:
        return f"{self.data['vehicle']['make']} {self.data['vehicle']['model']} {self.data['vehicle']['modelVersionInput']}"

    @property
    def price(self) -> int:
        return int(self.data['tracking']['price'])

    @property
    def production_year(self) -> int:
        return int(self.data['tracking']['firstRegistration'].split('-')[1])

    @property
    def mileage(self) -> int:
        return int(self.data['tracking']['mileage'])

    @property
    def fuel_type(self) -> str:
        return self.data['vehicleDetails'][3]['data']

    @property
    def engine_volume(self) -> int:
        raise NotImplementedError

    def as_model(self) -> Ad:
        # Похоже этого просто нет на сайте.
        try:
            engine_volume = self.engine_volume
            renewed_at = self.renewed_at
        except NotImplementedError:
            engine_volume = 0  # Так проще чем снимать со схемы ограничение nullable=False
            renewed_at = None

        return Ad(
            url=self.url,
            external_id=self.id,
            title=self.title,
            price=self.price,
            production_year=self.production_year,
            mileage=self.mileage,
            fuel_type=self.fuel_type,
            engine_volume=engine_volume,
            renewed_at=renewed_at,
        )


class AutoScout24De(Provider):
    brand: str
    model: str

    def __init__(self, brand: str, model: str) -> None:
        self.brand = brand
        self.model = model

    def get_ad_list_url(self, page_number: int) -> str:
        url = f"""
        https://www.autoscout24.de/_next/data/as24-search-funnel_main-3921/lst
        /{self.brand}/{self.model}/tr_automatik.json?
        atype=C
        &cy=D%2CA%2CB%2CE%2CF%2CI%2CL%2CNL
        &damaged_listing=exclude
        &desc=1
        &ocs_listing=include
        &powertype=kw
        &priceto=10000
        &search_id=xpwagnkm84
        &sort=power
        &source=listpage_pagination
        &ustate=N%2CU
        &page={page_number}
        &slug=volvo
        &slug=xc90
        &slug=tr_automatik
        """

        return url.replace(' ', '').replace('\n', '')

    @staticmethod
    def parse_pages_count(page_contents: str) -> int:
        return json.loads(page_contents)['pageProps']['numberOfPages']

    @classmethod
    def parse_ads_data(cls, page_contents: str) -> dict:
        data = json.loads(page_contents)
        return data['pageProps']['listings']

    def get_ads_jsons_paginated(cls) -> list[dict]:
        ads_data = []

        page_number = 1
        while page_number:
            url = cls.get_ad_list_url(page_number)
            response = requests.get(url=url)
            assert response.status_code == 200, f'Response status is {response.status_code} instead of 200'

            ads_data.extend(cls.parse_ads_data(response.content.decode()))

            pages_count = cls.parse_pages_count(response.content.decode())
            sleep(5)

            if pages_count > page_number:
                page_number += 1
            else:
                break

        return ads_data

    def get_ads(self) -> list[AutoScout24DeAdInfo]:
        ad_jsons = self.get_ads_jsons_paginated()
        ads_info = []
        for ad_json in ad_jsons:
            ads_info.append(AutoScout24DeAdInfo(ad_json))
        return ads_info
