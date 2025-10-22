import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Wage Tracker", layout="wide")

df = pd.read_csv("medianas_variacao_renda_2012_2017.csv")

st.sidebar.header("Filters")

years = sorted(df["ano_inicial"].unique())
year_range = st.sidebar.slider(
    "Anos de Range",
    min_value=int(min(years)),
    max_value=int(max(years)),
    value=(int(min(years)), int(max(years)))
)

filtered = df[(df["ano_inicial"] >= year_range[0]) & (df["ano_inicial"] <= year_range[1])]

chart = (
    alt.Chart(filtered)
    .mark_line(point=True)
    .encode(
        x=alt.X("ano_inicial:O", title="Ano"),
        y=alt.Y("mediana_variacao:Q", title="Variação Mediana da Renda"),
        color=alt.Color("trimestre:N", title="Trimestre")
    )
    .properties(width=800, height=400)
)

st.title("Wage Tracker — Variação Mediana da Renda")
st.altair_chart(chart, use_container_width=True)

st.caption("Fonte: PNAD Contínua — Dados de 2012 a 2017")
