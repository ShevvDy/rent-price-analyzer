import pandas as pd
import os


def merge_cian_data() -> None:
    result_df = pd.DataFrame()
    data_dir = "./data/spb/cian"
    for dirname in sorted(os.listdir(data_dir)):
        if dirname in ['dataset.csv', 'clean_dataset.csv']:
            continue
        cur_dir = f"{data_dir}/{dirname}"
        try:
            cur_df = pd.read_csv(f'{cur_dir}/dataset.csv')
            result_df = pd.concat([result_df, cur_df])
        except FileNotFoundError:
            print(f'file dataset.csv in {cur_dir} not found')
    result_df = result_df.drop_duplicates()
    result_df.to_csv(f'{data_dir}/dataset.csv', index=False)
