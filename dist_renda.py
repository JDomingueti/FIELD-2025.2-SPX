from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

pasta_base = Path("PNAD_data/Pareamentos")

arquivos = sorted(pasta_base.glob("pessoas_*_classificado.parquet"))

dados_lista = []

for file in arquivos:
    nome = file.stem
    partes = nome.split("_")
    
    ano = int(partes[1][:4])
    trimestre = int(partes[1][4])
    
    df = pd.read_parquet(file)
    
    df = df[df["VD4019"].notna() & (df["classe_individuo"] >= 3)]
    
    # Adiciona colunas de ano/trimestre e log
    df["Ano"] = ano
    df["Trimestre"] = trimestre
    df["log_renda"] = np.log(df["VD4019"])
    df["periodo"] = f"{ano}.{trimestre}"
    
    dados_lista.append(df[["Ano", "Trimestre", "VD4019", "log_renda", "periodo"]])

dados = pd.concat(dados_lista, ignore_index=True)

dados = dados.sort_values(by=["Ano", "Trimestre"])

plt.figure(figsize=(14, 6))
sns.boxplot(
    x='periodo',
    y='log_renda',
    data=dados,
    color='skyblue'
)
plt.xticks(rotation=45)
plt.xlabel('Ano.Trimestre')
plt.ylabel('Log do salário nominal')
plt.title('Distribuição dos salários nominais por trimestre (log)')
plt.tight_layout()
plt.show()