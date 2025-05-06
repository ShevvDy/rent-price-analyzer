import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score


X_test = joblib.load("./data/model/x_test_data.pkl")
Y_test = joblib.load("./data/model/y_test_data.pkl")
X_train = joblib.load("./data/model/x_train_data.pkl")
Y_train = joblib.load("./data/model/y_train_data.pkl")


def get_metrics(y_true: pd.Series, y_predicted: pd.Series, model) -> dict:
    # cv = KFold(n_splits=5, shuffle=True, random_state=42)
    # scores = cross_val_score(
    #     model,
    #     X_train,
    #     Y_train.values.ravel(),
    #     cv=cv,
    #     scoring="neg_root_mean_squared_error",
    #     n_jobs=-1,
    # )
    return {
        'mean': round(y_true.mean(), 2),
        'mae': round(mean_absolute_error(y_true, y_predicted), 2),
        'mse': round(mean_squared_error(y_true, y_predicted), 2),
        'rmse': round(np.sqrt(mean_squared_error(y_true, y_predicted)), 2),
        'r^2': round(r2_score(y_true, y_predicted), 4),
        # 'cv-rmse': f'{-scores.mean():.2f} ± {scores.std():.2f}',
    }

def print_metrics(metrics: dict) -> None:
    print(f"Среднее значение: {metrics['mean']}")
    print(f"MAE: {metrics['mae']}")
    print(f"MSE: {metrics['mse']}")
    print(f"RMSE: {metrics['rmse']}")
    print(f"R²: {metrics['r^2']}")
    print(f"Кросс-валидация RMSE: {metrics.get('cv-rmse')}\n")

def get_statistics_by_model(model_name: str = 'xgb', is_test: bool = True) -> dict:
    model = joblib.load(f"./data/model/{model_name}_model.pkl")
    X = X_test if is_test else X_train
    Y = Y_test if is_test else Y_train
    y_pred = model.predict(X)

    print(f"Результаты на {'тестовых' if is_test else 'тренировочных'} данных для модели {model_name}:")
    metrics = get_metrics(Y, y_pred, model)
    print_metrics(metrics)

    # importance = pd.DataFrame(
    #     {"feature": X_train.columns, "importance": model.feature_importances_}
    # ).sort_values("importance", ascending=False)
    #
    # print(importance)
    return metrics

def find_best_model() -> None:
    metrics = {name: get_statistics_by_model(name) for name in ['xgb', 'rf']}
    for model_name in metrics.keys():
        model_metrics = metrics[model_name]
        model_metrics['sum_score'] = model_metrics['r^2'] + (1.0 - model_metrics['mae'] / model_metrics['mean'])
    if metrics['xgb']['sum_score'] > metrics['rf']['sum_score']:
        best_model = 'xgb'
    else:
        best_model = 'rf'
    joblib.dump(joblib.load(f"./data/model/{best_model}_model.pkl"), "./data/model/best_model.pkl")
