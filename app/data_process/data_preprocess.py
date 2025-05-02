import numpy as np
import pandas as pd
from geopy.distance import geodesic
import json

from ..settings import settings


def get_metro_df_by_city(city: str) -> pd.DataFrame:
    with open(f'./data/{city}/underground.json', 'r', encoding='utf-8') as f:
        metro_data = json.load(f)
        new_data = []
        for metro in metro_data:
            coords = metro_data[metro]
            new_data.append({'name': metro, 'lat': coords[0], 'long': coords[1]})
    return pd.DataFrame.from_records(new_data)


def find_nearest_metro(row: pd.DataFrame, metro_df: pd.DataFrame) -> str | None:
    """Возвращает название ближайшей станции метро."""
    if pd.isna(row['underground_name']):
        try:
            # Получаем координаты квартиры
            flat_point = (row['latitude'], row['longitude'])

            # Рассчитываем расстояния до всех станций
            distances = metro_df.apply(
                lambda x: geodesic(flat_point, (x['lat'], x['long'])).meters,
                axis=1
            )

            # Находим ближайшую
            nearest_idx = distances.idxmin()
            return metro_df.iloc[nearest_idx]['name']
        except:
            return None
    else:
        return row['underground_name']

def drop_useless(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(by=["cianId", "addedTimestamp"], ascending=[True, True])
    df = df.drop_duplicates(subset=["cianId"], keep="last")
    df = df.drop(["cianId"], axis=1)
    df = df[(df.lap > 0.1) | (df.lap.isna())]
    df = df[~((df["kap"] >= 0.6) & (df["flatType"] == "studio") | (df["kap"] >= 0.75))]
    df = df.reset_index(drop=True)
    return df

def fill_simple_fields(df: pd.DataFrame, city_name: str) -> pd.DataFrame:
    metro_df = get_metro_df_by_city(city_name)
    df["isApartments"] = df["isApartments"].fillna(False).astype(np.bool_)
    df["balconiesCount"] = df["balconiesCount"].fillna(0).astype(np.int64)
    df["loggiasCount"] = df["loggiasCount"].fillna(0).astype(np.int64)
    df["hasFurniture"] = df["hasFurniture"].fillna(False).astype(np.bool_)
    df["roomsCount"] = (
        df["roomsCount"].fillna(0).astype(np.int64)
    )  # because NaN is set when flayType == studio
    df["underground_name"] = df.apply(lambda x: find_nearest_metro(x, metro_df), axis=1)
    df["building_material"] = df["building_material"].fillna("unknown")
    df["elevators"] = np.where(
        df["elevators"].isna(),
        np.where(
            df["floors_count"] <= 12,
            np.where(df["floors_count"] <= 5, 0, 1),
            2,
        ),
        df["elevators"],
    )
    df["elevators"] = df["elevators"].astype(np.int64)
    df["parking"] = df["parking"].fillna("open")
    return df

def fill_areas(df: pd.DataFrame) -> pd.DataFrame:
    from sklearn.experimental import enable_iterative_imputer
    from sklearn.impute import IterativeImputer
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.compose import ColumnTransformer

    df_copy = df.copy()
    df_copy['isApartments'] = df_copy['isApartments'].astype(int)
    numeric_features = ['isApartments', 'totalArea', 'roomsCount', 'balconiesCount', 'loggiasCount', 'lap', 'kap']
    categorical_features = ['flatType']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ])
    imputer = IterativeImputer(
        estimator=RandomForestRegressor(n_estimators=50),
        initial_strategy='median',
        max_iter=20,
        random_state=42
    )

    X = preprocessor.fit_transform(df_copy)
    X_dense = X.toarray() if hasattr(X, "toarray") else X
    X_imputed = imputer.fit_transform(X_dense)

    df_copy['lap'] = np.where(df_copy['lap'].isna(), X_imputed[:, 5], df_copy['lap'])
    df_copy['kap'] = np.where(df_copy['kap'].isna(), X_imputed[:, 6], df_copy['kap'])
    df_copy["livingArea"] = df_copy["livingArea"].fillna(round(df_copy["lap"] * df_copy["totalArea"], 1))
    df_copy["kitchenArea"] = df_copy["kitchenArea"].fillna(round(df_copy["kap"] * df_copy["totalArea"], 1))
    df_copy = df_copy.drop(["kap", "lap"], axis=1)

    return df_copy

def preprocess_cian_data() -> None:
    for city in settings.CITIES:
        df = pd.read_csv(f"./data/{city['name']}/cian/dataset.csv")
        df["lap"] = df["livingArea"] / df["totalArea"]
        df["kap"] = df["kitchenArea"] / df["totalArea"]
        df = drop_useless(df)
        df = fill_simple_fields(df, city['name'])
        df = fill_areas(df)
        df.to_csv(f"./data/{city['name']}/cian/clean_dataset.csv", index=False)
