from pathlib import Path
import pandas as pd
import numpy as np
import bisect

pasta_base = Path("PNAD_data/Pareamentos")

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
classes = [0, 1, 3, 5, 15]

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
        cla = classes_rotulo.get(posi)
        
        return cla

    validos = dados["VD4019"].notna()
    sub = dados.loc[validos, ["ID_UNICO", "VD4019", "Ano", "Trimestre"]]
    
    # ordena pelo primeiro ano e trimestre dentro do arquivo
    sub = sub.sort_values(["ID_UNICO", "Ano", "Trimestre"])
    
    # primeira aparicao do individuo 
    first = sub.groupby("ID_UNICO").first()
    
    # aplica a classe de renda
    first["classe_inicial"] = first["VD4019"].apply(classe)
    
    dados["grupo_renda"] = pd.NA
    
    #mapeia cada id para sua classe inicial
    dados.loc[validos, "grupo_renda"] = dados.loc[validos, "ID_UNICO"].map(first["classe_inicial"])
    
    dados.to_parquet(file)

    print(f"{file.name} → {first.shape[0]} indivíduos processados (classe inicial definida).")

if __name__ == "__main__":
    anos = range(2012, 2025)
    tri = range(1, 5)

    for ano in anos:
        for trimestre in tri:
            if ano == 2024 and trimestre == 4:
                break

            faixas(ano, trimestre)
