from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from pathlib import Path
import pandas as pd
import numpy as np

pasta_base = Path("PNAD_data/Pareamentos")

def otimizar_clusters(X, k_min=2, k_max=10, random_state=42, plot=True):

    scores = {}
    for k in range(k_min, k_max+1):
        kmeans = KMeans(n_clusters=k, random_state=random_state, n_init='auto')
        labels = kmeans.fit_predict(X)
        
        score = silhouette_score(X, labels)
        scores[k] = score

    melhor_k = max(scores, key=scores.get)

    return melhor_k

def cluster(ano, trimestre):
           
    file = pasta_base / f"pessoas_{ano}{trimestre}_{ano+1}{trimestre}_classificado.parquet"

    dados = pd.read_parquet(file)

    validos = dados["VD4019"].notna()
    rendas = dados.loc[validos, "VD4019"].values.reshape(-1, 1)

    kmeans = KMeans(n_clusters=2, random_state=42).fit(rendas)
    labels = kmeans.labels_
    centros = kmeans.cluster_centers_.flatten()
    
    if centros[0] > centros[1]:
        labels = np.where(labels == 0, 1, 0)
        
    print(f"{ano}.{trimestre}\nCentróides dos grupos: {kmeans.cluster_centers_}\n")

    dados["grupo_renda"] = np.nan

    dados.loc[validos, "grupo_renda"] = labels
    
    print(f"Tamanho do grupo 0: {(dados['grupo_renda'] == 0).sum()}\nTamanho do grupo 1: {(dados['grupo_renda'] == 1).sum()}\n \n")

    dados.to_parquet(file)