from sklearn.cluster import KMeans
from pathlib import Path
import pandas as pd
import numpy as np

pasta_base = Path("../FIELD-2025.2-SPX/PNAD_data/Pareamentos")

def cluster(ano, trimestre):
           
    file = pasta_base / f"pessoas_{ano}{trimestre}_{ano+1}{trimestre}_classificado.parquet"

    dados = pd.read_parquet(file)

    validos = dados["VD4019"].notna()
    rendas = dados.loc[validos, "VD4019"].values.reshape(-1, 1)

    kmeans = KMeans(n_clusters=2, random_state=42).fit(rendas)
    labels = kmeans.labels_
    print(f"Centróides dos grupos de {ano}.{trimestre}: {kmeans.cluster_centers_}")

    dados["grupo_renda"] = np.nan

    dados.loc[validos, "grupo_renda"] = labels

    dados.to_parquet(file)