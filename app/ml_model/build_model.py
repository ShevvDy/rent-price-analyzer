import joblib
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

from ..data_process import get_train_test_data


def build_models() -> None:
    X_train, X_test, Y_train, Y_test = get_train_test_data()
    data_name_map = {
        "x_train": X_train,
        "x_test": X_test,
        "y_train": Y_train,
        "y_test": Y_test,
    }
    for obj_name in data_name_map:
        joblib.dump(data_name_map[obj_name], f"./data/model/{obj_name}_data.pkl")

    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=23,
        max_features=7,
        n_jobs=-1,
        random_state=42,
    )
    rf.fit(X_train, Y_train.values.ravel())
    joblib.dump(rf, "./data/model/rf_model.pkl")

    xgb = XGBRegressor(
        max_depth=8,
        learning_rate=0.08,
        n_estimators=300,
        reg_alpha=8,
        random_state=42,
        n_jobs=-1
    )
    xgb.fit(X_train, Y_train.values.ravel())
    joblib.dump(xgb, "./data/model/xgb_model.pkl")
