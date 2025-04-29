from dotenv import load_dotenv
from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    DADATA_TOKEN: str
    DADATA_SECRET: str

    CITIES: list[dict] = [
        {'name': 'spb', 'id': 2, 'name_ru': 'Санкт-Петербург', 'center': (59.9390012, 30.3158184)},
        {'name': 'moscow', 'id': 1, 'name_ru': 'Москва', 'center': (55.7540584, 37.62049)},
        {'name': 'kazan', 'id': 4777, 'name_ru': 'Казань', 'center': (55.796317, 49.106092)}
    ]


settings = Settings()

cities = [
    {'name': 'spb', 'id': 2, 'name_ru': 'Санкт-Петербург', 'center': (59.9390012, 30.3158184)},
    {'name': 'moscow', 'id': 1, 'name_ru': 'Москва', 'center': (55.7540584, 37.62049)},
    {'name': 'kazan', 'id': 4777, 'name_ru': 'Казань', 'center': (55.796317, 49.106092)}
]