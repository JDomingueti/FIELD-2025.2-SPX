# Field Project SPX x EMAp 2025
## Termômetro do Mercado de Trabalho Brasileiro baseado na PNAD contínua 

#### Integrantes: Bernardo Quintella, Jean Gabriel Domingueti e Sofia Monteiro

O projeto tem como objetivo a análise e tratamento de microdados coletados pela PNAD contínua, visando a geração de estatísticas de maior eficácia na avaliação e previsão no mercado de trabalho brasileiro.

#### Etapas

O desenvolveimento envolveu a realização das seguintes etapas:

 - Download e pré-processamento dos dados da PNADC
 - Pareamento e Classificação
 - Filtragem por classe de confiabilidade
 - Geração de Dados de Mediana de Variação
 - Vizualização
   
#### Funcionalidades
- **Atualização dos dados (`update`)** – baixa e processa quatro trimestres da PNAD utilizando R e Python, gerando cerca de 50 arquivos CSV limpos e leves
-  **Execução da aplicação (`run`)** – uma interface Streamlit que lê esses CSVs e exibe análises e gráficos interativos.

#### Estrutura do Projeto 
```bash
FIELD-2025.2-SPX/
│
├── updater/                     # Scripts de pré-processamento (R e Python)
│   ├── Dockerfile               # Ambiente de update
│   ├── script_geral.R
│   ├── PNAD_data/
│      └── ...
│   └── ...                     
│
├── app/                         # Aplicação Streamlit
│   ├── Dockerfile               # Ambiente de execução
│   ├── app.py                   
│   └── ...
│
├── dados_medianas_var/          # CSVs já processados
│      └── ...
│
├── docker-compose.yml
└── README.md
```
## Rodar o Projeto com Docker Compose

O projeto utiliza **profiles** no Docker Compose para separar a etapa pesada de processamento da etapa leve de visualização.

---

#### Pré-processamento dos dados (`update`)

Em caso de lançamento de novos dados da PNAD, baixa e processa os trimestres e atualiza os arquivos CSV em `dados_medianas_var/`. Para isso, execute:

```bash
docker compose --profile update up --build
```

#### Executar o Streamlit (run)

Para visualizar os dados já processados, execute:

```bash
docker compose --profile run up --build
```

A aplicação estará disponível em:

```bash
http://localhost:8501
```

#### Observações

    A pasta dados_medianas_var/ é compartilhada entre os serviços via volume, então os resultados do processamento ficam acessíveis ao Streamlit.

    A etapa update só precisa ser executada novamente quando você desejar atualizar os dados.

    A aplicação Streamlit usa apenas os CSVs gerados e não acessa diretamente os microdados brutos.
