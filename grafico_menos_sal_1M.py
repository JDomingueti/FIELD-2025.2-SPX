from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

pasta_base = Path("../FIELD-2025.2-SPX/PNAD_data/Pareamentos")

percentual_salario_min = []
tris = []

anos = range(2012, 2025)
trimestres = [1, 2, 3, 4]

salarios_minimos = {
      "2012" : 622,
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

for ano in anos:
    for tri in trimestres:
        if ano == 2024 and tri == 3:
            break
        
        file = pasta_base / f"pessoas_{ano}{tri}_{ano+1}{tri}_classificado.parquet"
        
        dados = pd.read_parquet(file)
        
        validos = dados[dados["classe_individuo"] >= 3]
        validos = validos["VD4019"].notna()
        
        if ano == 2023:
            if tri == 1:
                salario_minimo = salarios_minimos.get("2023_1")
            else:
                salario_minimo = salarios_minimos.get("2023")
        else:
            salario_minimo = salarios_minimos.get(str(ano))

        rendas_abaixo = [validos < salario_minimo]
        
        percentual_salario_min.append((len(rendas_abaixo) / len(validos)) * 100)
        tris.append(f"{str(ano)[2:]}.{tri}")


plt.figure(figsize=(14, 7))
plt.plot(tris, np.array(percentual_salario_min) * 100)
plt.title("% de Individuos abaixo de 1 Salario Minimo")
plt.xlabel("Ano e Trimestre")
plt.ylabel("Percentual (%)")

indices_ticks = np.arange(0, len(tris), 4) # Pega índices 0, 4, 8, ...
labels_ticks = [tris[i] for i in indices_ticks] # Pega os rótulos correspondentes ("12.1", "13.1", ...)

plt.xticks(ticks=indices_ticks, labels=labels_ticks, rotation=45, ha='right')

plt.tight_layout()
plt.show()