import pandas as pd
import numpy as np
import plotly.graph_objects as go
import pyarrow.parquet as pq
import pyarrow.compute as pc
from pathlib import Path

MEDIA = False # Mude para false para calcular a mediana ao invés da média

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
    data_p = {}
    dataREP = {}
    dataREP_p = {}
    dataRET = {}
    dataRET_p = {}
    dataRHP = {}
    dataRHP_p = {}
    dataRHT = {}
    dataRHT_p = {}
    for year in range(y_start, y_end + 1):
        for i in range(4):
            trim = (t_start - 1 + i)%4 + 1
            lbl = str(year) + "-" + str(trim)
            print(lbl)
            data[lbl] = {}
            data_p[lbl] = {}
            dataREP[lbl] = {}
            dataREP_p[lbl] = {}
            dataRET[lbl] = {}
            dataRET_p[lbl] = {}
            dataRHP[lbl] = {}
            dataRHP_p[lbl] = {}
            dataRHT[lbl] = {}
            dataRHT_p[lbl] = {}
            parquet = pc.drop_null(pq.read_table(make_data_paths(year, trim)[1], columns=["V4010", # Código de ocupação
                                                                                        "V1028",  # Peso com calibração
                                                                                        "VD4016",  # Renda habitual principal
                                                                                        "VD4017",  # Renda efetiva principal
                                                                                        "VD4019",  # Renda habitual total
                                                                                        "VD4020",  # Renda efetiva total
                                                                                        ]))
            ocp = {}
            ocp_p = {}
            rendaET = {}
            rendaET_p = {}
            rendaHT = {}
            rendaHT_p = {}
            rendaHP = {}
            rendaHP_p = {}
            rendaEP = {}
            rendaEP_p = {}
            for line, moneyEP, peso, moneyET, moneyHP, moneyHT, in zip(parquet["V4010"], parquet["VD4017"], parquet["V1028"], parquet["VD4020"], parquet["VD4016"], parquet["VD4019"]):
                obj = int(line)//1000
                if obj in keys:
                    ocp[filtro[obj]] += 1
                    ocp_p[filtro[obj]] += float(peso)#float(parquet["V1028"][1])
                    if MEDIA:
                        rendaEP[filtro[obj]] += float(moneyEP)
                        rendaEP_p[filtro[obj]] += float(moneyEP)*float(peso)#float(parquet["V1028"][1])
                        rendaET[filtro[obj]] += float(moneyET)
                        rendaET_p[filtro[obj]] += float(moneyET)*float(peso)#float(parquet["V1028"][1])
                        rendaHP[filtro[obj]] += float(moneyHP)
                        rendaHP_p[filtro[obj]] += float(moneyHP)*float(peso)#float(parquet["V1028"][1])
                        rendaHT[filtro[obj]] += float(moneyHT)
                        rendaHT_p[filtro[obj]] += float(moneyHT)*float(peso)#float(parquet["V1028"][1])
                    else:
                        rendaEP[filtro[obj]].append(float(moneyEP))
                        rendaEP_p[filtro[obj]].append(float(moneyEP)*float(peso))#float(parquet["V1028"][1])
                        rendaET[filtro[obj]].append(float(moneyET))
                        rendaET_p[filtro[obj]].append(float(moneyET)*float(peso))#float(parquet["V1028"][1])
                        rendaHP[filtro[obj]].append(float(moneyHP))
                        rendaHP_p[filtro[obj]].append(float(moneyHP)*float(peso))#float(parquet["V1028"][1])
                        rendaHT[filtro[obj]].append(float(moneyHT))
                        rendaHT_p[filtro[obj]].append(float(moneyHT)*float(peso))#float(parquet["V1028"][1])
                else:
                    ocp[filtro[obj]] = 1
                    ocp_p[filtro[obj]] = float(peso)#float(parquet["V1028"][1])
                    if MEDIA:
                        rendaEP[filtro[obj]] = float(moneyEP)
                        rendaEP_p[filtro[obj]] = float(moneyEP)*float(peso)#float(parquet["V1028"][1])
                        rendaET[filtro[obj]] = float(moneyET)
                        rendaET_p[filtro[obj]] = float(moneyET)*float(peso)#float(parquet["V1028"][1])
                        rendaHP[filtro[obj]] = float(moneyHP)
                        rendaHP_p[filtro[obj]] = float(moneyHP)*float(peso)#float(parquet["V1028"][1])
                        rendaHT[filtro[obj]] = float(moneyHT)
                        rendaHT_p[filtro[obj]] = float(moneyHT)*float(peso)#float(parquet["V1028"][1])
                    else:
                        rendaEP[filtro[obj]] = [float(moneyEP)]
                        rendaEP_p[filtro[obj]] = [float(moneyEP)*float(peso)]#float(parquet["V1028"][1])
                        rendaET[filtro[obj]] = [float(moneyET)]
                        rendaET_p[filtro[obj]] = [float(moneyET)*float(peso)]#float(parquet["V1028"][1])
                        rendaHP[filtro[obj]] = [float(moneyHP)]
                        rendaHP_p[filtro[obj]] = [float(moneyHP)*float(peso)]#float(parquet["V1028"][1])
                        rendaHT[filtro[obj]] = [float(moneyHT)]
                        rendaHT_p[filtro[obj]] = [float(moneyHT)*float(peso)]#float(parquet["V1028"][1])
                    keys.append(obj)
            data[lbl] = ocp
            data_p[lbl] = ocp_p
            dataREP[lbl] = rendaEP
            dataREP_p[lbl] = rendaEP_p
            dataRET[lbl] = rendaET
            dataRET_p[lbl] = rendaET_p
            dataRHP[lbl] = rendaHP
            dataRHP_p[lbl] = rendaHP_p
            dataRHT[lbl] = rendaHT
            dataRHT_p[lbl] = rendaHT_p
            if (trim == t_end) and (year == y_end): break
            keys = []
    ocp_df = pd.DataFrame(data)
    ocp_p_df = pd.DataFrame(data_p)
    figO = go.Figure()
    figOp = go.Figure()
    rendaEP_df = pd.DataFrame(dataREP)
    rendaEP_p_df = pd.DataFrame(dataREP_p)
    rendaET_df = pd.DataFrame(dataRET)
    rendaET_p_df = pd.DataFrame(dataRET_p)
    figREP = go.Figure()
    figREPp = go.Figure()
    figRET = go.Figure()
    figRETp = go.Figure()
    rendaHP_df = pd.DataFrame(dataRHP)
    rendaHP_p_df = pd.DataFrame(dataRHP_p)
    rendaHT_df = pd.DataFrame(dataRHT)
    rendaHT_p_df = pd.DataFrame(dataRHT_p)
    figRHP = go.Figure()
    figRHPp = go.Figure()
    figRHT = go.Figure()
    figRHTp = go.Figure()

    for line in range(len(ocp_p_df)):
        name = ocp_df.iloc[line,:].name
        name_p = ocp_p_df.iloc[line,:].name
        x = []
        rEP = []
        rEPp = []
        rET = []
        rETp = []
        rHP = []
        rHPp = []
        rHT = []
        rHTp = []
        xp = []
        y = []
        yp = []
        for i, ip, ep, ep_p, et, et_p, hp, hp_p, ht, ht_p, date in zip(ocp_df.iloc[line,:], ocp_p_df.iloc[line,:],
                                                                        rendaEP_df.iloc[line,:], rendaEP_p_df.iloc[line,:],
                                                                        rendaET_df.iloc[line,:], rendaET_p_df.iloc[line,:],
                                                                        rendaHP_df.iloc[line,:], rendaHP_p_df.iloc[line,:],
                                                                        rendaHT_df.iloc[line,:], rendaHT_p_df.iloc[line,:],
                                                                        ocp_df.columns):
            x.append(date)
            y.append(i)
            yp.append(ip)
            if MEDIA:
                rEP.append(ep/i)
                rEPp.append(ep_p/ip)
                rET.append(et/i)
                rETp.append(et_p/ip)
                rHP.append(hp/i)
                rHPp.append(hp_p/ip)
                rHT.append(ht/i)
                rHTp.append(ht_p/ip)
            else:
                rEP.append(np.median(ep))
                rEPp.append(np.median(ep_p))
                rET.append(np.median(et))
                rETp.append(np.median(et_p))
                rHP.append(np.median(hp))
                rHPp.append(np.median(hp_p))
                rHT.append(np.median(ht))
                rHTp.append(np.median(ht_p))
        figO.add_trace(go.Scatter(x=x, y=y, name=name, mode="lines+markers", line=dict(width=8)))#, line_color=f"rgba{hex_to_rgb(cores[line%16])}", fill="tozeroy", fillcolor=f"rgba{hex_to_rgb(cores[line%16])}"))
        figOp.add_trace(go.Scatter(x=x, y=yp, name=name, mode="lines+markers", line=dict(width=8)))
        figREP.add_trace(go.Scatter(x=x, y=rEP, name=name, mode="lines+markers", line=dict(width=8)))
        figREPp.add_trace(go.Scatter(x=x, y=rEPp, name=name, mode="lines+markers", line=dict(width=8)))
        figRET.add_trace(go.Scatter(x=x, y=rET, name=name, mode="lines+markers", line=dict(width=8)))
        figRETp.add_trace(go.Scatter(x=x, y=rETp, name=name, mode="lines+markers", line=dict(width=8)))
        figRHP.add_trace(go.Scatter(x=x, y=rHP, name=name, mode="lines+markers", line=dict(width=8)))
        figRHPp.add_trace(go.Scatter(x=x, y=rHPp, name=name, mode="lines+markers", line=dict(width=8)))
        figRHT.add_trace(go.Scatter(x=x, y=rHT, name=name, mode="lines+markers", line=dict(width=8)))
        figRHTp.add_trace(go.Scatter(x=x, y=rHTp, name=name, mode="lines+markers", line=dict(width=8)))
        
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
    figREP.update_layout(
        title_text=f"Renda efetiva principal ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo",
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
    figREPp.update_layout(
        title_text=f"Renda efetiva principal ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo - Com pesos",
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
    figRET.update_layout(
        title_text=f"Renda efetiva total ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo",
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
    figRETp.update_layout(
        title_text=f"Renda efetiva total ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo - Com pesos",
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
    figRHP.update_layout(
        title_text=f"Renda habitual principal ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo",
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
    figRHPp.update_layout(
        title_text=f"Renda habitual principal ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo - Com pesos",
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
    figRHT.update_layout(
        title_text=f"Renda habitual total ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo",
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
    figRHTp.update_layout(
        title_text=f"Renda habitual total ({"média" if MEDIA else "mediana"}) por ocupação ao longo do tempo - Com pesos",
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
    figREP.show()
    figREPp.show()
    figRET.show()
    figRETp.show()
    figRHP.show()
    figRHPp.show()
    figRHT.show()
    figRHTp.show()