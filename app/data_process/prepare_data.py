import joblib
import pandas as pd
from category_encoders import TargetEncoder
from sklearn.model_selection import train_test_split
from scipy.stats import median_abs_deviation

from ..models import City
from ..util.geo_objects import get_metro_data_by_city, haversine, add_distances_to_geo_objects


def calculate_groupwise_zscore(group):
    # Находим медиану для каждой группы
    median_price = group['price_by_meter'].median()

    # Вычисляем медианное абсолютное отклонение (MAD)
    mad_price = median_abs_deviation(group['price_by_meter'], scale='normal')

    # Вычисляем модифицированный Z-score для каждой группы
    group['Modified_Z_Score'] = (group['price_by_meter'] - median_price) / mad_price

    return group


def process_data_by_city(city: 'City') -> pd.DataFrame:
    df = pd.read_csv(f"./data/{city.short_name}/clean_dataset.csv")
    parks = pd.read_csv(f'./data/{city.short_name}/parks.csv')
    schools = pd.read_csv(f'./data/{city.short_name}/schools.csv')
    malls = pd.read_csv(f'./data/{city.short_name}/malls.csv')
    df = add_distances_to_geo_objects(df, parks, 'park')
    df = add_distances_to_geo_objects(df, schools, 'school')
    df = add_distances_to_geo_objects(df, malls, 'mall')
    df['has_underground_parking'] = df['parking'].apply(lambda x: x == 'underground')
    binary_cols = ["isApartments", "hasFurniture", 'has_underground_parking', 'isPremium']
    for col in binary_cols:
        df[col] = df[col].astype(int)
    df["price_by_meter"] = round(df["price"] / df["totalArea"], 2)
    center_lat = city.center_lat
    center_lon = city.center_lon
    df["distance_to_center"] = df.apply(
        lambda row: haversine(row["latitude"], row["longitude"], center_lat, center_lon),
        axis=1,
    )
    metro_data = get_metro_data_by_city(city)
    if metro_data:
        df['underground_lat'] = df['underground_name'].map(lambda x: metro_data[x][0])
        df['underground_lon'] = df['underground_name'].map(lambda x: metro_data[x][1])
        df['metro_distance'] = df.apply(
            lambda row: haversine(row["latitude"], row["longitude"], row['underground_lat'], row['underground_lon']),
            axis=1)
        df = df.drop(['underground_lat', 'underground_lon'], axis=1)
    else:
        df['metro_distance'] = 100.0
    material_mapping = {
        'stalin': 'old',
        'aerocreteBlock': 'block',
        'unknown': 'other',
    }
    df["building_material"] = df["building_material"].replace(material_mapping)
    df['balconiesCount'] = df['balconiesCount'] + df['loggiasCount']
    df = df.groupby(['city', 'district']).apply(calculate_groupwise_zscore)
    df = df[(df['Modified_Z_Score'] < 3.5) & (df['Modified_Z_Score'] > -3.5)]
    df.reset_index(drop=True, inplace=True)
    df['city_district'] = df.apply(lambda row: f"{row['city']}, {row['district']}", axis=1)
    df_copy = df.copy()
    df_copy = df_copy[[
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
        'latitude',
        'longitude',
    ]]
    binary_cols = ["isApartments", "hasFurniture"]
    for col in binary_cols:
        df_copy[col] = df_copy[col].astype(bool)
    df_copy.to_csv(f'./data/{city.short_name}/analogues_dataset.csv', index=False)
    df = df.drop(
        [
            "price",
            'parking',
            'flatType',
            "latitude",
            "longitude",
            'Modified_Z_Score',
            'loggiasCount',
            'underground_name',
            'has_underground_parking',
            'isPremium',
            'city',
            'district',
        ],
        axis=1
    )
    df.to_csv(f'./data/{city.short_name}/prepared_dataset.csv', index=False)
    return df


def prepare_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = pd.DataFrame()
    for city in City.get_all_cities_for_model():
        cur_df = process_data_by_city(city)
        df = pd.concat([df, cur_df])
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
    data_name_map = {
        "x_train": X_train,
        "x_test": X_test,
        "y_train": Y_train,
        "y_test": Y_test,
    }
    for obj_name in data_name_map:
        joblib.dump(data_name_map[obj_name], f"./data/model/{obj_name}_data.pkl")
    return X_train, X_test, Y_train, Y_test
