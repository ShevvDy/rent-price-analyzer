from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import relationship, Mapped
from .database import Base


if TYPE_CHECKING:
    from .user import User


class EstimatedHome(Base):
    __tablename__ = 'estimated_home'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('user.id'), nullable=False)
    address = Column(String, nullable=False)
    total_area = Column(Float, nullable=False)
    is_apartments = Column(Boolean, nullable=False)
    floors_count = Column(Integer, nullable=False)
    floor_number = Column(Integer, nullable=False)
    rooms_count = Column(Integer, nullable=False)
    building_material = Column(String, nullable=False)
    elevators = Column(Integer, nullable=False)
    balconies_count = Column(Integer, nullable=False)
    has_furniture = Column(Boolean, nullable=False)
    compute_date = Column(BigInteger, nullable=False)
    computed_price = Column(Integer, nullable=False)
    similar_objects = Column(JSON, default='[]')
    graphic = Column(JSON, default='{}', nullable=False)

    user: Mapped['User'] = relationship(back_populates='estimated_homes')
