from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Text, create_engine, DateTime, select, func, Boolean
from settings import settings
from datetime import datetime
from typing import Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm.session import Session as SQLASession


Base = declarative_base()
engine = create_engine(f'sqlite:///{settings.db_path.absolute()}')
Session = sessionmaker(engine)


class AdIsNotFound(Exception):
    """Объявление не найдено в базе по его внешнему ID"""


class Ad(Base):
    __tablename__ = 'ad'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)

    external_id = Column(String, nullable=False)

    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    production_year = Column(Integer, nullable=False)
    mileage = Column(Integer, nullable=False)
    fuel_type = Column(String, nullable=False)
    engine_volume = Column(Integer, nullable=False)

    description = Column(Text)
    renewed_at = Column(DateTime(timezone=True))

    interesting = Column(Boolean, default=False, server_default='false')

    def __str__(self) -> str:
        return f"{self.id}({self.external_id}): {self.title} FOR {self.price} ({self.url})"

    @property
    def match_fields(self) -> tuple[str, ...]:
        return 'title', 'price', 'description'

    def get_diff(self, other_model: 'Ad') -> dict:
        diff = {}
        for field in self.match_fields:
            new_value = getattr(other_model, field)
            old_value = getattr(self, field)
            if new_value != old_value:
                diff[field] = new_value
        return diff

    def is_changed(self, other_model: 'Ad') -> bool:
        if self.get_diff(other_model):
            return True
        return False

    @classmethod
    def most_recent_version(cls, session: SQLASession, external_id: str) -> 'Ad':
        most_recent_versions_ids = select(cls.id, func.max(cls.created_at)).group_by(cls.external_id).subquery()
        query = select(cls).join(most_recent_versions_ids, most_recent_versions_ids.c.id == cls.id)

        query = query.where(Ad.external_id == external_id)

        try:
            return session.execute(query).scalar_one()
        except NoResultFound:
            raise AdIsNotFound(external_id)

    @classmethod
    def all_versions(cls, session: SQLASession, external_id: str) -> list['Ad']:
        query = select(cls).where(cls.external_id == external_id).order_by(cls.created_at)
        versions = [x for x in session.execute(query).scalars()]
        return versions

    def get_attribute_history(self, session: SQLASession, attribute_name: str) -> dict:
        versions = self.all_versions(session=session, external_id=self.external_id)
        return {x.created_at: getattr(x, attribute_name) for x in versions}

    def add_version(self, session: SQLASession, ad_info) -> Optional['Ad']:
        new_version = ad_info.as_model()
        if new_version.is_changed(self):
            session.add(new_version)
            session.flush()
            return new_version

    @staticmethod
    def create(session: SQLASession, ad_info) -> 'Ad':
        ad = ad_info.as_model()
        session.add(ad)
        session.flush()
        return ad
