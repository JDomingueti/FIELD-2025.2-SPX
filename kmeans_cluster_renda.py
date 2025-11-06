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

def cluster(ano, trimestre, k):
           
    file = pasta_base / f"pessoas_{ano}{trimestre}_{ano+1}{trimestre}_classificado.parquet"

    dados = pd.read_parquet(file)

    validos = dados["log_renda"].notna()
    rendas = dados.loc[validos, "log_renda"].values.reshape(-1, 1)

    kmeans = KMeans(n_clusters=k, random_state=42).fit(rendas)
    labels = kmeans.labels_
    centros = kmeans.cluster_centers_.flatten()
    
    centros = kmeans.cluster_centers_.flatten()

    ordem = np.argsort(centros)
    centros_ordenados = centros[ordem]
    
    labels_ordenados = np.zeros_like(labels)
    for novo_label, antigo_label in enumerate(ordem):
        labels_ordenados[labels == antigo_label] = novo_label
    
    print(f"{ano}.{trimestre}")
    for i, c in enumerate(centros_ordenados):
        print(f"  Cluster {i}: centróide = {c:.2f}")
    
    dados["grupo_renda_kmeans"] = np.nan
    dados.loc[validos, "grupo_renda_kmeans"] = labels_ordenados
    
    print("\nTamanho dos grupos:")
    for i in range(k):
        print(f"  Cluster {i}: {(dados['grupo_renda_kmeans'] == i).sum()}")

    dados.to_parquet(file)