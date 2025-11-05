import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

medianas = {(2019, 1) : 1500,
(2019, 2) : 1400,
(2019, 3) : 1500,
(2019, 4) : 1500,
(2020, 1) : 1500,
(2020, 2) : 1200,
(2020, 3) : 1250,
(2020, 4) : 1300,
(2021, 1) : 1400,
(2021, 2) : 1300,
(2021, 3) : 1300,
(2021, 4) : 1400,
(2022, 1) : 1500,
(2022, 2) : 1500,
(2022, 3) : 1500,
(2022, 4) : 1600,
(2023, 1) : 1720,
(2023, 2) : 1700,
(2023, 3) : 1700,
(2023, 4) : 1800,
(2024, 1) : 2000,
(2024, 2) : 2000}

def tratamento_medianas(medianas):
    df = {'Ano': [0], 'Trimestre': [0], 'Mediana': [0]}
    
    for mediana in list(medianas.items()):
        df['Ano'] = df['Ano'] + [mediana[0][0]]
        df['Trimestre'] = df['Trimestre'] + [mediana[0][1]]
        df['Mediana'] = df['Mediana'] + [mediana[1]]
    
    del df['Ano'][0]
    del df['Trimestre'][0]
    del df['Mediana'][0]
    
    return df    

dados_medianas = tratamento_medianas(medianas)

df_medianas = pd.DataFrame(dados_medianas)

df_medianas['periodo_label'] = df_medianas.apply(
    lambda row: f"{int(row['Ano'])}_T{int(row['Trimestre'])}", axis=1
)

df_medianas = df_medianas.sort_values(['Ano', 'Trimestre']).reset_index(drop=True)

# print("DataFrame de Medidas (ordenado):")
# print(df_medianas)

############### Gráfico de Linha Absoluta

plt.figure(figsize=(10, 6))
sns.lineplot(
    data=df_medianas,
    x='periodo_label',
    y='Mediana',
    marker='o',
    linestyle='-',
    color='darkblue',
    linewidth=2
)
# Adiciona linha de tendência
sns.regplot(
    data=df_medianas,
    x=df_medianas.index, # Usa o índice para a regressão
    y='Mediana',
    scatter=False,
    ci = None,
    line_kws={'color':'black', 'linestyle':'--'}
)

plt.title('Evolução da Mediana da Renda dos Transporte por Aplicativo', fontsize=14, fontweight='bold')
plt.xlabel('Período da Entrevista (Ano_Trimestre)')
plt.ylabel('Mediana')
plt.grid(True, axis='y', linestyle='--', alpha=0.7)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

############### Gráfico de Barras de Variação

df_medianas['Mediana_Anterior'] = df_medianas['Mediana'].shift(1)
df_medianas['Variacao_Percentual'] = (
    (df_medianas['Mediana'] - df_medianas['Mediana_Anterior']) / df_medianas['Mediana_Anterior']
) * 100


df_variacao = df_medianas.iloc[1:].copy() 

df_variacao['Cor'] = df_variacao['Variacao_Percentual'].apply(lambda x: 'tab:green' if x >= 0 else 'tab:red')

plt.figure(figsize=(10, 6))

sns.barplot(
    data=df_variacao,
    x='periodo_label',
    y='Variacao_Percentual',
    palette=df_variacao['Cor'].tolist(), # Passa a lista de cores calculadas
    legend=False
)

for index, row in df_variacao.iterrows():
    # Usa a posição do índice filtrado (iloc[1:]) para posicionar o texto
    posicao_x = df_variacao.index.get_loc(index)
    
    if row['Variacao_Percentual'] >= 0:
        va = 'bottom'
    else:
        va = 'top'
        
    label = f"{row['Variacao_Percentual']:+.1f}%"
    
    plt.text(
        posicao_x,
        row['Variacao_Percentual'],
        label,
        ha='center',
        va=va,
        fontsize=10,
        fontweight='bold',
        color=row['Cor']
    )

plt.axhline(0, color='gray', linestyle='--')

plt.title('Variação Percentual Trimestral da Mediana da Renda dos Transporte por Aplicativo', fontsize=14, fontweight='bold')
plt.xlabel('Período de Comparação (Trimestre Anterior -> Trimestre Atual)')
plt.ylabel('Variação Percentual (%)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

############### Gráfico de Linha Variação

plt.figure(figsize=(10, 6))
sns.lineplot(
    data=df_variacao,
    x='periodo_label',
    y='Variacao_Percentual',
    marker='o',
    linestyle='-',
    color='royalblue',
    linewidth=2
)
# Adiciona linha de tendência
sns.regplot(
    data=df_variacao,
    x=df_variacao.index, # Usa o índice para a regressão
    y='Variacao_Percentual',
    scatter=False,
    ci = None,
    line_kws={'color':'black', 'linestyle':'--'}
)

plt.title('Variação Percentual Trimestral da Mediana da Renda dos Transporte por Aplicativo', fontsize=14, fontweight='bold')
plt.xlabel('Período da Entrevista (Ano_Trimestre)')
plt.ylabel('Variação Percentual (%)')
plt.grid(True, axis='y', linestyle='--', alpha=0.7)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()
