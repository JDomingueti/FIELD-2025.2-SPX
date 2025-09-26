import pandas as pd
from to_parquet import make_data_paths

def parear(file_n, file_n4):
    
    df_n = pd.read_parquet(file_n)
    df_n4 = pd.read_parquet(file_n4)
    
    df_n = df_n[df_n["V1014"] == "1"]
    df_n4 = df_n4[df_n4["V1014"] == "5"]
    
    matched = df_n.merge(df_n4, on="person_id", how="inner")

    print("Indivíduos pareados:", matched.shape[0])
    
    return matched

if __name__ == "__main__":
    y, t = int(input("Ano inicial a ser comparado: ")), int(input("Trimestre desejado: "))
    
    _, file_n = make_data_paths(y, t)
    _, file_n4 = make_data_paths(y+1, t)
    matched_file = f"matched_{y}_{y+1}_t.parquet"
    
    matched = parear(file_n, file_n4)
    
    matched.to_parquet(matched_file, index=False)