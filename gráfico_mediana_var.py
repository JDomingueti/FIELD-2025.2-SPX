import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns 

# Carrega os dados
df_medianas = pd.read_csv("medianas_variacao_renda.csv")

# Cria uma coluna combinando ano e trimestre, por exemplo: "2012.1"
df_medianas['ano_tri'] = df_medianas['ano_inicial'].astype(str) + '.' + df_medianas['trimestre'].astype(str)

# Para regressão, vamos criar um eixo numérico contínuo
df_medianas['x_numeric'] = range(len(df_medianas))

df_medianas['mediana_variacao'] = df_medianas['mediana_variacao'] * 100

plt.figure(figsize=(10, 6))

# Linha principal
sns.lineplot(
    data=df_medianas,
    x='ano_tri',
    y='mediana_variacao',
    marker='o',
    linestyle='-',
    color='darkblue',
    linewidth=2,
    errorbar=None)

plt.title('Evolução da Mediana da Variação da Renda Efetiva', fontsize=13, loc = 'left', fontweight = 'bold')
plt.xlabel('Período da Entrevista (Ano.Trimestre)')
plt.ylabel('Mediana da Variação (%)')
plt.ylim(0, 11)  
plt.yticks(range(0, 12, 1))
plt.grid(True, axis='y')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()