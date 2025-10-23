import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Wage Tracker", layout="wide")

filtros = {
    "Base": "_0",
    "Trabalhador de App": "_1",
    "Job Switcher": "_2"
}

deflator = {
    "Não": "",
    "Sim": "D"
}

arquivo_base = "./dados_medianas_var/medianas_variacao_renda"

@st.cache_data
def load_data(suffix):
    """Carrega o DataFrame com base no sufixo do filtro."""
    file_path = f"{arquivo_base}{suffix}.csv"
    df = pd.read_csv(file_path)
    return df

st.sidebar.title("Opções de Filtro")

grupo_selecionado = st.sidebar.radio(
    "Grupo Específico",
    options=list(filtros.keys()),
    index=0
)

deflator_selecionado = st.sidebar.radio(
    "Deflator Aplicado",
    options=list(deflator.keys()),
    index=0 
)

codigo_grupo = filtros[grupo_selecionado]

codigo_deflator = deflator[deflator_selecionado]

file_suffix = codigo_grupo + codigo_deflator

df = load_data(file_suffix)

years = sorted(df["ano_final"].unique())
year_range = st.slider(
    "Anos de Range",
    min_value=int(min(years)),
    max_value=int(max(years)),
    value=(int(min(years)), int(max(years)))
)

filtered = df[(df["ano_final"] >= year_range[0]) & (df["ano_final"] <= year_range[1])]
filtered["periodo"] = filtered['ano_final'].astype(str) + '.' + filtered['trimestre'].astype(str)

chart = (
    alt.Chart(filtered)
    .mark_line()
    .encode(
        x=alt.X("periodo:O", title="Ano"),
        y=alt.Y("mediana_variacao:Q", title="Variação Mediana da Renda", axis=alt.Axis(format=".1%"))
        )
    .configure_mark(color='red'
)
    .properties(width=800, height=400)
)

st.title("Variação Mediana da Renda")
st.altair_chart(chart, use_container_width=True, )

st.caption("Fonte: PNAD Contínua — Dados de 2012 a 2017")
