import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns 
import os
#TODO: Pular 2021.4 no caso de plotar o deflator
filtro = {
    0: "",
    1: "Trabalhador de App",
    2: "Job Switcher",
    '0D': "Deflator",
    '1D': "Trabalhador de App - Deflator",
    '2D': "Job Switcher - Deflator"
}

# navegando por todos os filtros de mediana
for i in (filtro.keys()):
    # Carrega os dados
    if os.path.exists(f"medianas_variacao_renda_{i}.csv"):
        df_medianas = pd.read_csv(f"medianas_variacao_renda_{i}.csv")

        # Cria uma coluna combinando ano e trimestre, por exemplo: "2012.1"
        df_medianas['ano_tri'] = df_medianas['ano_final'].astype(str) + '.' + df_medianas['trimestre'].astype(str)
        
        # Removendo outlier no caso do Deflator
        if "D" in str(i):
            df_medianas = df_medianas[df_medianas['ano_tri'] != '2021.4']

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

        plt.title(f'Evolução da Mediana da Variação da Renda Habitual - {filtro[i]}', fontsize=13, loc = 'left', fontweight = 'bold')
        plt.xlabel('Período da Entrevista (Ano.Trimestre)')
        plt.ylabel('Mediana da Variação (%)')

        if i == '1D':
            plt.ylim(-20, 5)
            plt.yticks(range(-21, 5, 1))
        elif "D" in str(i):
            plt.ylim(-10, 5)
            plt.yticks(range(-11, 6, 1))
        elif i == 1:
            plt.ylim(0, 15)
            plt.yticks(range(0, 16, 1))
        else:
            plt.ylim(0, 11)
            plt.yticks(range(0, 12, 1))

        plt.grid(True, axis='y')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()
    else:
        print(f"Arquivo com filtro {i} nao existe!")
    
    