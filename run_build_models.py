from app.ml_model.build_model import build_models
build_models()


from app.ml_model.statistics import get_statistics_by_model
get_statistics_by_model('xgb')
get_statistics_by_model('rf')
