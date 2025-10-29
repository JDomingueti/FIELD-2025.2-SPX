import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

try: # carrega os dados
    df = pd.read_csv("estatisticas_variacao_nula.csv")
except FileNotFoundError:
    print("Arquivo nao encontrado!")
    exit()

# Cria uma coluna combinando ano e trimestre, por exemplo: "2012.1"
df['ano_tri'] = df['ano_final'].astype(str) + '.' + df['trimestre'].astype(str)

# Criar o grafico
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize = (15, 8))

ax.plot(df['ano_tri'], df['percentual_zero'], marker = 'o', linestyle = '-', label='Proporção com Variação = 0%')
ax.plot(df['ano_tri'], df['percentual_menor_igual_zero'], marker='s', linestyle='--', label='Proporção com Variação <= 0%')

# add linha em 50%
ax.axhline(y=0.5, color='red', linestyle=':', linewidth=1.5, label='Limite de 50% (Mediana = 0)')

ax.set_title('Proporção de Indivíduos com Variação de Renda Nula ou Negativa', fontsize=16)
ax.set_xlabel('Período (Ano-Trimestre)', fontsize=12)
ax.set_ylabel('Proporção', fontsize=12)

ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
ax.set_ylim(0, max(df['percentual_menor_igual_zero'].max() * 1.1, 0.6))
plt.xticks(rotation=45, ha='right')
ax.xaxis.set_major_locator(plt.MaxNLocator(20))

ax.legend(fontsize=11)
plt.tight_layout()
plt.show()