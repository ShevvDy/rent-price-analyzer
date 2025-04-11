import datetime
import json
import os
import random
import time

import requests


def log(text: str) -> None:
    print(f"{datetime.datetime.now()} - {text}")


def get_cian_data_by_room_page(room_type: int, page: int) -> dict | None:
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
            "region": {"type": "terms", "value": [2]},
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


def get_cian_data_by_room(room: int) -> None:
    result = get_cian_data_by_room_page(room, 1)
    if result is None:
        return
    directory = f"./data/spb/cian/{datetime.date.today()}"
    if not os.path.exists(directory):
        os.mkdir(directory)
    with open(f"{directory}/{room}_1.json", "w", encoding="utf-8") as f:
        json.dump(result["offersSerialized"], f, indent=4, ensure_ascii=True)
    i = 2
    offers_count = len(result["offersSerialized"])
    while True:
        time.sleep(random.randint(5, 15))
        page_result = get_cian_data_by_room_page(room, i)
        if page_result is None:
            return
        if len(page_result["offersSerialized"]) == 0:
            log(f"finished getting data with room {room}, got {offers_count} rows")
            return
        offers = page_result["offersSerialized"]
        with open(f"{directory}/{room}_{i}.json", "w", encoding="utf-8") as f:
            json.dump(offers, f, indent=4, ensure_ascii=True)
        offers_count += len(offers)
        i += 1


def get_cian_data() -> None:
    log("started cian data collect")
    room_types = [1, 2, 3, 4, 5, 6, 9]
    for room in room_types:
        get_cian_data_by_room(room)
    log("finished cian data collect process")


get_cian_data()
