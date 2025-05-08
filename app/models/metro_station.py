from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, String, Integer, Float
from sqlalchemy.orm import relationship, Mapped
from .database import Base


if TYPE_CHECKING:
    from .city import City


class MetroStation(Base):
    __tablename__ = 'metro_station'

    id = Column(Integer, primary_key=True)
    city_id = Column(ForeignKey('city.id'), nullable=False)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)

    city: Mapped['City'] = relationship(back_populates='metro_stations')
