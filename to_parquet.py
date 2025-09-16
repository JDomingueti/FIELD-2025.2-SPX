from pathlib import Path
import re
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa

layout_path = Path("PNAD_data/input_PNADC_trimestral.txt")

def make_data_paths(year, trimester):
    """
    Dado o ano e trimestre desejados, retorna os paths para o arquivo referente e 
    para o local do Parquet a ser gerado.
    
    Parêmatros:
        year (int): ano para o arquivo em questão, no formato XXXX (ex.: 2021)
        trimester (int): trimestre para o arquivo em questão, no formato X (ex.: 1)
    """
    
    raw_path = f"PNAD_data/{year}/PNADC_0{trimester}{year}.txt" # path do arquivo direto do PNAD
    parquet_path = f"PNAD_data/{year}/PNADC_0{trimester}{year}.parquet" # path para o arquivo resultante
    
    return Path(raw_path), Path(parquet_path)

pattern = r'@(\d+)\s+(\w+)\s+([^\s]+)\.'  # extração de início, varname e formatação
starts, widths, names = [], [], []

with open(layout_path, 'r', encoding='latin1') as file:
    for line in file:
        match = re.search(pattern, line)
        if match:
            start = int(match.group(1))
            var = match.group(2)
            fmt = match.group(3)

            # comprimento pode ser derivado a partir do rpóximo início
            starts.append(start)
            names.append(var)

widths = [starts[i+1] - starts[i] for i in range(len(starts)-1)]
widths.append(4000 - starts[-1] + 1)

if __name__ == "__main__":
    y = input("Ano dos microdados:")
    t = input("Trimestre desejado:")

    txt_file, parquet_file = make_data_paths(y, t)

    columns_to_keep = ["Ano", "Trimestre", "UF", "UPA", "V1008", "V1014", "V2003", "V2005", 
                    "V2007", "V2009", "VD4016", "VD4002", "VD4019", "VD4035", "V3009A", "V2010"]

    # separando o arquivo e lendo por chunks
    chunksize = 100_000
    dfs = []
    total_rows = 0 

    for i, chunk in enumerate(pd.read_fwf(txt_file, 
                                        widths=widths, 
                                        names=names, 
                                        dtype=str, 
                                        encoding='latin1', 
                                        chunksize=chunksize)):
        total_rows += len(chunk)
        print(f"Lidas {total_rows:,} linhas ate agora...")

        chunk = chunk[[c for c in columns_to_keep if c in chunk.columns]]
        dfs.append(chunk)

    # concatenar os chunks
    df = pd.concat(dfs, ignore_index=True)
            
    print(f"Loaded {len(df):,} rows with {len(df.columns)} columns.")
            
    table = pa.Table.from_pandas(df)
            
    pq.write_table(table, parquet_file, compression='snappy')

    print(f"Saved to {parquet_file}")