import pandas as pd
from pathlib import Path
from to_parquet import make_data_paths

y = input("Ano dos microdados:")
t = input("Trimestre desejado:")

_, initial_file = make_data_paths(y, t)

df = pd.read_parquet(initial_file)

print("Dimensões iniciais: ", df.shape)
print("Colunas disponíveis: ", df.columns.tolist()[:15])

df["id"] = ()

