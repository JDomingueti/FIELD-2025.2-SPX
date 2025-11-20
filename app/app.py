import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

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
    "Branca": "_171",
    "Preta": "_172",
    "Amarela": "_173",
    "Parda": "_174",
    "Indígena": "_175",
    "Sem instrução": "_181",
    "Fundamental incompleto": "_182",
    "Fundamental completo": "_183",
    "Médio incompleto": "_184",
    "Médio completo": "_185",
    "Superior incompleto": "_186",
    "Superior completo": "_187",
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
    "Indústrias": "_203",
    "Classe A": "_21A",
    "Classe B": "_21B",
    "Classe C": "_21C",
    "Classe D": "_21D",
    "Classe E": "_21E",
    "Cluster 0": "_22_0",
    "Cluster 1": "_22_1"
}

# Mapeia a opção do deflator para o sufixo
deflator_suffix = {
    "Sim": "D",
    "Não": ""
}

DATA_DIR = Path("/data")
arquivo_base = DATA_DIR

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

@st.cache_data
def load_data_variacao_nula(base_path):
    """Carrega os dados para o gráfico de variação nula."""
    # Assume que o arquivo está na mesma pasta base dos outros
    file_path = f"{base_path}/estatisticas_variacao_nula.csv"
    try:
        df = pd.read_csv(file_path)
        # Cria a coluna 'ano_tri' aqui para ficar em cache
        df['ano_tri'] = df['ano_final'].astype(str) + '.' + df['trimestre'].astype(str)
        return df
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado para o gráfico de metodologia: {file_path}")
        return None

@st.cache_data
def load_data_classes_pareamento(base_path):
    """
    Carrega e transforma os dados de percentual das classes de pareamento
    para um formato "longo".
    """
    file_path = f"{base_path}/contagem_classe_pareamento.csv"
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado para o gráfico de classes: {file_path}")
        return None

    # Criar a coluna 'periodo' para o eixo X (ex: "2012.1")
    df['periodo'] = df['ano'].astype(str) + '.' + df['trimestre'].astype(str)
    
    # Definir as colunas que são percentuais
    value_vars = [f'classe {i}' for i in range(1, 6)]
    
    # Manter colunas de identificação
    id_vars = ['periodo', 'ano', 'trimestre', 'total_individuos']
    
    df_long = df.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Classe',
        value_name='Percentual'
    )
    
    return df_long
  
@st.cache_data
def load_data_grupos_domesticos(base_path):
    """
    Carrega os dados de proporção de domicilios com 1 grupo doméstico.
    """
    file_path = f"{base_path}/contagem_grupos_domesticos.csv"
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado para o gráfico de grupos domésticos: {file_path}")
        return None
    
    # Cria a coluna 'periodo' para o eixo X (ex: "2012.1")
    df['periodo'] = df['ano'].astype(str) + '.' + df['trimestre'].astype(str)
    
    return df


# --- Sidebar (Filtros Globais) ---

st.sidebar.title("Opções de Filtro")

# Filtro 1: Deflator
deflator_selecionado = st.sidebar.radio(
    "Deflator Aplicado",
    options=list(deflator_suffix.keys()),
    index=0
)
# obtem o sufixo D
codigo_deflator = deflator_suffix[deflator_selecionado]

# Filtro 2: Range de Anos
df_base_temp = load_data(grupos_suffix["Base"] + codigo_deflator)

if not df_base_temp.empty:
    # Lógica para o Filtro de Anos
    years = sorted(df_base_temp["ano_final"].unique())
    min_yr, max_yr = int(min(years)), int(max(years))
    
    min_y_val = df_base_temp['mediana_variacao'].min()
    max_y_val = df_base_temp['mediana_variacao'].max()
    
    # Adiciona um buffer de 20% no slider para dar espaço (10% para cima, 10% para baixo)
    y_buffer = (max_y_val - min_y_val) * 2.5
    
    # Converte para porcentagem para o slider
    slider_min_y = (min_y_val - y_buffer) * 100
    slider_max_y = (max_y_val + y_buffer) * 100
    default_min_y = min_y_val * 100
    default_max_y = max_y_val * 100

else:
    # Fallback caso o arquivo não seja encontrado
    min_yr, max_yr = 2012, 2025
    slider_min_y, slider_max_y = -20.0, 30.0
    default_min_y, default_max_y = -10.0, 20.0

# Cria o Slider de Anos
year_range = st.sidebar.slider(
    "Filtrar Anos",
    min_value=min_yr,
    max_value=max_yr,
    value=(min_yr, max_yr)
)

y_range_pct = st.sidebar.slider(
    "Filtrar Eixo Y (Variação %)",
    min_value=slider_min_y,
    max_value=slider_max_y,
    value=(default_min_y, default_max_y), # Padrão é o min/max real dos dados
    step=0.1,
    format="%.1f%%"  # Formata o slider para mostrar como porcentagem
)
# Converte a seleção do slider (porcentagem) de volta para decimal
y_range_values = (y_range_pct[0] / 100.0, y_range_pct[1] / 100.0)

# --- Variável global para a cor da linha Base ---
BASE_COLOR = '#606060' # Cinza escuro

def create_combined_chart(df, group_column=None):
    """
    Cria um gráfico combinado (Renda + Observações) para o DataFrame fornecido.
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
    tooltip_list = [
        'periodo',
        alt.Tooltip('mediana_variacao', format='.1%'),
        alt.Tooltip('obs')
    ]

    if group_column and len(filtered_df[group_column].unique()) > 1:
        # Lógica para MÚLTIPLOS GRUPOS (Incluindo Base)
        
        # Define a ordem do DOMAIN (Base sempre primeiro)
        grupos_no_df = list(filtered_df[group_column].unique())
        if 'Base' in grupos_no_df:
            grupos_no_df.remove('Base')
            grupos_no_df.insert(0, 'Base')
        
        cores_tableau10 = [
            '#4C78A8', '#F58518', '#E45756', '#72B7B2', '#54A24B', 
            '#EECA3B', '#B279A2', '#FF9DA6', '#9D755D', '#BAB0AC'
        ]
        
        # Pega as cores da paleta para os outros grupos (excluindo a primeira)
        cores_outros = cores_tableau10
        range_cores = [BASE_COLOR] + cores_outros[:len(grupos_no_df) - 1]
        
        # 4. Cria a codificação de cor com DOMAIN e RANGE fixos
        color_encoding = alt.Color(
            f"{group_column}:N", 
            title="Grupo",
            scale=alt.Scale(
                domain=grupos_no_df, # Ordem fixa dos grupos
                range=range_cores    # Cores fixas correspondentes (Base + Tableau)
            )
        )
        
        tooltip_list.append(alt.Tooltip(f"{group_column}:N", title="Grupo"))
        
        # Configuração de interatividade
        selection = alt.selection_point(
            fields=["Grupo"],
            bind="legend",
        )
        opacidade = alt.condition(selection, alt.value(1), alt.value(0.1))
        p = [selection]
        color_base = color_encoding # Usa a codificação de cor
        
    else:
        # Lógica para GRUPO ÚNICO (como na aba 'Base')
        # A cor é definida diretamente para BASE_COLOR
        color_base = alt.ColorValue(BASE_COLOR)
        opacidade = alt.value(1)
        p = []


    # Gráfico base
    base = alt.Chart(filtered_df).encode(
        x=alt.X("periodo:O", title="Ano.Trimestre"),
        tooltip=tooltip_list,
        opacity=opacidade
    ).add_params(*p)

    # Gráfico 1: Variação da Renda
    chart_renda = base.mark_line().encode(
        y=alt.Y("mediana_variacao:Q",
                title="Variação Mediana da Renda",
                axis=alt.Axis(format=".1%"),
                scale=alt.Scale(domain=[y_range_values[0], y_range_values[1]], clamp=True)
                ),
        # Usa a cor definida de forma condicional
        color=color_base
    ).properties(
        height=400
    ).interactive() # Permite zoom e pan

    # Gráfico 2: Número de Observações
    chart_obs = base.mark_line(point=False).encode(
        y=alt.Y("obs:Q", title="N (Amostras)"),
        # Usa a cor definida de forma condicional
        color=color_base
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
tab_metodologia, tab_base, tab_app, tab_switcher, tab_sexo, tab_regioes, tab_carteira, tab_quartis, tab_idade, tab_rac, tab_edu, tab_ocp, tab_div, tab_classes, tab_clusters = st.tabs([
    "Metodologia",
    "Base",
    "Trabalhador de App",
    "Job Switcher",
    "Sexo",
    "Regiões",
    "Carteira Assinada",
    "Quartis",
    "Faixa Etária",
    "Cor ou raça",
    "Nível educacional",
    "Ocupações",
    "Divisões ocp.",
    "Classes de Renda",
    "Clusters de Renda"
])

with tab_metodologia:
    #st.header("Metodologia")

    st.markdown("""
    # Metodologia

    ## Data Source

    Os dados que utilizamos para a construção do Wage Tracker são oriundos da PNAD (Pesquisa Nacional por Amostra
    de Domicílios) Contínua, realizada pelo IBGe para fornecer dados sobre a força de trabalho e o mercado de trabalho
    brasileiro de forma trimestral. Nas pesquisas da PNAD Contínua os domicílios são visitados cinco vezes consecutivas
    trimestralmente, após as cinco entrevistas os domicílios são retirados da amostra. Em um trimeste, aproximadamente
    20% dos domicílios são visitados pela primeira vez, e 20% estão na quinta visita. Dessa forma, conseguimos acompanhar
    a evolução dos indivíduos de determinado domicílio apenas durante 5 trimestres consecutivos. Portanto, para nossa análise
    da mediana da variação da renda dos indivíduos, calculamos as variações da primeira entrevista para a quinta entrevista das
    rendas daqueles indivíduos que possuíam rendas válidas.

    ## Pareamento
    
    A PNAD Contínua não disponibiliza suas pesquisas no formato de dados em painéis, disponibilizando apenas na estrutura
    cross-section. Para contornar esse problema, reproduzimos um método de pareamento de domicílios e indivíduos elaborada nesse
    artigo: OSORIO, RAFAEL. **Sobre a Montagem e a Identificação dos Painéis da PNAD Contínua. Ipea, 2022**. Com isso, conseguimos
    mapear os indivíduos com diferentes graus de confiabilidade no pareamento. Antes do pareamento dos indivíduos
    identificamos os grupos domésticos dentro de um mesmo domicílio. Os indivíduos de grupos domésticos distintos possuem conjuntos de entrevistas sem
    intersecção. Se um domicílio tem indivíduos com registros de pessoa nas primeira e segunda visitas,
    e outros com registros nas terceira, quarta e quinta visitas, há dois grupos domésticos. Se um
    indivíduo tem registros de pessoa em todas as entrevistas, há apenas um grupo doméstico, não
    importando quão radicais possam ser as mudanças na sua composição.
    A partir disso, classificamos os indivíduos da seguinte forma:

    Classe 1: Neste, que é o caso mais simples e de menor incerteza na identificação, em todas as entrevistas o grupo
    doméstico é composto por conjuntos de pessoas idênticas nessas quatro características

    Classe 2: Se o grupo doméstico tem tamanho constante, mas há indivíduos que não estão presentes em todas as entrevistas.
    Classificamos como 2 os indivíduos que estão presentes em todas as entrevistas, o grupo doméstico é composto por
    conjuntos de pessoas idênticas segundo sexo e data de nascimento, mas ao menos um tem variações
    na condição no domicílio e número de ordem.

    Classe 3: Indivíduos que pertecem a grupos domésticos que mudam de tamanha ou composição,
    e/ou cujas pessoas possuem variáveis com erros variados de declaração ou registro, porém tais
    indivíduos possuem mesmo sexo e data de nascimento e aparecem em todas as entrevistas.
                
    Classe >=4: Menos confiabilidade no pareamento dos indivíduos, indivíduos que aparecem em apenas
    algumas entrevistas.
    """)

    st.subheader("Distribuição das Classes de Pareamento ao Longo do Tempo")

    # --- GRÁFICO 1: Classes de Pareamento ---
    df_classes_long = load_data_classes_pareamento(arquivo_base)

    if df_classes_long is not None and not df_classes_long.empty:
        
        # Filtra os dados com base no slider de ano da sidebar
        df_classes_filtrado = df_classes_long[
            (df_classes_long["ano"] >= year_range[0]) &
            (df_classes_long["ano"] <= year_range[1])
        ]

        if not df_classes_filtrado.empty:
            # Cria o gráfico de área empilhado com Altair
            area_chart = alt.Chart(df_classes_filtrado).mark_area().encode(
                # Eixo X é o 'periodo' (ex: "2012.1")
                x=alt.X('periodo:O', title='Período (Ano.Trimestre)'),
                
                # Eixo Y é o 'Percentual'
                # stack='zero' garante que as áreas somem 100%
                y=alt.Y('Percentual:Q', stack='zero', title='Proporção de Indivíduos', axis=alt.Axis(format='%')),
                
                # A cor é baseada na 'Classe'
                color=alt.Color('Classe:N', title='Classe de Pareamento'),
                
                # Tooltip para interatividade
                tooltip=[
                    alt.Tooltip('periodo', title='Período'),
                    alt.Tooltip('Classe'),
                    alt.Tooltip('Percentual', format='.1%'),
                    alt.Tooltip('total_individuos', title='N Total no Período')
                ]
            ).properties(
                height=350
            ).interactive() # Permite zoom e pan

            st.altair_chart(area_chart, use_container_width=True)
            
        else:
            st.warning("Nenhum dado de classe de pareamento encontrado para o período selecionado.")

    st.markdown("---")
    # ---GRÁFICO 2: Grupos Domésticos ---
    st.subheader("Proporção de Domicílios com Apenas 1 Grupo Doméstico")

    df_grupos = load_data_grupos_domesticos(arquivo_base)

    if df_grupos is not None and not df_grupos.empty:
        # Filtra os dados com base no slider de ano da sidebar
        df_grupos_filtrado = df_grupos[
            (df_grupos["ano"] >= year_range[0]) &
            (df_grupos["ano"] <= year_range[1])
        ]

        if not df_grupos_filtrado.empty:
            
            # Gráfico de Linha + Pontos com Altair
            base_chart = alt.Chart(df_grupos_filtrado).encode(
                x=alt.X('periodo:O', title='Período (Ano.Trimestre)'),
                y=alt.Y('proporcao_1_grupo:Q', 
                        title='Proporção de 1 Grupo Doméstico', 
                        axis=alt.Axis(format='%')),
                tooltip=[
                    alt.Tooltip('periodo', title='Período'),
                    alt.Tooltip('proporcao_1_grupo', format='.2%', title='Proporção'),
                    alt.Tooltip('total_domicilios', title='N Total de Domicílios')
                ]
            )

            # Linha
            line = base_chart.mark_line(color='blue').properties(height=350) 
            # Pontos
            points = base_chart.mark_point(color='blue', size=60) 

            chart_grupos = (line + points).interactive()
            st.altair_chart(chart_grupos, use_container_width=True)
        else:
            st.warning("Nenhum dado de grupos domésticos encontrado para o período selecionado.")

    st.markdown("""
    ## Pesos Amostrais

    Optamos por não utilizar os pesos amostrais que iriam possuir a função de tentar utilizar a nossa amostra da PNAD
    para reproduzir uma proxy dos dados caso toda a população do Brasil fosse entrevistada. Nossa decisão se baseou no fato de que
    estamos reduzindo a nossa amostra ao utilizar apenas indivíduos de classe 1 a 3, como os pesos são calculados utilizando como base
    todos os indivíduos da amostra, ao filtrar os indivíduos de classe 1 a 3, os pesos amostrais se tornam enviesados.

    Estamos com uma amostra de aproximadamente 25.000 indivíduos por trimestre, dado que estamos olhando apenas para os indivíduos
    de classe 1 a 3 e apenas aproximadamente 20% da amostra total daquele trimestre. Durante os anos de 2020, 2021 e 2022, apresentamos uma
    amostra reduzida de aproximadamente 10.000 indivíduos, porém essa amostra começa a aumentar em 2023, estando agora em patamares
    próximos de anos pré-pandêmicos.
                
    """)

    st.markdown("---") # Adiciona uma linha divisória
    st.header("Proporção de Variação de Renda Nula")
    st.markdown("""
    O gráfico abaixo mostra a proporção de indivíduos cuja renda não variou (variação = 0%)
    ou não aumentou (variação <= 0%) entre a primeira e a quinta entrevista. Importante analisar esse gráfico
    pois sem a aplicação do deflator nas rendas, em muitos trimestres a mediana da variação da renda está em 0%.
    """)

    # Carrega os dados usando a nova função de cache
    df_nula = load_data_variacao_nula(arquivo_base) # Passa a variável 'arquivo_base'

    # Só executa se os dados foram carregados com sucesso
    if df_nula is not None and not df_nula.empty:
        
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize = (15, 8))

        ax.plot(df_nula['ano_tri'], df_nula['percentual_zero'], marker = 'o', linestyle = '-', label='Proporção com Variação = 0%')
        ax.plot(df_nula['ano_tri'], df_nula['percentual_menor_igual_zero'], marker='s', linestyle='--', label='Proporção com Variação <= 0%')

        # add linha em 50%
        ax.axhline(y=0.5, color='red', linestyle=':', linewidth=1.5, label='Limite de 50% (Mediana = 0)')

        ax.set_title('Proporção de Indivíduos com Variação de Renda Nula ou Negativa', fontsize=16)
        ax.set_xlabel('Período (Ano-Trimestre)', fontsize=12)
        ax.set_ylabel('Proporção', fontsize=12)

        ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
        
        ylim_max = 0.6
        if not df_nula['percentual_menor_igual_zero'].empty:
            ylim_max = max(df_nula['percentual_menor_igual_zero'].max() * 1.1, 0.6)
            
        ax.set_ylim(0, ylim_max)
        plt.xticks(rotation=45, ha='right')
        ax.xaxis.set_major_locator(plt.MaxNLocator(20))

        ax.legend(fontsize=11)
        plt.tight_layout()
        
        st.pyplot(fig)
    else:
        st.warning("Não foi possível carregar os dados para o gráfico de variação nula.")

# --- Aba 1: Base (Geral) ---
with tab_base:
    st.header("Base")
    
    df_base = load_data(grupos_suffix["Base"] + codigo_deflator)
    
    # Adiciona uma coluna 'Grupo' para identificar cada DataFrame
    df_base['Grupo'] = 'Base'
    
    # Combina os três DataFrames em um só
    df_base_combined = pd.concat([df_base])
    
    if not df_base_combined.empty:
        # Chamamos SEM 'group_column' para forçar a lógica de grupo único e cor BASE_COLOR
        chart = create_combined_chart(df_base_combined)
        st.altair_chart(chart, use_container_width=True)

# --- Aba 2: Trabalhador de App ---
with tab_app:
    st.header("Trabalhador de App")
    
    df_base = load_data(grupos_suffix["Base"] + codigo_deflator)
    df_trab_app = load_data(grupos_suffix["Trabalhador de App"] + codigo_deflator)
    
    # Adiciona uma coluna 'Grupo' para identificar cada DataFrame
    df_base['Grupo'] = 'Base'
    df_trab_app["Grupo"] = "Trabalhador de App"
    
    # Combina os três DataFrames em um só
    df_trab_app_combined = pd.concat([df_base, df_trab_app])
    
    if not df_trab_app_combined.empty:
        # Chama a mesma função, mas agora passando 'group_column'
        chart = create_combined_chart(df_trab_app_combined, group_column="Grupo")
        st.altair_chart(chart, use_container_width=True)

# --- Aba 3: Job Switcher ---
with tab_switcher:
    st.header("Job Switcher")
    
    df_base = load_data(grupos_suffix["Base"] + codigo_deflator)
    df_job_switcher = load_data(grupos_suffix["Job Switcher"] + codigo_deflator)
    
    # Adiciona uma coluna 'Grupo' para identificar cada DataFrame
    df_base['Grupo'] = 'Base'
    df_job_switcher["Grupo"] = "Job Switcher"
    
    # Combina os três DataFrames em um só
    df_job_switcher_combined = pd.concat([df_base, df_job_switcher])
    
    if not df_job_switcher_combined.empty:
        # Chama a mesma função, mas agora passando 'group_column'
        chart = create_combined_chart(df_job_switcher_combined, group_column="Grupo")
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

with tab_rac:
    st.header("Cor ou Raça")
    
    df_base = load_data(grupos_suffix['Base'] + codigo_deflator)
    df_bra = load_data(grupos_suffix['Branca'] + codigo_deflator)
    df_pre = load_data(grupos_suffix['Preta'] + codigo_deflator)
    df_ama = load_data(grupos_suffix['Amarela'] + codigo_deflator)
    df_par = load_data(grupos_suffix['Parda'] + codigo_deflator)
    df_ind = load_data(grupos_suffix['Indígena'] + codigo_deflator)

    df_base['Grupo'] = "Base"
    df_bra['Grupo'] = "Branca"
    df_pre['Grupo'] = "Preta"
    df_ama['Grupo'] = "Amarela"
    df_par['Grupo'] = "Parda"
    df_ind['Grupo'] = "Indígena"
    
    df_raca_combined = pd.concat([df_base, df_bra, df_pre, df_ama, df_par, df_ind])

    if not df_raca_combined.empty:
        # Chama a mesma função, mas agora passando 'group_column'
        chart = create_combined_chart(df_raca_combined, group_column="Grupo")
        st.altair_chart(chart, use_container_width=True)
        
with tab_edu:
    st.header("Nível educacional")
    
    df_base = load_data(grupos_suffix["Base"] + codigo_deflator)
    df_s_inst = load_data(grupos_suffix["Sem instrução"] + codigo_deflator)
    df_fund_i = load_data(grupos_suffix["Fundamental incompleto"] + codigo_deflator)
    df_fund_c = load_data(grupos_suffix["Fundamental completo"] + codigo_deflator)
    df_med_i = load_data(grupos_suffix["Médio incompleto"] + codigo_deflator)
    df_med_c = load_data(grupos_suffix["Médio completo"] + codigo_deflator)
    df_sup_i = load_data(grupos_suffix["Superior incompleto"] + codigo_deflator)
    df_sup_c = load_data(grupos_suffix["Superior completo"] + codigo_deflator)
    
    df_base['Grupo'] = "Base"
    df_s_inst['Grupo'] = "Sem instrução"
    df_fund_i['Grupo'] = "Fundamental incompleto"
    df_fund_c['Grupo'] = "Fundamental completo"
    df_med_i['Grupo'] = "Médio incompleto"
    df_med_c['Grupo'] = "Médio completo"
    df_sup_i['Grupo'] = "Superior incompleto"
    df_sup_c['Grupo'] = "Superior completo"
    
    df_educ_combined = pd.concat([df_base, df_s_inst, df_fund_i, df_fund_c, df_med_i, df_med_c, df_sup_i, df_sup_c])

    if not df_educ_combined.empty:
        # Chama a mesma função, mas agora passando 'group_column'
        chart = create_combined_chart(df_educ_combined, group_column="Grupo")
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
    
    df_div_combined = pd.concat([df_base, df_com, df_ser, df_ind])

    if not df_div_combined.empty:
        # Chama a mesma função, mas agora passando 'group_column'
        chart = create_combined_chart(df_div_combined, group_column="Grupo")
        st.altair_chart(chart, use_container_width=True)

with tab_classes:
    st.header("Classes de Renda")

    df_base = load_data(grupos_suffix['Base'] + codigo_deflator)
    df_a = load_data(grupos_suffix["Classe A"] + codigo_deflator)
    df_b = load_data(grupos_suffix["Classe B"] + codigo_deflator)
    df_c = load_data(grupos_suffix["Classe C"] + codigo_deflator)
    df_d = load_data(grupos_suffix["Classe D"] + codigo_deflator)
    df_e = load_data(grupos_suffix["Classe E"] + codigo_deflator)

    df_base['Grupo'] = "Base"
    df_a["Grupo"] = "Classe A"
    df_b["Grupo"] = "Classe B"
    df_c["Grupo"] = "Classe C"
    df_d["Grupo"] = "Classe D"
    df_e["Grupo"] = "Classe E"

    df_classe_combined = pd.concat([df_base, df_a, df_b, df_c, df_d, df_e])

    if not df_classe_combined.empty:
        # Chama a mesma função, mas agora passando 'group_column'
        chart = create_combined_chart(df_classe_combined, group_column="Grupo")
        st.altair_chart(chart, use_container_width=True)

with tab_clusters:
    st.header("Clusters de Renda")
    df_base = load_data(grupos_suffix['Base'] + codigo_deflator)
    df_cluster_0 = load_data(grupos_suffix["Cluster 0"] + codigo_deflator)
    df_cluster_1 = load_data(grupos_suffix["Cluster 1"] + codigo_deflator)

    df_base['Grupo'] = "Base"
    df_cluster_0["Grupo"] = "Cluster 0"
    df_cluster_1['Grupo'] = "Cluster 1"

    df_cluster_combined = pd.concat([df_base, df_cluster_0, df_cluster_1])

    if not df_cluster_combined.empty:
        # Chama a mesma função, mas agora passando 'group_column'
        chart = create_combined_chart(df_cluster_combined, group_column="Grupo")
        st.altair_chart(chart, use_container_width=True)


st.caption(f"Fonte: PNAD Contínua — Dados de 2012 a {max_yr}")
