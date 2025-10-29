import pandas as pd
from pathlib import Path
import numpy as np 

# Caminho base onde estão os arquivos parquet
pasta_base = Path("../FIELD-2025.2-SPX/PNAD_data/Pareamentos")

# Arquivo onde os resultados serão salvos
arquivo_saida_texto = Path("mediana_variacao_renda.txt")
arquivo_saida_texto.write_text("")  # Limpa o arquivo antes de começar

# Lista de trimestres e anos a processar
anos = range(2012, 2026)
trimestres = range(1, 5)

# DataFrame para armazenar todos os resultados
resultados = pd.DataFrame(columns=["ano_inicial", "trimestre", "mediana_variacao"])

# Loop principal
for ano in anos:
    for tri in trimestres:
        start_ano = ano
        start_tri = tri
        end_ano = ano + 1
        end_tri = tri

        rotulo_primeiro = f"{start_ano}_{start_tri}"
        rotulo_ultimo = f"{end_ano}_{end_tri}"

        arquivo_entrada = pasta_base / f"pessoas_{start_ano}{start_tri}_{end_ano}{end_tri}_classificado.parquet"

        if not arquivo_entrada.exists():
            print("Arquivo não encontrado:", arquivo_entrada)
            continue

        print("Processando:", rotulo_primeiro, ":", rotulo_ultimo)

        dados = pd.read_parquet(arquivo_entrada)

        filtro_classe = dados[dados['classe_individuo'] <= 3.0]
        dados_filtrados = filtro_classe[filtro_classe['Trimestre'] == str(tri)]
        dados_filtrados = dados_filtrados.groupby('ID_UNICO').filter(lambda x: len(x) == 2)
        
        dados_filtrados = dados_filtrados.sort_values(by=['ID_UNICO', 'Ano'])
        dados_filtrados = dados_filtrados[dados_filtrados['VD4019'].notna()]
        
        dados_filtrados['variacao_renda'] = dados_filtrados.groupby('ID_UNICO')['VD4019'].pct_change(fill_method = None)

        dados_var = dados_filtrados.groupby('ID_UNICO').tail(1)[['ID_UNICO', 'variacao_renda']]
        
        # Calcula a mediana da variação
        mediana_variacao = dados_var["variacao_renda"].median()

        # Adiciona ao DataFrame de resultados
        resultados = pd.concat([resultados, pd.DataFrame([{
            "ano_inicial": start_ano,
            "trimestre": start_tri,
            "mediana_variacao": mediana_variacao
        }])], ignore_index=True)

# Exibe tabela final de resultados
print(resultados)

# Salva como CSV para análise posterior
resultados.to_csv("medianas_variacao_renda.csv", index=False)