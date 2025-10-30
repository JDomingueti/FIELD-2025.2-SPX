from sklearn.cluster import KMeans
from pathlib import Path
import pandas as pd

pasta_base = Path("../FIELD-2025.2-SPX/PNAD_data/Pareamentos")

def cluster(ano, trimestre):
    
    file = pasta_base / f"pessoas_{ano}{trimestre}_{ano+1}{trimestre}_classificado.parquet"

    dados = pd.read_parquet(file)
    
    rendas = dados["V4019"].values.reshape(-1, 1)
    kmeans = KMeans(n_clusters=2, random_state=42).fit(rendas)
    dados["grupo_renda"] = kmeans.labels_
    
    dados.to_parquet(file)