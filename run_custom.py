import os

import pandas as pd
import json

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
        clean_row['isPremium'] = row.get('isPremium') or False
        clean_row['city'] = 'Санкт-Петербург'
        districts = geo_data.get("districts") or []
        if not districts:
            continue
        fd = districts[0]
        if any(char.isdigit() for char in fd.get('name')):
            if len(districts) > 1:
                fd = districts[1]
            else:
                continue
        clean_row['district'] = fd.get('name')
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


# result_df = pd.DataFrame()
# dirname = './data/spb/cian/2025-04-17'
# for filename in os.listdir(dirname):
#     with open(f'{dirname}/{filename}', 'r') as f:
#         data = json.load(f)
#     file_df = get_clean_dataframe(data)
#     result_df = pd.concat([result_df, file_df])
# result_df.drop_duplicates()
# result_df.to_csv(f'{dirname}.csv', index=False)
from app.util.get_city_data import get_poi_coordinates
get_poi_coordinates({'name': 'moscow', 'id': 1, 'name_ru': 'Москва', 'center': (55.7540584, 37.62049)})
