import datetime
import os
import random
import time

import pandas as pd
import requests


simple_fields = [
    "isApartments",
    "balconiesCount",
    "kitchenArea",
    "totalArea",
    "flatType",
    "floorNumber",
    "loggiasCount",
    "hasFurniture",
    "addedTimestamp",
    "cianId",
    "roomsCount",
    "livingArea",
]


def log(text: str) -> None:
    print(f"{datetime.datetime.now()} - {text}")


def get_clean_dataframe(dirty_data: list[dict]) -> pd.DataFrame:
    clean_data = []
    for row in dirty_data:
        clean_row = {}
        for field in simple_fields:
            clean_row[field] = row.get(field)
        geo_data = row.get("geo") or {}
        coords = geo_data.get("coordinates") or {}
        clean_row["latitude"] = coords.get("lat")
        clean_row["longitude"] = coords.get("lng")
        addr_fields_mapping = {
            "location": "city",
            "raion": "district",
        }
        clean_row['isPremium'] = row.get('isPremium') or False
        for addr in geo_data.get("address") or []:
            addr_type = addr["type"]
            if addr_type in addr_fields_mapping and addr_fields_mapping[addr_type] not in clean_row:
                clean_row[addr_fields_mapping[addr_type]] = addr.get("name")
                continue
            if addr_type == "mikroraion":
                clean_row["district"] = addr.get("name")
        undergrounds = geo_data.get("undergrounds")
        closest_underground = undergrounds[0] if undergrounds is not None and len(undergrounds) > 0 else None
        if closest_underground is not None:
            clean_row["underground_name"] = closest_underground.get("name")
        else:
            clean_row["underground_name"] = None
        building_data = row.get("building") or {}
        clean_row["building_material"] = building_data.get("materialType")
        clean_row["elevators"] = building_data.get("passengerLiftsCount")
        clean_row["floors_count"] = building_data.get("floorsCount")
        clean_row["parking"] = (building_data.get("parking") or {}).get("type")
        clean_row["price"] = row["bargainTerms"]["priceRur"]
        clean_data.append(clean_row)
    return pd.DataFrame.from_records(clean_data)


def get_cian_data_by_city_room_page(city_id: int, room_type: int, page: int) -> dict | None:
    url = "https://api.cian.ru/search-offers/v2/search-offers-desktop/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 OPR/117.0.0.0",
        "Content-Type": "application/json",
        "Connection": "keep-alive",
    }
    body = {
        "jsonQuery": {
            "_type": "flatrent",
            "engine_version": {"type": "term", "value": 2},
            "region": {"type": "terms", "value": [city_id]},
            "for_day": {"type": "term", "value": "!1"},
            "page": {"type": "term", "value": page},
            "room": {"type": "terms", "value": [room_type]},
        }
    }
    req = requests.post(url, json=body, headers=headers)
    try:
        return req.json()["data"]
    except Exception as e:
        log(f"error during get data with room {room_type}, page {page}: {e}")
        return None


def get_cian_data_by_city_room(city: dict, room: int) -> pd.DataFrame:
    city_room_df = pd.DataFrame()
    i = 1
    while True:
        time.sleep(random.randint(3, 12))
        page_result = get_cian_data_by_city_room_page(city['id'], room, i)
        if page_result is None or len(page_result["offersSerialized"]) == 0:
            city_room_df = city_room_df.drop_duplicates()
            return city_room_df
        city_room_df = pd.concat([city_room_df, get_clean_dataframe(page_result["offersSerialized"])])
        i += 1


def get_cian_data_by_city(city: dict) -> None:
    log(f"started cian data collect for city {city['name']}")
    result_df = pd.DataFrame()
    room_types = [1, 2, 3, 4, 5, 6, 9]
    for room in room_types:
        room_df = get_cian_data_by_city_room(city, room)
        result_df = pd.concat([result_df, room_df])
    result_df.to_csv(f'./data/{city["name"]}/cian/{datetime.date.today()}.csv', index=False)
    log(f"finished cian data collect process for city {city['name']}, got {result_df.shape[0]} rows")


cities = [
    {'name': 'spb', 'id': 2},
    # {'name': 'moscow', 'id': 1},
]

def get_cian_data() -> None:
    log("started cian data collect process")
    for city in cities:
        dirname = f'./data/{city["name"]}/cian'
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        get_cian_data_by_city(city)
    log("finished cian data collect process")
