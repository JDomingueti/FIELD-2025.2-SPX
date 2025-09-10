import pandas as pd
from to_parquet import make_data_paths

def id_composta(trimestre):
    df = pd.read_parquet(trimestre)

    df["person_id"] = (
        df["UF"].astype(str).str.zfill(2) +
        df["UPA"].astype(str).str.zfill(9) +
        df["V1008"].astype(str).str.zfill(2) +
        df["V1014"].astype(str).str.zfill(2) +
        df["V2003"].astype(str).str.zfill(2)
        )
    
    return df