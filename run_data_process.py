from app.data_process.convert_data_to_csv import get_csv_from_files
from app.data_process.data_preprocess import preprocess_cian_data
from app.data_process.merge_cian_data import merge_cian_data


get_csv_from_files()
merge_cian_data()
preprocess_cian_data()
