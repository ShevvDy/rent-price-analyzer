from datetime import datetime

import joblib
import pandas as pd
import numpy as np

from ..models import City
from ..util.geo_objects import haversine, add_distances_to_geo_objects, find_nearest_metro, get_metro_df_by_city, get_metro_data_by_city
from ..util.address import get_address_info


def get_rental_price(data: dict) -> dict:
    addr_data = get_address_info(data['address'])
    if addr_data is None:
        raise Exception(f'Address {data["address"]} not found')
    city = City.get_by_name_ru(addr_data[0])
    if not city or not city.is_in_model:
        raise Exception(f'City {addr_data[0]} is not currently supported')
    data['city_district'] = f"{addr_data[0]}, {addr_data[1]}"
    data['latitude'] = addr_data[2]
    data['longitude'] = addr_data[3]
    data['addedTimestamp'] = datetime.now().timestamp()

    df = pd.DataFrame([data])
    flat_area = data["totalArea"]
    binary_cols = ["isApartments", "hasFurniture", "has_underground_parking", 'isPremium']
    for col in binary_cols:
        df[col] = df[col].astype(int)

    metro_data = get_metro_data_by_city(city.short_name)
    df['underground_name'] = np.nan
    metro_df = get_metro_df_by_city(city.short_name)
    df["underground_name"] = df.apply(lambda x: find_nearest_metro(x, metro_df), axis=1)
    df['underground_lat'] = df['underground_name'].map(lambda x: metro_data[x][0])
    df['underground_lon'] = df['underground_name'].map(lambda x: metro_data[x][1])
    parks = pd.read_csv(f'./data/{city.short_name}/parks.csv')
    schools = pd.read_csv(f'./data/{city.short_name}/schools.csv')
    malls = pd.read_csv(f'./data/{city.short_name}/malls.csv')
    df = add_distances_to_geo_objects(df, parks, 'park')
    df = add_distances_to_geo_objects(df, schools, 'school')
    df = add_distances_to_geo_objects(df, malls, 'mall')
    center_lat, center_lon = city.center_lat, city.center_lon  # Координаты центра
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
    for col in ['city_district', 'building_material']:
        encoder = joblib.load(f"./data/model/{col}_encoder.pkl")
        df[col + "_encoded"] = encoder.transform(df[col])
        df = df.drop(col, axis=1)
        df[col + "_encoded"] = df[col + "_encoded"].fillna(0.0)

    model = joblib.load("./data/model/best_model.pkl")
    X_train = joblib.load("./data/model/x_train_data.pkl")
    df = df[X_train.columns]
    prediction = model.predict(df)
    return {'status': 'success', 'price_by_meter': float(prediction[0]), 'total_price': int(round(prediction[0] * flat_area))}