from typing import Optional
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Base(db.Model):
    __abstract__ = True

    def add(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete(self) -> None:
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_all(cls) -> list['Base']:
        return cls.query.order_by(cls.id).all()

    @classmethod
    def get_item_by_id(cls, item_id: int) -> Optional['Base']:
        return cls.query.filter(cls.id == item_id).first()
