from pathlib import Path
import pandas as pd
import numpy as np

def processar_dados(file):
    try:
        # Ler o df
        df = pd.read_parquet(file)
        
        # Inicializa a coluna com NaN
        df["log_renda"] = np.nan
        
        if "VD4019" in df.columns:
            mask = df["VD4019"].notna() & (df["VD4019"] > 0)
            
            # calcula o log apenas onde mask é verdadeira
            df.loc[mask, "log_renda"] = np.log(df.loc[mask, "VD4019"])

            #  Sobrescrever o arquivo original com o df modificado
            df.to_parquet(file, index=False)
        
            print(f"  Sucesso: {file} foi atualizado com 'log_renda'.")
        else:
            print(f"  AVISO: Coluna 'VD4019' não encontrada em {file}. Pulando.")

    except Exception as e:
        print(f"  ERRO ao processar {file}: {e}")

if __name__ == "__main__":
    pasta_base = Path("PNAD_data/Pareamentos")
    arquivos = sorted(pasta_base.glob("pessoas_*_classificado.parquet"))
    print(f"Encontrados {len(arquivos)} arquivos para processar...")

    for file in arquivos:
        print(f"Processando: {file.name}")
        processar_dados(file)

    print("\nProcessamento concluído.")