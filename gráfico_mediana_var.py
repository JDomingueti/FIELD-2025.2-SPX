import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns 
import os

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

        # Plot com subplot da quantidade de observacoes abaixo
        fig, axes = plt.subplots(
            nrows=2,
            ncols=1,
            figsize=(10, 8),
            sharex=True,
            gridspec_kw={'height_ratios': [6, 2], 'hspace': 0.05}
        )

        ax_principal = axes[0]  # Eixo plot mediana
        ax_obs = axes[1]        # Eixo plot obs

        # Plot principal - mediana
        sns.lineplot(
            data=df_medianas,
            x='ano_tri',
            y='mediana_variacao',
            marker='o',
            linestyle='-',
            color='darkblue',
            linewidth=2,
            errorbar=None,
            ax=ax_principal)
        
        ax_principal.set_title(f'Evolução da Mediana da Variação da Renda Habitual - {filtro[i]}', 
                               fontsize=13, loc='left', fontweight='bold')
        ax_principal.set_xlabel('') 
        ax_principal.set_ylabel('Mediana da Variação (%)')

        if i == '1D':
            ax_principal.set_ylim(-20, 5)
            ax_principal.set_yticks(range(-21, 5, 1))
        elif "D" in str(i):
            ax_principal.set_ylim(-10, 5)
            ax_principal.set_yticks(range(-11, 6, 1))
        elif i == 1:
            ax_principal.set_ylim(0, 15)
            ax_principal.set_yticks(range(0, 16, 1))
        else:
            ax_principal.set_ylim(0, 11)
            ax_principal.set_yticks(range(0, 12, 1))

        ax_principal.grid(True, axis='y')
        ax_principal.tick_params(axis = 'x', which = 'both', bottom=False) 

        # Plot da contagem de amostras

        sns.lineplot(
           data=df_medianas,
            x='ano_tri',
            y='obs',
            linestyle='--',
            marker='.',
            color='green',
            errorbar=None,
            ax=ax_obs) 

        ax_obs.set_title('Número de Observações por Trimestre', fontsize=10, loc='left')
        ax_obs.set_xlabel('Período da Entrevista (Ano.Trimestre)')
        ax_obs.set_ylabel('N (Amostras)')

        y_min = df_medianas['obs'].min()
        y_max = df_medianas['obs'].max()
        ax_obs.set_ylim(0, y_max * 1.1)

        # Ajusta os ticks dos eixos para ambos os plots 
        all_labels = df_medianas['ano_tri'].tolist()

        tick_indices = [i for i, label in enumerate(all_labels) if label.endswith('.1')]
        tick_labels = [all_labels[i] for i in tick_indices]
        if not all_labels[-1].endswith('.1'):
             tick_indices.append(len(all_labels) - 1)
             tick_labels.append(all_labels[-1])

        ax_obs.set_xticks(tick_indices)
        ax_obs.set_xticklabels(tick_labels, rotation=45, ha='right')
        ax_obs.grid(True, axis='x', linestyle=':')

        #ax_principal.spines['bottom'].set_visible(False)
        #ax_obs.spines['top'].set_visible(False)

        fig.tight_layout(rect=[0, 0, 1, 0.98])
        plt.show()
    else:
        print(f"Arquivo com filtro {i} nao existe!")
