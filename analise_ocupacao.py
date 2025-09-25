import pandas as pd
import plotly.graph_objects as go
import pyarrow.parquet as pq
import pyarrow.compute as pc
from pathlib import Path

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

def make_data_paths(year, trimester): ## Roubei a função rapidão, é bom q tirar daqui dps
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

if __name__ == "__main__":
    y_start = int(input("Ano início: "))
    t_start = int(input("Trimestre início: "))
    y_end = int(input("Ano término: "))
    t_end = int(input("Trimestre término: "))

    keys = []
    data = {}
    dataR = {}
    data_p = {}
    dataR_p = {}
    for year in range(y_start, y_end + 1):
        for i in range(4):
            trim = (t_start - 1 + i)%4 + 1
            lbl = str(year) + "-" + str(trim)
            data[lbl] = {}
            data_p[lbl] = {}
            dataR[lbl] = {}
            dataR_p[lbl] = {}
            parquet = pc.drop_null(pq.read_table(make_data_paths(year, trim)[1], columns=["V4010", # Código de ocupação
                                                                                        "V1028", # Peso com calibração
                                                                                        "VD4017"
                                                                                        ]))
            ocp = {}
            ocp_p = {}
            renda = {}
            renda_p = {}
            for line, money, peso in zip(parquet["V4010"], parquet["VD4017"], parquet["V1028"]):
                obj = int(line)//1000
                if obj in keys:
                    ocp[filtro[obj]] += 1
                    renda[filtro[obj]] += float(money)
                    ocp_p[filtro[obj]] += float(peso)#float(parquet["V1028"][1])
                    renda_p[filtro[obj]] += float(money)*float(peso)#float(parquet["V1028"][1])
                else:
                    ocp[filtro[obj]] = 1
                    renda[filtro[obj]] = float(money)
                    ocp_p[filtro[obj]] = float(peso)#float(parquet["V1028"][1])
                    renda_p[filtro[obj]] = float(money)*float(peso)#float(parquet["V1028"][1])
                    keys.append(obj)
            data[lbl] = ocp
            data_p[lbl] = ocp_p
            dataR[lbl] = renda
            dataR_p[lbl] = renda_p
            if (trim == t_end) and (year == y_end): break
            keys = []
    ocp_df = pd.DataFrame(data)
    ocp_p_df = pd.DataFrame(data_p)
    renda_df = pd.DataFrame(dataR)
    renda_p_df = pd.DataFrame(dataR_p)
    figO = go.Figure()
    figOp = go.Figure()
    figR = go.Figure()
    figRp = go.Figure()

    for line in range(len(ocp_p_df)):
        name = ocp_df.iloc[line,:].name
        name_p = ocp_p_df.iloc[line,:].name
        x = []
        r = []
        rp = []
        xp = []
        y = []
        yp = []
        for i, ip, j, jr, date in zip(ocp_df.iloc[line,:], ocp_p_df.iloc[line,:], renda_df.iloc[line,:], renda_p_df.iloc[line,:], ocp_df.columns):
            x.append(date)
            y.append(i)
            yp.append(ip)
            r.append(j/i)
            rp.append(jr/ip)
        figO.add_trace(go.Scatter(x=x, y=y, name=name, mode="lines+markers", line=dict(width=8)))#, line_color=f"rgba{hex_to_rgb(cores[line%16])}", fill="tozeroy", fillcolor=f"rgba{hex_to_rgb(cores[line%16])}"))
        figOp.add_trace(go.Scatter(x=x, y=yp, name=name, mode="lines+markers", line=dict(width=8)))#, line_color=f"rgba{hex_to_rgb(cores[line%16])}", fill="tozeroy", fillcolor=f"rgba{hex_to_rgb(cores[line%16])}"))
        figR.add_trace(go.Scatter(x=x, y=r, name=name, mode="lines+markers", line=dict(width=8)))#, line_color=f"rgba{hex_to_rgb(cores[line%16])}", fill="tozeroy", fillcolor=f"rgba{hex_to_rgb(cores[line%16])}"))
        figRp.add_trace(go.Scatter(x=x, y=rp, name=name, mode="lines+markers", line=dict(width=8)))#, line_color=f"rgba{hex_to_rgb(cores[line%16])}", fill="tozeroy", fillcolor=f"rgba{hex_to_rgb(cores[line%16])}"))
        
    figO.update_layout(
        title_text="Ocupações ao longo do tempo",
        title_x=0.5,
        font_size=25,
        xaxis=dict(type="date",
                    tickformat="%m-%Y",
                    dtick="M3",
                    ## Add range slider
                    # rangeselector=dict(
                    #     buttons=list([
                    #         dict(count=3,
                    #             label="1t",
                    #             step="month",
                    #             stepmode="backward"),
                    #         dict(count=6,
                    #             label="1s",
                    #             step="month",
                    #             stepmode="backward"),
                    #         dict(count=12,
                    #             label="y",
                    #             step="year",
                    #             stepmode="todate"),
                    #         dict(step="all")
                    #     ])
                    # ),
                    # rangeslider=dict(
                    #     visible=True
                    # ),
                    ##
                ),
        legend=dict(
            orientation="h",
            yanchor='bottom',
            y=-0.2,
            xanchor='left',
            x=0,
        ),
    )
    figOp.update_layout(
        title_text="Ocupações ao longo do tempo - Com pesos",
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
    figR.update_layout(
        title_text="Renda por ocupação ao longo do tempo",
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
    figRp.update_layout(
        title_text="Renda por ocupação ao longo do tempo - Com pesos",
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

    figO.show()
    figOp.show()
    figR.show()
    figRp.show()