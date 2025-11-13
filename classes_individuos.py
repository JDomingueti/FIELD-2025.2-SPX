from pathlib import Path
import pandas as pd

pasta_base = Path("PNAD_data/Pareamentos")

pasta_saida = Path("dados_medianas_var")

def classes_pareamento_individuos(ano, trimestre):
    """
    Conta quantos individuos de cada classe (1 a 5) existem em cada trimestre e em cada ano.
    """

    file_path = pasta_base /  f"pessoas_{ano}{trimestre}_{ano+1}{trimestre}_classificado.parquet"

    df = pd.read_parquet(file_path)

    #conta quantos valores existem de cada tipo
    counts = df["classe_individuo"].value_counts() 

    total_individuos = counts.sum()

    row_data = {
        "ano": ano,
        "trimestre": trimestre,
        "classe 1": counts.get(1, 0) / total_individuos,
        "classe 2": counts.get(2, 0) / total_individuos,
        "classe 3": counts.get(3, 0) / total_individuos,
        "classe 4": counts.get(4, 0) / total_individuos,
        "classe 5": counts.get(5, 0) / total_individuos,
        "total_individuos": total_individuos
    }

    return row_data

if __name__ == "__main__":
    anos = range(2012, 2025)
    trimestres = range(1, 5)

    data = []

    for ano in anos:
        for tri in trimestres:
            if ano == 2024 and tri == 3: break
            data_row = classes_pareamento_individuos(ano, tri)

            if data_row:
                data.append(data_row)

        if not data:
            print("Nenhum dado processado.")
        else:
            df_final = pd.DataFrame(data)

            name = "contagem_classe_pareamento.csv"
            path_saida = pasta_saida / name
            
            df_final.to_csv(path_saida, index=False)
