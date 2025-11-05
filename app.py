import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Wage Tracker", layout="wide")

# --- Configuração dos Arquivos ---

# Mapeia os nomes das abas/grupos para os sufixos dos arquivos
grupos_suffix = {
    "Base": "_0",
    "Trabalhador de App": "_1",
    "Job Switcher": "_2",
    "Masculino": "_3",
    "Feminino": "_4",
    "Norte": '_5',
    "Nordeste": '_6',
    "Sudeste": '_7',
    'Sul': '_8',
    'Centro-Oeste': '_9',
    "Carteira Assinada": "_10",
    "Média": "_11",
    "Percentil 25": "_12",
    "Percentil 75": "_13",
    "14-24 anos": "_14",
    "25-54 anos": "_15",
    "55+ anos": "_16",
    "Diretores e gerentes":"_191",
    "Prof. das ciências e intelectuais":"_192",
    "Prof. de nível médio":"_193",
    "Trab. de apoio adm.":"_194",
    "Trab. de serv. e vend.":"_195",
    "Trab. ambientais qualificados":"_196",
    "Trab. urbanos qualificados":"_197",
    "Operadores de máquinas":"_198",
    "Ocupações elementares":"_199",
    "Militares":"_190",
    "Comércios": "_201",
    "Serviços": "_202",
    "Indústrias": "_203"
}

# Mapeia a opção do deflator para o sufixo
deflator_suffix = {
    "Não": "",
    "Sim": "D"
}

# Caminho base para os arquivos CSV
# Ajuste este caminho se seus arquivos CSV estiverem em outro lugar
arquivo_base = "./dados_medianas_var" 

@st.cache_data
def load_data(suffix):
    """Carrega o DataFrame com base no sufixo do filtro."""
    file_path = f"{arquivo_base}/medianas_variacao_renda{suffix}.csv"
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        st.error(f"Arquivo de dados não encontrado: {file_path}")
        return pd.DataFrame() # Retorna um DataFrame vazio se o arquivo não existir

# --- Sidebar (Filtros Globais) ---

st.sidebar.title("Opções de Filtro")

# Filtro 1: Deflator
deflator_selecionado = st.sidebar.radio(
    "Deflator Aplicado",
    options=list(deflator_suffix.keys()),
    index=0 
)
# Obtém o sufixo do deflator (ex: "" ou "D")
codigo_deflator = deflator_suffix[deflator_selecionado]

# Filtro 2: Range de Anos
# Carregamos o arquivo 'Base' para obter o range min/max dos anos
df_base_temp = load_data(grupos_suffix["Base"] + codigo_deflator)

if not df_base_temp.empty:
    years = sorted(df_base_temp["ano_final"].unique())
    min_yr, max_yr = int(min(years)), int(max(years))
else:
    min_yr, max_yr = 2012, 2025 # Fallback caso o arquivo não seja encontrado

year_range = st.sidebar.slider(
    "Filtrar Anos",
    min_value=min_yr,
    max_value=max_yr,
    value=(min_yr, max_yr)
)

def create_combined_chart(df, group_column=None):
    """
    Cria um grafioc combinado (Renda + Observações) para o DataFrame fornecido.
    Filtra os dados com base no year_range global.
    Se 'group_column' for fornecido, cria um grafico de múltiplas linhas.
    """
    
    # Filtra o DataFrame pelo range de anos da sidebar
    filtered_df = df[(df["ano_final"] >= year_range[0]) & (df["ano_final"] <= year_range[1])]
    
    if filtered_df.empty:
        st.warning("Nao há dados para os filtros selecionados neste periodo.")
        return None

    # Cria a coluna 'periodo' para o eixo X
    filtered_df = filtered_df.assign(
        periodo = filtered_df['ano_final'].astype(str) + '.' + filtered_df['trimestre'].astype(str)
    )

    # --- Define as configurações de cor e tooltip ---
    color_encoding = alt.Color()
    tooltip_list = [
        'periodo', 
        alt.Tooltip('mediana_variacao', format='.1%'), 
        alt.Tooltip('obs')
    ]

    if group_column:
        # Se um group_column é dado (ex: "Grupo"), usa para colorir as linhas
        color_encoding = alt.Color(f"{group_column}:N", title="Grupo")
        tooltip_list.append(alt.Tooltip(f"{group_column}:N", title="Grupo"))
        selection = alt.selection_point(
            fields=["Grupo"],   # As categorias que queremos permitir a interação
            bind="legend",      # Liga a interação com a legenda
        )
        opacidade = alt.condition(selection, alt.value(1), alt.value(0.1))
        p = [selection]
    else:
        opacidade = alt.value(1)
        p = []

    # Gráfico base
    base = alt.Chart(filtered_df).encode(
        x=alt.X("periodo:O", title="Ano.Trimestre"),
        color="Grupo:N",
        tooltip=tooltip_list,
        opacity=opacidade
    ).add_params(*p)

    # Gráfico 1: Variação da Renda
    chart_renda = base.mark_line().encode(
        y=alt.Y("mediana_variacao:Q", title="Variação Mediana da Renda", axis=alt.Axis(format=".1%")),
        color=color_encoding
    ).properties(
        height=400
    ).interactive() # Permite zoom e pan

    # Gráfico 2: Número de Observações
    chart_obs = base.mark_line(point=False).encode(
        y=alt.Y("obs:Q", title="N (Amostras)"),
        color=color_encoding
    ).properties(
        height=100
    ).interactive()

    # Concatena os gráficos verticalmente
    combined_chart = alt.vconcat(
        chart_renda,
        chart_obs,
    ).resolve_scale(
        x = 'shared' # Compartilha o eixo X
    ).configure_view(
        stroke = None # Remove a borda
    )
    
    return combined_chart

# --- Corpo Principal da Página (com Abas) ---

st.title("Mediana da Variação da Renda")

# Cria as abas
tab_base, tab_app, tab_switcher, tab_sexo, tab_regioes, tab_carteira, tab_quartis, tab_idade, tab_ocp, tab_div = st.tabs([
    "Base", 
    "Trabalhador de App", 
    "Job Switcher", 
    "Sexo",
    "Regiões",
    "Carteira Assinada",
    "Quartis",
    "Faixa Etária",
    "Ocupações",
    "Divisões ocp."
])

# --- Aba 1: Base (Geral) ---
with tab_base:
    st.header("Base")
    suffix = grupos_suffix["Base"] + codigo_deflator
    df_data = load_data(suffix)
    
    if not df_data.empty:
        chart = create_combined_chart(df_data)
        st.altair_chart(chart, use_container_width=True)

# --- Aba 2: Trabalhador de App ---
with tab_app:
    st.header("Trabalhador de App")
    suffix = grupos_suffix["Trabalhador de App"] + codigo_deflator
    df_data = load_data(suffix)
    
    if not df_data.empty:
        chart = create_combined_chart(df_data)
        st.altair_chart(chart, use_container_width=True)

# --- Aba 3: Job Switcher ---
with tab_switcher:
    st.header("Job Switcher")
    suffix = grupos_suffix["Job Switcher"] + codigo_deflator
    df_data = load_data(suffix)
    
    if not df_data.empty:
        chart = create_combined_chart(df_data)
        st.altair_chart(chart, use_container_width=True)

# --- Aba 4: Comparação por Sexo ---
with tab_sexo:
    st.header("Sexo")
    
    # Carrega os 3 arquivos de dados necessários
    df_base = load_data(grupos_suffix["Base"] + codigo_deflator)
    df_masc = load_data(grupos_suffix["Masculino"] + codigo_deflator)
    df_fem = load_data(grupos_suffix["Feminino"] + codigo_deflator)
    
    # Adiciona uma coluna 'Grupo' para identificar cada DataFrame
    df_base['Grupo'] = 'Base'
    df_masc['Grupo'] = 'Masculino'
    df_fem['Grupo'] = 'Feminino'
    
    # Combina os três DataFrames em um só
    df_sexo_combined = pd.concat([df_base, df_masc, df_fem])
    
    if not df_sexo_combined.empty:
        # Chama a mesma função, mas agora passando 'group_column'
        chart = create_combined_chart(df_sexo_combined, group_column="Grupo")
        st.altair_chart(chart, use_container_width=True)

with tab_regioes:
    st.header("Regiões")
    
    df_base = load_data(grupos_suffix['Base'] + codigo_deflator)
    df_nordeste = load_data(grupos_suffix['Nordeste'] + codigo_deflator)
    df_sudeste = load_data(grupos_suffix['Sudeste'] + codigo_deflator)
    df_centro_oeste = load_data(grupos_suffix['Centro-Oeste'] + codigo_deflator)
    df_norte = load_data(grupos_suffix['Norte'] + codigo_deflator)
    df_sul = load_data(grupos_suffix['Sul'] + codigo_deflator)

    df_base['Grupo'] = 'Base'
    df_nordeste['Grupo'] = 'Nordeste'
    df_sudeste['Grupo'] = 'Sudeste'
    df_centro_oeste['Grupo'] = 'Centro-Oeste'
    df_sul['Grupo'] = 'Sul'
    df_norte['Grupo'] = 'Norte'

    df_regioes_combined = pd.concat([df_base, df_nordeste, df_norte, df_sul, df_sudeste, df_centro_oeste])

    if not df_regioes_combined.empty:
        # Chama a mesma função, mas agora passando 'group_column'
        chart = create_combined_chart(df_regioes_combined, group_column="Grupo")
        st.altair_chart(chart, use_container_width=True)

with tab_carteira:
    st.header("Carteira Assinada")

    df_base = load_data(grupos_suffix['Base'] + codigo_deflator)
    df_carteira = load_data(grupos_suffix["Carteira Assinada"] + codigo_deflator)

    df_base['Grupo'] = "Base"
    df_carteira["Grupo"] = "Carteira Assinada"

    df_carteira_combined = pd.concat([df_base, df_carteira])

    if not df_carteira_combined.empty:
        # Chama a mesma função, mas agora passando 'group_column'
        chart = create_combined_chart(df_carteira_combined, group_column="Grupo")
        st.altair_chart(chart, use_container_width=True)

with tab_quartis:
    st.header("Quartis")
    
    df_base = load_data(grupos_suffix['Base'] + codigo_deflator)
    df_media = load_data(grupos_suffix["Média"] + codigo_deflator)
    df_p25 = load_data(grupos_suffix['Percentil 25'] + codigo_deflator)
    df_p75 = load_data(grupos_suffix['Percentil 75'] + codigo_deflator)

    df_base['Grupo'] = "Base"
    df_media["Grupo"] = "Média"
    df_p25['Grupo'] = "Percentil 25"
    df_p75["Grupo"] = "Percentil 75"

    df_quartis_combined = pd.concat([df_base, df_media, df_p25, df_p75])

    if not df_quartis_combined.empty:
        # Chama a mesma função, mas agora passando 'group_column'
        chart = create_combined_chart(df_quartis_combined, group_column="Grupo")
        st.altair_chart(chart, use_container_width=True)

with tab_idade:
    st.header("Faixa Etária")
    
    df_base = load_data(grupos_suffix['Base'] + codigo_deflator)
    df_14_24 = load_data(grupos_suffix['14-24 anos'] + codigo_deflator)
    df_25_54 = load_data(grupos_suffix['25-54 anos'] + codigo_deflator)
    df_55 = load_data(grupos_suffix['55+ anos'] + codigo_deflator)

    df_base['Grupo'] = "Base"
    df_14_24['Grupo'] = "14-24"
    df_25_54['Grupo'] = "25-54"
    df_55['Grupo'] = "55+"

    df_idade_combined = pd.concat([df_base, df_14_24, df_25_54, df_55])

    if not df_idade_combined.empty:
        # Chama a mesma função, mas agora passando 'group_column'
        chart = create_combined_chart(df_idade_combined, group_column="Grupo")
        st.altair_chart(chart, use_container_width=True)

with tab_ocp:
    st.header("Grupos de ocupações")
    
    df_base = load_data(grupos_suffix['Base'] + codigo_deflator)
    df_dir = load_data(grupos_suffix["Diretores e gerentes"] + codigo_deflator)
    df_int = load_data(grupos_suffix["Prof. das ciências e intelectuais"] + codigo_deflator)
    df_med = load_data(grupos_suffix["Prof. de nível médio"] + codigo_deflator)
    df_adm = load_data(grupos_suffix["Trab. de apoio adm."] + codigo_deflator)
    df_vend = load_data(grupos_suffix["Trab. de serv. e vend."] + codigo_deflator)
    df_amb = load_data(grupos_suffix["Trab. ambientais qualificados"] + codigo_deflator)
    df_urb = load_data(grupos_suffix["Trab. urbanos qualificados"] + codigo_deflator)
    df_ope = load_data(grupos_suffix["Operadores de máquinas"] + codigo_deflator)
    df_ele = load_data(grupos_suffix["Ocupações elementares"] + codigo_deflator)
    df_mil = load_data(grupos_suffix["Militares"] + codigo_deflator)

    df_base['Grupo'] = "Base"
    df_dir['Grupo'] = "Diretores e gerentes"
    df_int['Grupo'] = "Prof. das ciências e intelectuais"
    df_med['Grupo'] = "Prof. de nível médio"
    df_adm['Grupo'] = "Trab. de apoio adm."
    df_vend['Grupo'] = "Trab. de serv. e vend."
    df_amb['Grupo'] = "Trab. ambientais qualificados"
    df_urb['Grupo'] = "Trab. urbanos qualificados"
    df_ope['Grupo'] = "Operadores de máquinas"
    df_ele['Grupo'] = "Ocupações elementares"
    df_mil['Grupo'] = "Militares"
    
    df_ocp_combined = pd.concat([df_base, df_dir, df_int, df_med, df_adm, df_vend, df_amb, df_urb, df_ope, df_ele, df_mil])

    if not df_ocp_combined.empty:
        # Chama a mesma função, mas agora passando 'group_column'
        chart = create_combined_chart(df_ocp_combined, group_column="Grupo")
        st.altair_chart(chart, use_container_width=True)

with tab_div:
    st.header("Grupos de ocupações")
    
    df_base = load_data(grupos_suffix['Base'] + codigo_deflator)
    df_com = load_data(grupos_suffix["Comércios"] + codigo_deflator)
    df_ser = load_data(grupos_suffix["Serviços"] + codigo_deflator)
    df_ind = load_data(grupos_suffix["Indústrias"] + codigo_deflator)
    
    df_base['Grupo'] = "Base"
    df_com['Grupo'] = "Comércios"
    df_ser['Grupo'] = "Serviços"
    df_ind['Grupo'] = "Indústrias"
    
    df_ocp_combined = pd.concat([df_base, df_com, df_ser, df_ind])

    if not df_ocp_combined.empty:
        # Chama a mesma função, mas agora passando 'group_column'
        chart = create_combined_chart(df_ocp_combined, group_column="Grupo")
        st.altair_chart(chart, use_container_width=True)

st.caption("Fonte: PNAD Contínua — Dados de 2012 a 2025")