import json
import os

import pandas as pd

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


def get_csv_from_files() -> None:
    data_dir = "./data/spb/cian"
    for dirname in sorted(os.listdir(data_dir)):
        if dirname in ['dataset.csv', 'clean_dataset.csv']:
            continue
        cur_dir = f"{data_dir}/{dirname}"
        files = sorted(os.listdir(cur_dir))
        if 'dataset.csv' in files:
            continue
        result_df = pd.DataFrame()
        for filename in sorted(os.listdir(cur_dir)):
            with open(f"{cur_dir}/{filename}", "r", encoding="utf-8") as f:
                file_data = json.load(f)
                file_df = get_clean_dataframe(file_data)
            result_df = pd.concat([result_df, file_df])
        result_df.to_csv(f"{cur_dir}/dataset.csv", index=False)
