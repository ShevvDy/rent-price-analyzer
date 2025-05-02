from app.data_process.collect_data import get_cian_data
from app.data_process.data_cleaning import clean_data
import datetime
import time


# cur_date = datetime.datetime.now()
# planned_date = datetime.datetime(cur_date.year, cur_date.month, cur_date.day, 20)
# delta = (planned_date - cur_date).total_seconds()
# time.sleep(delta)
get_cian_data()
clean_data()
