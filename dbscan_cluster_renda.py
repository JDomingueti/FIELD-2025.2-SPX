from sklearn.cluster import DBSCAN
import numpy as np
from pathlib import Path
import pandas as pd

pasta_base = Path("../FIELD-2025.2-SPX/PNAD_data/Pareamentos")

def cluster_dbscan(ano, trimestre):
           
    file = pasta_base / f"pessoas_{ano}{trimestre}_{ano+1}{trimestre}_classificado.parquet"

    dados = pd.read_parquet(file)

    validos = dados["VD4019"].notna()
    rendas = dados.loc[validos, "VD4019"].values.reshape(-1, 1)

    db = DBSCAN(eps=5000, min_samples=100).fit(rendas)
    labels = db.labels_

    print("Labels:", labels)