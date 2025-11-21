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

    validos = dados["log_renda"].notna() & (dados["classe_individuo"] <= 3)
    
    sub = dados.loc[validos, ["ID_UNICO", "log_renda", "Ano", "Trimestre"]].copy()

    # ordem de tempo
    sub = sub.sort_values(["ID_UNICO", "Ano", "Trimestre"])

    # pega somente a primeira aparicao dos individuos
    first = sub.groupby("ID_UNICO").first()

    # vetor para clustering
    x = first["log_renda"].values.reshape(-1, 1)

    # kmeans somente nas primeiras aparicoes
    kmeans = KMeans(n_clusters=k, random_state=42).fit(X=x)
    labels = kmeans.labels_
    centros = kmeans.cluster_centers_.flatten()

    # ordenar pelo centroide
    ordem = np.argsort(centros)
    centros_ordenados = centros[ordem]

    labels_ordenados = np.zeros_like(labels)
    for novo_label, antigo_label in enumerate(ordem):
        labels_ordenados[labels == antigo_label] = novo_label

    first["cluster"] = labels_ordenados

    dados["grupo_renda_kmeans"] = np.nan
    dados.loc[validos, "grupo_renda_kmeans"] = dados.loc[validos, "ID_UNICO"].map(first["cluster"])

    print(f"\nArquivo {ano}.{trimestre}")
    for i, c in enumerate(centros_ordenados):
        print(f"  Cluster {i}: centróide = {c:.2f}")

    print("\nTamanho dos grupos:")
    for i in range(k):
        print(f"  Cluster {i}: {(dados['grupo_renda_kmeans'] == i).sum()}")

    dados.to_parquet(file)

if (__name__ == "__main__"):
    anos = range(2012, 2025)
    tri = range(1, 5)

    for ano in anos:
        for trimestre in tri:
            if ano == 2024 and trimestre == 4:
                break
            
            cluster(ano, trimestre, 2)