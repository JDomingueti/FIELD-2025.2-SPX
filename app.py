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

chart_renda = (
    alt.Chart(filtered)
    .mark_line(color='red')
    .encode(
        x=alt.X("periodo:O", title="Ano"),
        y=alt.Y("mediana_variacao:Q", title="Variação Mediana da Renda", axis=alt.Axis(format=".1%")),
        tooltip=['periodo', alt.Tooltip('mediana_variacao', format='.1%')]
        )
    .properties(width=800, height=400)
    .interactive()
)

chart_obs = (
    alt.Chart(filtered)
    .mark_line(color='green')
    .encode(
        x=alt.X("periodo:O", title='Ano'),
        y=alt.Y("obs:Q", title="N (Amostras)"),
        tooltip=['periodo','obs']
    )
    .properties(height=100)
    .interactive()
)

combined_chart = alt.vconcat(
    chart_renda,
    chart_obs,
).resolve_scale(
    x = 'shared'
).configure_view(stroke = None)

st.title("Mediana da Variação da Renda")
st.altair_chart(combined_chart, use_container_width=True, )

st.caption("Fonte: PNAD Contínua — Dados de 2012 a 2025")
