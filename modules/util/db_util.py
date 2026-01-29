
import pandas as pd
from modules.db.db_records import get_isak_full
from modules.util.isak_util import build_record_antropometrico
from modules.util.util import data_format, expand_all_json_columns

def get_isak():
    df_raw = get_isak_full(as_df=True)
    
    if df_raw.empty:
        return df_raw

    records_calculados = []

    for _, row in df_raw.iterrows():
        record = build_record_antropometrico(row.to_dict())
        records_calculados.append(record)

    df_final = pd.DataFrame(records_calculados)
    df_final = expand_all_json_columns(df_final)
    df_final = data_format(df_final)
    return df_final
