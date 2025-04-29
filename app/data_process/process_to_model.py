import json
from math import asin, cos, radians, sin, sqrt

import joblib
import numpy as np
import pandas as pd
from category_encoders import TargetEncoder
from sklearn.model_selection import train_test_split
from scipy.stats import median_abs_deviation


def get_metro_data_by_city(city: str) -> dict:
    with open(f'./data/{city}/underground.json', 'r', encoding='utf-8') as f:
        return json.load(f)


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


def add_poi_distances(df: pd.DataFrame, poi_df: pd.DataFrame, prefix: str) -> pd.DataFrame:
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


def calculate_groupwise_zscore(group):
    # Находим медиану для каждой группы
    median_price = group['price_by_meter'].median()

    # Вычисляем медианное абсолютное отклонение (MAD)
    mad_price = median_abs_deviation(group['price_by_meter'], scale='normal')

    # Вычисляем модифицированный Z-score для каждой группы
    group['Modified_Z_Score'] = (group['price_by_meter'] - median_price) / mad_price

    return group


def process_data_by_city(city: dict) -> pd.DataFrame:
    df = pd.read_csv(f"./data/{city['name']}/cian/clean_dataset.csv")
    metro_data = get_metro_data_by_city(city['name'])
    df['underground_lat'] = df['underground_name'].map(lambda x: metro_data[x][0])
    df['underground_lon'] = df['underground_name'].map(lambda x: metro_data[x][1])
    parks = pd.read_csv(f'./data/{city["name"]}/parks.csv')
    schools = pd.read_csv(f'./data/{city["name"]}/schools.csv')
    malls = pd.read_csv(f'./data/{city["name"]}/malls.csv')
    df = add_poi_distances(df, parks, 'park')
    df = add_poi_distances(df, schools, 'school')
    df = add_poi_distances(df, malls, 'mall')
    df['has_underground_parking'] = df['parking'].apply(lambda x: x == 'underground')
    binary_cols = ["isApartments", "hasFurniture", 'has_underground_parking', 'isPremium']
    for col in binary_cols:
        df[col] = df[col].astype(int)
    df["price_by_meter"] = round(df["price"] / df["totalArea"], 2)
    df = df.drop(["price", 'parking', 'flatType'], axis=1)
    center_lat, center_lon = city['center']
    df["distance_to_center"] = df.apply(
        lambda row: haversine(row["latitude"], row["longitude"], center_lat, center_lon),
        axis=1,
    )
    df['metro_distance'] = df.apply(
        lambda row: haversine(row["latitude"], row["longitude"], row['underground_lat'], row['underground_lon']),
        axis=1)
    df = df.drop(["latitude", "longitude", 'underground_lat', 'underground_lon'], axis=1)
    material_mapping = {
        'stalin': 'old',
        'aerocreteBlock': 'block',
        'unknown': 'other',
    }
    df["building_material"] = df["building_material"].replace(material_mapping)
    df['balconiesCount'] = df['balconiesCount'] + df['loggiasCount']
    df = df.groupby(['city', 'district']).apply(calculate_groupwise_zscore)
    df = df[(df['Modified_Z_Score'] < 3.5) & (df['Modified_Z_Score'] > -3.5)]
    df = df.drop(['Modified_Z_Score', 'loggiasCount'], axis=1)
    df.reset_index(drop=True, inplace=True)
    df['city_district'] = df.apply(lambda row: f"{row['city']}, {row['district']}", axis=1)
    df = df.drop(['underground_name', 'has_underground_parking', 'isPremium', 'city', 'district'], axis=1)
    df.to_csv(f'./data/{city["name"]}/cian/prepared_dataset.csv', index=False)
    return df


def get_train_test_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df_msc = process_data_by_city({'name': 'moscow', 'id': 1, 'name_ru': 'Москва', 'center': (55.7540584, 37.62049)})
    df_spb = process_data_by_city({'name': 'spb', 'id': 2, 'name_ru': 'Санкт-Петербург', 'center': (59.9390012, 30.3158184)})
    df = pd.concat([df_spb, df_msc])
    X = df.drop("price_by_meter", axis=1)
    Y = df["price_by_meter"]
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.1, random_state=42)
    encoders_map = {field_name: TargetEncoder() for field_name in ['city_district', 'building_material']}
    for col in encoders_map:
        encoder = encoders_map[col]
        X_train[col + "_encoded"] = encoder.fit_transform(X_train[col], Y_train)
        X_test[col + "_encoded"] = encoder.transform(X_test[col])
        X_train = X_train.drop(col, axis=1)
        X_test = X_test.drop(col, axis=1)
        joblib.dump(encoder, f"./data/model/{col}_encoder.pkl")

    return X_train, X_test, Y_train, Y_test
