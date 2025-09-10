import pandas as pd
from to_parquet import make_data_paths

def id_composta(file):
    df = pd.read_parquet(file)

    df["person_id"] = (
        df["UF"].astype(str).str.zfill(2) +
        df["UPA"].astype(str).str.zfill(9) +
        df["V1008"].astype(str).str.zfill(2) +
        df["V1014"].astype(str).str.zfill(2) +
        df["V2003"].astype(str).str.zfill(2)
        )
    
    return df

if __name__ == "__main__":
    y, t = input("Ano desejado: "), input("Trimestre desejado: ")
    
    _, file = make_data_paths(y, t)
    
    df = id_composta(file)
    
    df.to_parquet(file, index=False)
    
    
