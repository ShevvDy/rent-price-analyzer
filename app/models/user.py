from typing import Optional
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from .database import Base
from .estimated_home import EstimatedHome


class User(UserMixin, Base):
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    patronymic = Column(String)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    estimated_homes: Mapped[list['EstimatedHome']] = relationship(back_populates='user', order_by=EstimatedHome.compute_date.desc())

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        return cls.query.filter(cls.email == email).first()
