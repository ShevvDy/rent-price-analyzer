from dotenv import load_dotenv
from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    DADATA_TOKEN: str
    DADATA_SECRET: str
    SQLALCHEMY_DATABASE_URI: str
    SECRET_KEY: str

    CITIES: list[dict] = [
        {'name': 'spb', 'id': 2, 'name_ru': 'Санкт-Петербург', 'center': (59.9390012, 30.3158184), 'has_metro': True},
        {'name': 'moscow', 'id': 1, 'name_ru': 'Москва', 'center': (55.7540584, 37.62049), 'has_metro': True},
        {'name': 'nsk', 'id': 4897, 'name_ru': 'Новосибирск', 'center': (55.030204, 82.920430), 'has_metro': True},
        {'name': 'kazan', 'id': 4777, 'name_ru': 'Казань', 'center': (55.796317, 49.106092), 'has_metro': True},
        {'name': 'ekb', 'id': 4743, 'name_ru': 'Екатеринбург', 'center': (56.838011, 60.597474), 'has_metro': True},
        {'name': 'krasnoyarsk', 'id': 4827, 'name_ru': 'Красноярск', 'center': (56.010543, 92.852581), 'has_metro': False},
        {'name': 'nizh_novg', 'id': 4885, 'name_ru': 'Нижний Новгород', 'center': (56.326797, 44.006516), 'has_metro': True},
        {'name': 'chlb', 'id': 5048, 'name_ru': 'Челябинск', 'center': (55.159902, 61.402554), 'has_metro': False},
        {'name': 'ufa', 'id': 176245, 'name_ru': 'Уфа', 'center': (54.735152, 55.958736), 'has_metro': False},
        {'name': 'krasnodar', 'id': 4820, 'name_ru': 'Краснодар', 'center': (45.035470, 38.975313), 'has_metro': False},
    ]


settings = Settings()
