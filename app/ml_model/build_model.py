import joblib
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor


def build_models() -> None:
    X_train, X_test, Y_train, Y_test = [
        joblib.load(f"./data/model/{obj_name}_data.pkl") for obj_name in ["x_train", "x_test", "y_train", "y_test"]
    ]

    rf = RandomForestRegressor(
        n_estimators=500,
        max_depth=22,
        max_features=8,
        n_jobs=-1,
        random_state=42,
    )
    rf.fit(X_train, Y_train.values.ravel())
    joblib.dump(rf, "./data/model/rf_model.pkl")

    xgb = XGBRegressor(
        max_depth=12,
        learning_rate=0.08,
        n_estimators=700,
        reg_alpha=15,
        colsample_bylevel=0.4,
        random_state=42,
        n_jobs=-1
    )
    xgb.fit(X_train, Y_train.values.ravel())
    joblib.dump(xgb, "./data/model/xgb_model.pkl")
