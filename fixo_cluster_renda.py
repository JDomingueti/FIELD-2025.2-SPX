from pathlib import Path
import pandas as pd
import numpy as np
import bisect

pasta_base = Path("../FIELD-2025.2-SPX/PNAD_data/Pareamentos")

salarios_minimos = {"2012" : 622,
      "2013" : 678,
      "2014" : 724,
      "2015" : 788,
      "2016" : 880,
      "2017" : 937,
      "2018" : 954,
      "2019" : 998,
      "2020" : 1045,
      "2021" : 1100,
      "2022" : 1212,
      "2023_1" : 1302,
      "2023" : 1320,
      "2024" : 1412,
      "2025" : 1518
  }

classes_rotulo = {5 : "A", 4: "B", 3 : "C", 2 : "D", 1 : "E"}
classes = sorted(list(classes_rotulo.values()))

def faixas(ano, trimestre):
           
    file = pasta_base / f"pessoas_{ano}{trimestre}_{ano+1}{trimestre}_classificado.parquet"

    dados = pd.read_parquet(file)
    
    if ano == 2023 and trimestre == 1:
        salario_min = salarios_minimos.get("2023_1")
    else:
        salario_min = salarios_minimos.get(str(ano))
        
    def classe(renda):
        prop = renda/salario_min
        posi = bisect.bisect_left(classes, prop)
        
        return classes_rotulo.get(posi)

    validos = dados["VD4019"].notna()
    rendas = dados.loc[validos, "VD4019"].values.reshape(-1, 1)

    labels = [classe(r) for r in rendas]
    
    dados["grupo_renda"] = np.nan

    dados.loc[validos, "grupo_renda"] = labels
    
    contagem = dados["grupo_renda"].value_counts(dropna=False).sort_index()

    print("\nContagem de linhas por grupo de renda:")
    print(contagem)