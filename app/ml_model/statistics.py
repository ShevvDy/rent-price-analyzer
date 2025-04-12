import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score


X_test = joblib.load("./data/model/x_test_data.pkl")
Y_test = joblib.load("./data/model/y_test_data.pkl")
X_train = joblib.load("./data/model/x_train_data.pkl")
Y_train = joblib.load("./data/model/y_train_data.pkl")


def print_metrics(y_true: pd.Series, y_predicted: pd.Series, model):
    print(f'Среднее значение: {y_true.mean():.2f}')
    print(f"MAE: {mean_absolute_error(y_true, y_predicted):.2f}")
    print(f"MSE: {mean_squared_error(y_true, y_predicted):.2f}")
    print(f"RMSE: {np.sqrt(mean_squared_error(y_true, y_predicted)):.2f}")
    print(f"R²: {r2_score(y_true, y_predicted):.4f}")

    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(
        model,
        X_train,
        Y_train.values.ravel(),
        cv=cv,
        scoring="neg_root_mean_squared_error",
        n_jobs=-1,
    )

    print(f"Кросс-валидация RMSE: {-scores.mean():.2f} ± {scores.std():.2f}\n")


def get_statistics_by_model(model_name: str = 'xgb', is_test: bool = True) -> None:
    model = joblib.load(f"./data/model/{model_name}_model.pkl")
    X = X_test if is_test else X_train
    Y = Y_test if is_test else Y_train
    y_pred = model.predict(X)

    print(f"Результаты на {'тестовых' if is_test else 'тренировочных'} данных для модели {model_name}:")
    print_metrics(Y, y_pred, model)

    # importance = pd.DataFrame(
    #     {"feature": X_train.columns, "importance": model.feature_importances_}
    # ).sort_values("importance", ascending=False)
    #
    # print(importance)
