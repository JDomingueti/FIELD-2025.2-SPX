from pathlib import Path
import pandas as pd

pasta_base = Path("PNAD_data/Pareamentos")
pasta_saida = Path("dados_medianas_var")

def classes_pareamento_individuos(ano, trimestre):
    """
    Conta quantos individuos de cada classe (1 a 5) existem em cada trimestre e em cada ano.
    """

    file_path = pasta_base / f"pessoas_{ano}{trimestre}_{ano+1}{trimestre}_classificado.parquet"

    # caso o arquivo nao exista
    if not file_path.exists():
        print(f"Arquivo não encontrado, pulando: {file_path}")
        return None

    df = pd.read_parquet(file_path)

    # conta quantos valores existem de cada tipo
    counts = df["classe_individuo"].value_counts()

    total_individuos = counts.sum()

    # Previne divisao por zero
    if total_individuos == 0:
        print(f"Aviso: Total de indivíduos é zero para {ano}/{trimestre}")
        return {
            "ano": ano,
            "trimestre": trimestre,
            "classe 1": 0,
            "classe 2": 0,
            "classe 3": 0,
            "classe 4": 0,
            "classe 5": 0,
            "total_individuos": 0
        }

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

def gerar_contagem_classes(ultimo_ano_disponivel, ultimo_tri_disponivel):
    """
    Função que itera sobre os anos e trimestres
    baseado nos limites dinamicos e gera o CSV final.
    """
    
    anos = range(2012, ultimo_ano_disponivel)
    trimestres = range(1, 5)

    data = []
    print("Iniciando geração de contagem de classes...")

    for ano in anos:
        for tri in trimestres:
            if ano == ultimo_ano_disponivel - 1 and tri > ultimo_tri_disponivel:
                print(f"Atingido o limite de dados em: {ano}-{tri}")
                break  

            print(f"Processando contagem de classes para: {ano}.{tri}")
            data_row = classes_pareamento_individuos(ano, tri)

            if data_row:
                data.append(data_row)
        
        if ano == ultimo_ano_disponivel - 1 and tri > ultimo_tri_disponivel:
            break 

    if not data:
        print("Nenhum dado processado para contagem de classes.")
    else:
        df_final = pd.DataFrame(data)

        pasta_saida.mkdir(parents=True, exist_ok=True)
        
        name = "contagem_classe_pareamento.csv"
        path_saida = pasta_saida / name
        
        df_final.to_csv(path_saida, index=False)
        print(f"Arquivo de contagem de classes salvo em: {path_saida}")

