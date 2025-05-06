from datetime import datetime

import joblib
import pandas as pd
import numpy as np

from ..models import City
from ..util.geo_objects import haversine, add_distances_to_geo_objects, find_nearest_metro, get_metro_df_by_city, get_metro_data_by_city
from ..util.address import get_address_short_info, dadata_, geolocator


def get_nearest_neighbours(city: str, addr_lat: float, addr_lon: float) -> list[dict]:
    nearest = []

    df = pd.read_csv(f'./data/{city}/analogues_dataset.csv')
    df['distances'] = np.sqrt((addr_lat - df['latitude']) ** 2 + (addr_lon - df['longitude']) ** 2)
    df = df.sort_values('distances', ascending=True)

    for idx, row in df.iterrows():
        if len(nearest) == 3 or row['distances'] > 0.005:
            break
        try:
            addr = dadata_.geolocate('address', lat=row['latitude'], lon=row['longitude'])
            suggestion = addr['suggestions']['data']
            if not suggestion['street'] or not suggestion['house']:
                raise Exception
            district = addr['settlement']
            if district is None:
                nominatim_addr = geolocator.geocode(f"{row['latitude']}, {row['longitude']}", addressdetails=True)
                raw_addr = nominatim_addr.raw['address']
                district = (
                    raw_addr['city_district'].replace('округ', '').strip() if 'city_district' in raw_addr else None
                )
                district = district or addr.get('city_district')
            address_formers = [addr.get('city') or addr.get('region'), district, addr.get('street'), addr.get('house')]
        except:
            addr = geolocator.geocode(f"{row['latitude']}, {row['longitude']}", addressdetails=True)
            if not addr or not addr.raw:
                continue
            raw_addr = addr.raw['address']
            try:
                settlement = raw_addr.get('town')
                if not settlement:
                    city_district = (
                        raw_addr['city_district'].replace('округ', '').strip() if 'city_district' in raw_addr else None
                    )
                    if not city_district:
                        raise Exception
                    settlement = city_district
                address_formers = [raw_addr['state'], settlement, raw_addr['road'], raw_addr['house_number']]
            except:
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
        cur_dict['address'] = ', '.join(address_formers)
        nearest.append(cur_dict)
    return nearest

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
    data['addedTimestamp'] = datetime.now().timestamp()

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
    return {
        'status': 'success',
        'price_by_meter': float(prediction[0]),
        'total_price': round(prediction[0] * flat_area / 500) * 500,
        'nearest_neighbours': get_nearest_neighbours(city.short_name, addr_data[2], addr_data[3]),
    }