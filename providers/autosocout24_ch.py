import json
from datetime import datetime

import requests

from . import Provider, AdInfo, Ad
from utils import get_headers_from_firefox_headers_dump
import re


class AutoScout24ChAdInfo(AdInfo):
    data: dict

    def __init__(self, data: dict) -> None:
        self.data = data

    @property
    def url(self) -> str:
        return f"https://www.autoscout24.ch/de/d/{self.data['slug']}?vehid={self.id}"

    @property
    def renewed_at(self) -> datetime:
        raise NotImplementedError

    @property
    def id(self) -> str:
        return self.data['id']  # TODO Тестим тут все атрибуты

    @property
    def title(self) -> str:
        return self.data['title']

    @property
    def price(self) -> int:
        return int(re.search(r"(\d+'\d+)", self.data['prices'][0]).group().replace("'", ''))

    @property
    def production_year(self) -> int:
        return int(self.data['firstReg'].split('.')[1])

    @property
    def mileage(self) -> int:
        return int(self.data['mileage'].split(' km')[0].replace("'", ''))

    @property
    def fuel_type(self) -> str:
        return self.data['fuel']

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


class AutoScout24Ch(Provider):
    brand: str
    model: str
    headers: dict

    def __init__(self, brand: str, model: str, shitstring: str) -> None:
        self.brand = brand
        self.model = model
        self.headers = get_headers_from_firefox_headers_dump(shitstring)
        del self.headers['Accept-Encoding']

    @classmethod
    def get_brand_code(cls, brand: str) -> str:
        if brand == 'volvo':
            return '81'
        else:
            raise NotImplementedError

    @classmethod
    def get_model_code(cls, model: str) -> str:
        if model == 'xc90':
            return '581'
        if model == 'xc60':
            return '559'
        if model == 'xc70':
            return '580'
        else:
            raise NotImplementedError

    def get_ad_list_url(self, page_number: int) -> str:
        url = f"""        
        https://www.autoscout24.ch/webapp/v13/vehicles?
        priceto=10000&
        trans=21%2C209%2C189%2C188%2C187%2C190&
        make={self.get_brand_code(self.brand)}&
        model={self.get_model_code(self.model)}&
        page={page_number}&
        vehtyp=10
        """
        return url.replace('\n', '').replace(' ', '')

    @staticmethod
    def parse_pages_count(page_contents: str) -> int:
        data = json.loads(page_contents)
        return (data['vehicles']['count'] // 20) + 1

    @classmethod
    def parse_ads_data(cls, page_contents: str) -> dict:
        data = json.loads(page_contents)
        return data['vehicles']['items']

    def get_ads_jsons_paginated(self) -> list[dict]:
        ads_data = []

        page_number = 1
        while page_number:
            url = self.get_ad_list_url(page_number)
            response = requests.get(url=url, headers=self.headers)
            assert response.status_code == 200, f'Response status is {response.status_code} instead of 200'
            ads_data.extend(self.parse_ads_data(response.content.decode()))
            pages_count = self.parse_pages_count(response.content.decode())

            if pages_count > page_number:
                page_number += 1
            else:
                break

        return ads_data

    def get_ads(self) -> list[AutoScout24ChAdInfo]:
        ad_jsons = self.get_ads_jsons_paginated()
        ads_info = []
        for ad_json in ad_jsons:
            ads_info.append(AutoScout24ChAdInfo(ad_json))
        return ads_info
