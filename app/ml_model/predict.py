from datetime import datetime, timedelta

import json
import joblib
import pandas as pd
import plotly.express as px
import numpy as np
from flask_login import current_user

from ..models import City, EstimatedHome
from ..util.geo_objects import haversine, add_distances_to_geo_objects, find_nearest_metro, get_metro_df_by_city, get_metro_data_by_city
from ..util.address import get_address_short_info, get_formatted_address_by_coords


def get_nearest_neighbours(city: str, addr_lat: float, addr_lon: float) -> list[dict]:
    nearest = []

    df = pd.read_csv(f'./data/{city}/analogues_dataset.csv')
    df['distances'] = np.sqrt((addr_lat - df['latitude']) ** 2 + (addr_lon - df['longitude']) ** 2)
    df = df.sort_values('distances', ascending=True)

    for idx, row in df.iterrows():
        if len(nearest) == 3 or row['distances'] > 0.005:
            break
        formatted_address = get_formatted_address_by_coords(row['latitude'], row['longitude'])
        if formatted_address is None:
            continue
        cur_dict = {
            field: row[field] for field in [
                'kitchenArea',
                'totalArea',
                'livingArea',
                'hasFurniture',
                'addedTimestamp',
                'roomsCount',
                'elevators',
                'floorNumber',
                'floors_count',
                'price',
                'balconiesCount',
                'isApartments',
            ]
        }
        cur_dict['address'] = formatted_address
        nearest.append(cur_dict)
    return nearest

def get_historic_graphic_data(df: pd.DataFrame, model) -> dict:
    df_copy = df.copy()
    cur_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    # clean_dataset = pd.read_csv('./data/spb/clean_dataset.csv')
    # clean_min_date = datetime.fromtimestamp(clean_dataset['addedTimestamp'].min()).replace(
    #     hour=0, minute=0, second=0, microsecond=0, tzinfo=None
    # )
    # start_date = max(cur_date - timedelta(days=180), clean_min_date)
    start_date = datetime(year=2025, month=3, day=1)
    dates = []
    while start_date <= cur_date:
        dates.append(round(start_date.timestamp()))
        start_date += timedelta(days=1)
    df_copy = pd.concat([df_copy] * len(dates), ignore_index=True)
    df_copy['addedTimestamp'] = dates
    df_copy['predicted'] = model.predict(df_copy)
    df_copy['total_price'] = df_copy['predicted'] * df_copy['totalArea']
    df_copy['add_date'] = df_copy.apply(lambda x: datetime.fromtimestamp(x['addedTimestamp']).replace(day=1), axis=1)
    result = np.round(df_copy.groupby('add_date')['total_price'].mean() / 500) * 500
    fig = px.line(x=result.index, y=result.values, title='График изменения стоимости жилья во времени')
    fig.update_layout(template=None)
    graph_json = fig.to_dict()
    graph_json['data'][0]['x'] = [ts.strftime("%Y-%m-%d") for ts in result.index.tolist()]
    graph_json['data'][0]['y'] = result.values.tolist()
    graph_json['layout']['xaxis']['title']['text'] = 'Дата'
    graph_json['layout']['yaxis']['title']['text'] = 'Стоимость'
    return graph_json


def get_rental_price(data: dict) -> dict:
    addr_data = get_address_short_info(data['address'])
    if addr_data is None:
        raise Exception(f'Address {data["address"]} not found')
    city = City.get_by_name_ru(addr_data[0])
    if not city or not city.is_in_model:
        raise Exception(f'City {addr_data[0]} is not currently supported')
    data['city_district'] = f"{addr_data[0]}, {addr_data[1]}"
    data['latitude'] = addr_data[2]
    data['longitude'] = addr_data[3]
    data['addedTimestamp'] = round(datetime.now().timestamp())

    df = pd.DataFrame([data])
    flat_area = data["totalArea"]
    binary_cols = ["isApartments", "hasFurniture", "has_underground_parking", 'isPremium']
    for col in binary_cols:
        df[col] = df[col].astype(int)

    metro_data = get_metro_data_by_city(city)
    df['underground_name'] = np.nan
    metro_df = get_metro_df_by_city(city)
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
    total_price = round(prediction[0] * flat_area / 500) * 500
    similar_objects = get_nearest_neighbours(city.short_name, addr_data[2], addr_data[3])
    graph = get_historic_graphic_data(df, model)
    estimated_home = EstimatedHome(
        user=current_user,
        address=get_formatted_address_by_coords(addr_data[2], addr_data[3]),
        total_area=data['totalArea'],
        kitchen_area=data['kitchenArea'],
        living_area=data['livingArea'],
        is_apartments=data['isApartments'],
        floors_count=data['floors_count'],
        floor_number=data['floorNumber'],
        rooms_count=data['roomsCount'],
        building_material=data['building_material'],
        elevators=data['elevators'],
        balconies_count=data['balconiesCount'],
        has_furniture=data['hasFurniture'],
        compute_date=round(datetime.now().timestamp()),
        computed_price=total_price,
        similar_objects=similar_objects,
        graphic=json.dumps(graph),
    )
    estimated_home.add()
    return {
        'status': 'success',
        'total_price': total_price,
        'nearest_neighbours': similar_objects,
        'graph': graph
    }