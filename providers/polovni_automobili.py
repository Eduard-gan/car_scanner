from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup, Tag, ResultSet

from . import Provider, AdInfo, IncompleteData


class Page:
    url: str
    meta_info: dict
    content: Optional[BeautifulSoup] = None

    def __init__(self, url: str, raw_page_text: str = None, **kwargs):
        self.url = url
        self.meta_info = kwargs

        if raw_page_text:
            self.add_content(raw_page_text)

    def add_content(self, raw_page_text: str = None) -> None:
        self.content = BeautifulSoup(raw_page_text, 'html.parser')


class PolovniAutomobiliAdInfo(AdInfo):
    page: Page
    details: Tag
    photo_block: Tag
    under_photo_icons_block: Tag

    info_block: Tag
    info_boxes: ResultSet

    common_info_block: Tag
    additional_info_block: Tag
    safety_block: Tag
    options_block: Tag
    status_block: Tag
    description_block: Tag

    def __init__(self, page: Page) -> None:
        self.page = page

        self.details = self.page.content.find('div', class_='details')
        if not self.details:
            raise IncompleteData(f'NO DETAILS BLOCK: {self.url=}')

        self.photo_block = self.details.find('div', class_='uk-grid')
        self.under_photo_icons_block = self.photo_block.find('div', id='not-cached-holder')

        self.root_info_block = self.details.find('div', id='classified-content')
        self.info_boxes = self.root_info_block.find_all('div', class_='infoBox')
        self.common_info_block = [x for x in self.info_boxes if 'Opšte informacije' in x.text][0]
        self.additional_info_block = [x for x in self.info_boxes if 'Dodatne informacije' in x.text][0]

        try:
            self.safety_block = [x for x in self.info_boxes if 'Sigurnost' in x.text][0]
        except Exception as e:
            # print(f'SOMETHING WENT WRONG WITH SAFETY BLOCK ON {self.url}: {repr(e)}')
            pass

        try:
            self.options_block = [x for x in self.info_boxes if 'Oprema' in x.text][0]
        except Exception as e:
            # print(f'SOMETHING WENT WRONG WITH "OPTIONS" BLOCK ON {self.url}: {repr(e)}')
            pass

        self.status_block = [x for x in self.info_boxes if 'Stanje' in x.text][0]

        try:
            # Бывает что этого блока нет. Это валидный кейс.
            self.description_block = [x for x in self.info_boxes if 'Opis' in x.text][0]
        except IndexError:
            pass

    @property
    def url(self) -> str:
        return self.page.url

    @property
    def renewed_at(self) -> datetime:
        return self.page.meta_info['renew_date']

    @property
    def id(self) -> str:
        return self.under_photo_icons_block.attrs['data-classifiedid']

    @property
    def title(self) -> str:
        return self.details.h1.contents[0].strip()

    @property
    def price(self) -> int:
        element = self.details.find('span', class_='priceClassified')
        return int(element.text.replace('.', '').replace(' €', ''))

    @property
    def production_year(self) -> int:
        dividers = self.common_info_block.find_all('div', class_='divider')
        element = [x for x in dividers if x.div.div.text == 'Godište'][0]
        return int(element.div.contents[3].text.replace('.', ''))

    @property
    def mileage(self) -> int:
        dividers = self.common_info_block.find_all('div', class_='divider')
        element = [x for x in dividers if x.div.div.text == 'Kilometraža'][0]
        return int(element.div.contents[3].text.replace('.', '').replace('km', '').strip())

    @property
    def fuel_type(self) -> str:
        dividers = self.common_info_block.find_all('div', class_='divider')
        element = [x for x in dividers if x.div.div.text == 'Gorivo'][0]
        return element.div.contents[3].text

    @property
    def engine_volume(self) -> int:
        dividers = self.common_info_block.find_all('div', class_='divider')
        element = [x for x in dividers if x.div.div.text == 'Kubikaža'][0]
        return int(element.div.contents[3].text.replace(' cm3', ''))


class PolovniAutomobili(Provider):
    brand: str
    model: str

    def __init__(self, brand: str, model: str) -> None:
        self.brand = brand
        self.model = model

    def get_ad_list_url(self, page_number: int) -> str:
        return f'https://www.polovniautomobili.com/auto-oglasi/pretraga?page={page_number}&brand={self.brand}&model[0]={self.model}&price_to=10000'

    @staticmethod
    def fetch_page(page: Page) -> Page:
        headers = {"user-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0"}
        response = requests.get(url=page.url, headers=headers)
        page.add_content(response.text)
        return page

    @classmethod
    def fetch_pages(cls, pages: list[Page]) -> list[Page]:
        with ThreadPoolExecutor(max_workers=100) as executor:
            results = []
            futures = [executor.submit(cls.fetch_page, page=page) for page in pages]
            for f in as_completed(futures):
                try:
                    results.append(f.result())
                except Exception as e:
                    print(repr(e))
        return results

    @staticmethod
    def parse_pages_count(page_contents: BeautifulSoup) -> int:
        pagination = page_contents.find('ul', class_='uk-pagination')
        page_elements = pagination.findAll('li')

        pages_count = 0
        for element in page_elements:
            # print(f"PAGE_ELEMENT: {element.text}")
            try:
                page_number = int(element.text)
                if page_number > pages_count:
                    pages_count = page_number
            except Exception as e:
                # print(f'{element.text} NOT RECOGNIZED AS PAGE: {repr(e)}')
                pass
        return pages_count

    @classmethod
    def parse_ads_data(cls, page_contents: BeautifulSoup) -> list[Page]:
        search_results = page_contents.find('div', id='search-results')
        ads_blocks = search_results.findAll('article', class_='classified')

        pages = []
        for block in ads_blocks:
            pages.append(
                Page(
                    url=f'https://www.polovniautomobili.com{block.h2.a.attrs["href"]}',
                    renew_date=datetime.strptime(block.attrs['data-renewdate'], '%Y-%m-%d %H:%M:%S')
                )
            )
        return pages

    def get_ads_pages_paginated(cls) -> list[Page]:
        ads_data = []

        page_number = 1
        while page_number:
            url = cls.get_ad_list_url(page_number)
            page = cls.fetch_page(Page(url=url))

            ads_data.extend(cls.parse_ads_data(page.content))

            pages_count = cls.parse_pages_count(page.content)
            if pages_count > page_number:
                page_number += 1
            else:
                break

        return ads_data

    def get_ads(self) -> list[PolovniAutomobiliAdInfo]:
        ads_pages = self.get_ads_pages_paginated()

        fetched_pages = self.fetch_pages(ads_pages)

        ads_info = []
        for page in fetched_pages:
            try:
                ads_info.append(PolovniAutomobiliAdInfo(page))
            except IncompleteData as e:
                print(repr(e))
        return ads_info
