import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

MEDIA = True # Mude para false para calcular a mediana ao invés da média
CLASSIFICADO = True # False

filtro = {
    -1: "Não aplicável",
    1: "Diretores e Gerentes",
    2: "Profissionais das ciências e intelectuais",
    3: "Técnicos e profissionais de nivel médio",
    4: "Trabalhadores de apoio administrativo",
    5: "Trabalhadores dos serviços, vendedores dos comércios e mercados",
    6: "Trabalhadores qualificados da agropecuária, florestais, da caça e da pesca",
    7: "Trabalhadores qualificados, operários e artesãos da construção, das artes mecânicas e outros ofícios",
    8: "Operadores de instalações e máquinas e montadores",
    9: "Ocupações elementares",
    0: "Membros das forças armadas, policiais e bombeiros militares"
} 

# filtro = {
#     9621: "Mensageiros, carregadores de bagagens e entregadores de encomendas",
#     8321: "Condutores de motocicletas",
#     8322: "Condutores de automóveis, taxis e caminhonetes",
#     4412: "Trabalhadores de serviços de correios",
#     4323: "Trabalhadores de serviços de transporte"
#     }

def apply_deflator(df: pd.DataFrame, deflator_path, year, trim):
    t = f"{(3*trim-2):02}-{(3*trim-1):02}-{(3*trim):02}"
    deflat = pd.read_excel(deflator_path)
    deflat = deflat[deflat["Ano"] == year]
    deflat = deflat[deflat["trim"] == t].reset_index()
    deflat["UF"] = deflat["UF"].astype(str)
    df_temporario = pd.merge(df["UF"], deflat[["UF", "Habitual", "Efetivo"]], on='UF', how='left')
    df["VD4016"] = df["VD4016"] * df_temporario["Habitual"]
    df["VD4017"] = df["VD4017"] * df_temporario["Efetivo"]
    df["VD4019"] = df["VD4019"] * df_temporario["Habitual"]
    df["VD4020"] = df["VD4020"] * df_temporario["Efetivo"]

def carregar_dfs(y_start, t_start, y_end, t_end, classified):
    # deflator_path = Path("PNAD_data/deflator_PNADC_2025_trimestral_040506.xls")
    deflator_path = Path("PNAD_data/deflator_PNADC_2025_trimestral_040506.xlsx") # O warning pode ser ignorado, mas para parar tem que converter o arquivo
                                                                                 # pro formato xlsx e tirar cabeçalhos/rodapés
    keys = []
    datas = [
        {},     # Ocupação
        {},     # Ocupação - peso
        {},     # Renda Habitual Principal
        {},     # Renda Habitual Principal - peso
        {},     # Renda Efetiva Principal
        {},     # Renda Efetiva Principal - peso
        {},     # Renda Habitual Total
        {},     # Renda Habitual Total - peso
        {},     # Renda Efetiva Total
        {},     # Renda Efetiva Total - peso
        ]
    lista = list(filtro.keys())
    len_key = 1000 if lista[0] < 1000 else 100 if lista[0] < 100 else 10 if lista[0] < 10 else 1
    if classified:
        # path = Path(f"PNAD_data/Pareamentos/pessoas_{y_start}{t_start}_{y_start+1}{t_start}.parquet")
        path = Path(f"PNAD_data/Pareamentos/pessoas_{y_start}{t_start}_{y_start+1}{t_start}_classificado.parquet")
        parquet_group = pd.read_parquet(path,
                                        columns=["UF",
                                                "V1028",   # Peso com calibração
                                                "V4010",   # Código de ocupação
                                                "VD4016",  # Renda habitual principal
                                                "VD4017",  # Renda efetiva principal
                                                "VD4019",  # Renda habitual total
                                                "VD4020",  # Renda efetiva total
                                                "Ano",
                                                "Trimestre",
                                                "classe_individuo",
                                                "ID_UNICO"
                                                ]).dropna(ignore_index=True)
        parquet_group = parquet_group[parquet_group["classe_individuo"].astype(int) <= 3]
        parquet_group = parquet_group.groupby("ID_UNICO").filter(lambda x: len(x) == 5).drop(columns=["classe_individuo", "ID_UNICO"])
        y_end = y_start + 1
    for year in range(y_start, y_end + 1):
        for i in range(4):
            trim = (t_start - 1 + i)%4 + 1
            lbl = str(year) + "-" + str(trim*3-1)
            path = Path(f"PNAD_data/{year}/PNADC_0{trim}{year}.parquet")
            if classified:
                parquet = parquet_group[(parquet_group["Ano"] == str(year)) & (parquet_group["Trimestre"] == str(trim))].drop(columns=["Ano", "Trimestre"]).reset_index(drop=True)
            else:
                parquet = pd.read_parquet(path,
                                          columns=["UF",
                                                   "V1028",   # Peso com calibração
                                                   "V4010",   # Código de ocupação
                                                   "VD4016",  # Renda habitual principal
                                                   "VD4017",  # Renda efetiva principal
                                                   "VD4019",  # Renda habitual total
                                                   "VD4020",  # Renda efetiva total
                                                   ]).dropna(ignore_index=True)
            apply_deflator(parquet, deflator_path, year, trim)
            print(" -> Lido: ", lbl, ";")
            values = [
                {},     # Ocupação
                {},     # Ocupação - peso
                {},     # Renda Habitual Principal
                {},     # Renda Habitual Principal - peso
                {},     # Renda Efetiva Principal
                {},     # Renda Efetiva Principal - peso
                {},     # Renda Habitual Total
                {},     # Renda Habitual Total - peso
                {},     # Renda Efetiva Total
                {},     # Renda Efetiva Total - peso
            ]
            parquet_np = parquet.to_numpy(dtype=np.float64)
            for idx_line in range(len(parquet)):
                line = parquet_np[idx_line, :]
                obj = int(line[2])//len_key
                if obj not in lista:
                    continue
                if obj in keys:
                    values[0][filtro[obj]] += 1                                   # Ocupação
                    values[1][filtro[obj]] += line[1]                             # Ocupação - peso
                    if MEDIA:
                        for i in [2,4,6,8]:
                            values[i][filtro[obj]] += line[2+i//2]                # Renda
                            values[i+1][filtro[obj]] += line[2+i//2]*line[1]      # Renda - peso
                    else:
                        for i in [2,4,6,8]:
                            values[i][filtro[obj]].append(line[2+i//2])           # Renda
                            values[i+1][filtro[obj]].append(line[2+i//2]*line[1]) # Renda - peso
                else:
                    values[0][filtro[obj]] = 1                                    # Ocupação
                    values[1][filtro[obj]] = line[1]                              # Ocupação - peso
                    if MEDIA:
                        for i in [2,4,6,8]:
                            values[i][filtro[obj]] = line[2+i//2]                 # Renda
                            values[i+1][filtro[obj]] = line[2+i//2]*line[1]       # Renda - peso
                    else:
                        for i in [2,4,6,8]:
                            values[i][filtro[obj]]= [(line[2+i//2])]              # Renda
                            values[i+1][filtro[obj]] = [(line[2+i//2]*line[1])]   # Renda - peso
                    keys.append(obj)
            for i in range(len(values)):
                datas[i][lbl] = values[i]
            if (trim == t_start) and (year == y_end): break
            keys = []
    return datas

if __name__ == "__main__":
    y_start = int(input("Ano início: "))
    t_start = int(input("Trimestre início: "))
    if not CLASSIFICADO:
        y_end = int(input("Ano término: "))
        t_end = int(input("Trimestre término: "))
    else:
        y_end = y_start
        t_end = 1
    datas = carregar_dfs(y_start, t_start, y_end, t_end, CLASSIFICADO)
    print("Todos dataframes carregados;")
    dfs = []
    figs = []
    for i in range(len(datas)):
        dfs.append(pd.DataFrame(datas[i]))
        figs.append(go.Figure())
        
    for line in range(len(dfs[0])):
        nome = dfs[0].iloc[line,:].name
        x = list(dfs[0].columns)
        ys = []
        for i in range(len(dfs)):
            ys.append([])
        for col in range(len(dfs[0].iloc[line])):
            ys[0].append(dfs[0].iloc[line,col])
            ys[1].append(dfs[1].iloc[line,col])
            if MEDIA:
                for i in [2,4,6,8]:
                    ys[i].append(dfs[i].iloc[line,col]/ys[0][col])
                    ys[i+1].append(dfs[i+1].iloc[line,col]/ys[1][col])
            else:
                for i in [2,4,6,8]:
                    ys[i].append(np.median(dfs[i].iloc[line,col]))
                    ys[i+1].append(np.median(dfs[i+1].iloc[line,col]))
        for idx, fig in enumerate(figs):
            fig.add_trace(go.Scatter(x=x, y=ys[idx], name=nome, mode="lines+markers", line=dict(width=8)))
    titles = [
        "Ocupações ao longo do tempo",
        "Ocupações ao longo do tempo - Com pesos",
        f"Renda habitual principal ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo",
        f"Renda habitual principal ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo - Com pesos",
        f"Renda efetiva principal ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo",
        f"Renda efetiva principal ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo - Com pesos",
        f"Renda habitual total ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo",
        f"Renda habitual total ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo - Com pesos",
        f"Renda efetiva total ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo",
        f"Renda efetiva total ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo - Com pesos",
    ]

    for idx, fig in enumerate(figs):
        fig.update_layout(
        title_text=titles[idx],
        title_x=0.5,
        font_size=25,
        xaxis=dict(type="date",
                    tickformat="%m-%Y",
                    dtick="M3",
                ),
        legend=dict(
            orientation="h",
            yanchor='bottom',
            y=-0.2,
            xanchor='left',
            x=0,
            ),
        )
        fig.show()