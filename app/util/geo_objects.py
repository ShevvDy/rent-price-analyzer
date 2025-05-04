from math import radians, sin, cos, asin, sqrt

import numpy as np
import pandas as pd
import requests
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import time
import json


def get_metro_by_city(city: dict, undergrounds: list) -> None:
    coordinates = {}
    geolocator = Nominatim(user_agent="metro_spb_app")
    for station in undergrounds:
        location = geolocator.geocode(f"станция метро {station}, {city['name_ru']}, Россия")
        if location:
            coordinates[station] = [location.latitude, location.longitude]
        time.sleep(1)  # Чтобы избежать блокировки
    with open(f'./data/{city["name"]}/underground.json', 'w') as f:
        json.dump(coordinates, f, indent=4)


def get_geo_objects_data(city: dict) -> None:
    """Возвращает DataFrame с координатами объектов инфраструктуры"""
    overpass_url = "https://overpass-api.de/api/interpreter"

    # Запросы для разных типов объектов
    queries = {
        'park': f"""
            [out:json];
            area["name"="{city['name_ru']}"]->.searchArea;
            (
                node["leisure"="park"](area.searchArea);
                way["leisure"="park"](area.searchArea);
            );
            out center;
        """,
        'school': f"""
            [out:json];
            area["name"="{city['name_ru']}"]->.searchArea;
            (
                node["amenity"="school"](area.searchArea);
                way["amenity"="school"](area.searchArea);
            );
            out center;
        """,
        'mall': f"""
            [out:json];
            area["name"="{city['name_ru']}"]->.searchArea;
            (
                node["shop"="mall"](area.searchArea);
                way["shop"="mall"](area.searchArea);
            );
            out center;
        """
    }

    for poi_type in queries.keys():
        response = requests.post(overpass_url, data={'data': queries[poi_type]})
        data = response.json()

        poi_data = []
        for element in data['elements']:
            if 'tags' in element and 'name' in element['tags']:
                if 'center' not in element:
                    poi_data.append({
                        'name': element['tags']['name'],
                        'lat': element['lat'],
                        'lon': element['lon']
                    })
                else:
                    poi_data.append({
                        'name': element['tags']['name'],
                        'lat': element['center']['lat'],
                        'lon': element['center']['lon']
                    })
        pd.DataFrame(poi_data).to_csv(f'./data/{city["name"]}/{poi_type}s.csv', index=False)


def get_metro_data_by_city(city: str) -> dict | None:
    try:
        with open(f'./data/{city}/underground.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def get_metro_df_by_city(city: str) -> pd.DataFrame | None:
    metro_data = get_metro_data_by_city(city)
    df_data = []
    if not metro_data:
        return None
    for metro in metro_data:
        coords = metro_data[metro]
        df_data.append({'name': metro, 'lat': coords[0], 'lon': coords[1]})
    return pd.DataFrame.from_records(df_data)


def find_nearest_metro(row: pd.DataFrame, metro_df: pd.DataFrame | None) -> str | None:
    """Возвращает название ближайшей станции метро."""
    if metro_df is None:
        return None
    if pd.isna(row['underground_name']):
        try:
            # Получаем координаты квартиры
            flat_point = (row['latitude'], row['longitude'])

            # Рассчитываем расстояния до всех станций
            distances: pd.DataFrame = metro_df.apply(
                lambda x: geodesic(flat_point, (x['lat'], x['lon'])).meters,
                axis=1
            )

            # Находим ближайшую
            nearest_idx = distances.idxmin()
            return metro_df.iloc[nearest_idx]['name']
        except:
            return None
    else:
        return row['underground_name']


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Конвертация в радианы
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    # Разницы координат
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    # Формула Хаверсина
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    # Радиус Земли в километрах (6371 км)
    return c * 6371


def add_distances_to_geo_objects(df: pd.DataFrame, poi_df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Добавляет расстояние до ближайшего объекта инфраструктуры"""
    from sklearn.neighbors import BallTree

    # Конвертация в радианы
    poi_coords = np.deg2rad(poi_df[['lat', 'lon']].values)
    flat_coords = np.deg2rad(df[['latitude', 'longitude']].values)

    # Поиск ближайшего
    tree = BallTree(poi_coords, metric='haversine')
    distances, _ = tree.query(flat_coords, k=1)

    # Конвертация в метры (6371000 - радиус Земли)
    df[f'distance_to_{prefix}'] = distances * 6371000
    return df
