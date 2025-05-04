from typing import TYPE_CHECKING, Optional
from sqlalchemy import Column, Integer, String, Boolean, Float
from sqlalchemy.orm import relationship, Mapped
from .database import Base


if TYPE_CHECKING:
    from .metro_station import MetroStation


class City(Base):
    __tablename__ = 'city'

    id = Column(Integer, primary_key=True)
    short_name = Column(String, unique=True, nullable=False)
    name_ru = Column(String, unique=True, nullable=False)
    cian_id = Column(Integer, unique=True, nullable=False)
    center_lat = Column(Float, nullable=False)
    center_lon = Column(Float, nullable=False)
    is_in_model = Column(Boolean, default=False)

    metro_stations: Mapped[list['MetroStation']] = relationship(uselist=True, back_populates='city', lazy='selectin')

    @classmethod
    def get_all_cities_for_model(cls) -> list['City']:
        return cls.query.filter(cls.is_in_model.is_(True)).all()

    @classmethod
    def get_by_short_name(cls, short_name: str) -> Optional['City']:
        return cls.query.filter(cls.short_name == short_name).first()

    @classmethod
    def get_by_name_ru(cls, name_ru: str) -> Optional['City']:
        return cls.query.filter(cls.name_ru == name_ru).first()