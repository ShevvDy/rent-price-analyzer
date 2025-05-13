from app.data_process.collect_data import get_cian_data
from app.data_process.data_cleaning import clean_data
from app.data_process.prepare_data import prepare_data
from app_main import app
import datetime
import time


cur_date = datetime.datetime.now()
planned_date = datetime.datetime(cur_date.year, cur_date.month, cur_date.day, 19, 00)
delta = (planned_date - cur_date).total_seconds()
time.sleep(delta)
with app.app_context():
    get_cian_data()
    clean_data()
    prepare_data()
