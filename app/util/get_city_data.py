import pandas as pd
import requests
from geopy.geocoders import Nominatim
import time
import json
from datetime import date


def get_metro_by_city(city: dict, date_: date) -> None:
    df = pd.read_csv(f'./data/{city["name"]}/cian/{date_}.csv')
    undergrounds = df.underground_name.unique()
    coordinates = {}
    geolocator = Nominatim(user_agent="metro_spb_app")
    for station in undergrounds:
        location = geolocator.geocode(f"станция метро {station}, {city['name_ru']}, Россия")
        if location:
            coordinates[station] = [location.latitude, location.longitude]
        time.sleep(1)  # Чтобы избежать блокировки
    with open(f'./data/{city["name"]}/underground.json', 'w') as f:
        json.dump(coordinates, f, indent=4)


def get_poi_coordinates(city: dict) -> None:
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
