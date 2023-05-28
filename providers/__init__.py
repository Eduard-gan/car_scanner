from datetime import datetime

from db.models import Ad


class IncompleteData(Exception):
    """Данных недостаточно, чтобы предоставить базовый набор данных об объявлении."""


class AdInfo:

    @property
    def url(self) -> str:
        raise NotImplementedError

    @property
    def renewed_at(self) -> datetime:
        raise NotImplementedError

    @property
    def id(self) -> str:
        raise NotImplementedError

    @property
    def title(self) -> str:
        raise NotImplementedError

    @property
    def price(self) -> int:
        raise NotImplementedError

    @property
    def production_year(self) -> int:
        raise NotImplementedError

    @property
    def mileage(self) -> int:
        raise NotImplementedError

    @property
    def fuel_type(self) -> str:
        raise NotImplementedError

    @property
    def engine_volume(self) -> int:
        raise NotImplementedError

    def as_model(self) -> Ad:
        return Ad(
            url=self.url,
            external_id=self.id,
            title=self.title,
            price=self.price,
            production_year=self.production_year,
            mileage=self.mileage,
            fuel_type=self.fuel_type,
            engine_volume=self.engine_volume,
            # description=
            renewed_at=self.renewed_at,
        )


class Provider:
    def get_ads(self, *args, **kwargs) -> list[AdInfo]:
        raise NotImplementedError
