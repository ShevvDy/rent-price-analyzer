import json
import os
from datetime import datetime

import joblib
import pandas as pd
import numpy as np
from dadata import Dadata

from ..data_process import add_poi_distances, find_nearest_metro, haversine


with open('./data/spb/underground.json', 'r', encoding='utf-8') as f:
    metro_data = json.load(f)


def get_dadata_info_by_address(address: str) -> tuple[str, str, float, float] | None:
    dadata_ = Dadata(os.getenv('DADATA_TOKEN'), os.getenv('DADATA_SECRET'))
    addr_info = dadata_.clean('address', address)
    if addr_info['qc_geo'] != 0:
        return None
    return addr_info['region'], addr_info['settlement'] or addr_info['city_district'], float(addr_info['geo_lat']), float(addr_info['geo_lon'])


def get_rental_price(data: dict) -> dict:
    addr_data = get_dadata_info_by_address(data['address'])
    if addr_data is None:
        raise Exception(f'Address {data["address"]} not found')
    data['city'] = addr_data[0]
    data['district'] = addr_data[1]
    data['latitude'] = addr_data[2]
    data['longitude'] = addr_data[3]
    data['addedTimestamp'] = datetime.now().timestamp()

    df = pd.DataFrame([data])
    flat_area = data["totalArea"]
    binary_cols = ["isApartments", "hasFurniture", "has_underground_parking", 'isPremium']
    for col in binary_cols:
        df[col] = df[col].astype(int)

    df['underground_name'] = np.nan
    df["underground_name"] = df.apply(lambda x: find_nearest_metro(x), axis=1)
    df['underground_lat'] = df['underground_name'].map(lambda x: metro_data[x][0])
    df['underground_lon'] = df['underground_name'].map(lambda x: metro_data[x][1])
    parks = pd.read_csv('./data/spb/spb_parks.csv')
    schools = pd.read_csv('./data/spb/spb_schools.csv')
    malls = pd.read_csv('./data/spb/spb_malls.csv')
    df = add_poi_distances(df, parks, 'park')
    df = add_poi_distances(df, schools, 'school')
    df = add_poi_distances(df, malls, 'mall')
    center_lat, center_lon = 59.9390012, 30.3158184  # Координаты центра СПб
    df["distance_to_center"] = df.apply(
        lambda row: haversine(row["latitude"], row["longitude"], center_lat, center_lon),
        axis=1,
    )
    df['metro_distance'] = df.apply(
        lambda row: haversine(row["latitude"], row["longitude"], row['underground_lat'], row['underground_lon']),
        axis=1)
    material_mapping = {
        'stalin': 'old',
        'aerocreteBlock': 'block',
        'unknown': 'other',
    }
    df["building_material"] = df["building_material"].replace(material_mapping)
    df = df.drop(['underground_lat', 'underground_lon', "latitude", "longitude", 'address'], axis=1)

    # 3. Частотное кодирование
    for col in ["city", "district", "underground_name", 'building_material']:
        encoder = joblib.load(f"./staff_data/{col}_encoder.pkl")
        df[col + "_encoded"] = encoder.transform(df[col])
        df = df.drop(col, axis=1)
        df[col + "_encoded"] = df[col + "_encoded"].fillna(0.0)

    model = joblib.load("./staff_data/xgb_model.pkl")
    X_train = joblib.load("./staff_data/x_train_data.pkl")
    df = df[X_train.columns]
    prediction = model.predict(df)
    return {'status': 'success', 'price_by_meter': float(prediction[0]), 'total_price': int(round(prediction[0] * flat_area))}