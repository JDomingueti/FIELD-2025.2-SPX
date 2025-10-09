library(dplyr)
library(tidyr)
library(ggplot2)
library(arrow)
library(here)

ano <- as.integer(readline("Ano a ser examinado: "))
tri <- as.integer(readline("Tri a ser examinado: "))

# --- 2. CARREGAMENTO E PREPARAÇÃO DOS DADOS ---
arquivo_entrada <- here("PNAD_data", "Pareamentos", paste0("pessoas_", ano, tri, "_", ano + 1, tri, "_classificado.parquet"))

# verificar existencia do arquivo
if (!file.exists(arquivo_entrada)) {
  stop("Arquivo de entrada não encontrado: '", arquivo_entrada, "'. Verifique o nome e o diretório.")
}

cat("Carregando dados de:", arquivo_entrada, "\n")
dados_classificados <- read_parquet(arquivo_entrada)

# Filtrar para apenas individuos de classe 1
cat("Filtrando para manter apenas individuos de Classe 1...\n")
dados_classe1 <- dados_classificados %>%
  filter(classe_individuo == 1)

if (nrow(dados_classe1) == 0) {
  stop("Nenhum individuo de Classe 1 encontrado nos dados.")
}

# --- 3. ANÁLISE DA EVOLUÇÃO DOS PESOS ---

cat("Analisando a evolução dos pesos da primeira para a última entrevista...\n")

# Ordenar por período
dados_classe1 <- dados_classe1 %>% arrange(ID_UNICO, periodo)

# Selecionar apenas os indivíduos que têm as 5 entrevistas
dados_completos <- dados_classe1 %>%
  group_by(ID_UNICO) %>%
  filter(n() == 5) %>%
  ungroup()

cat("Indivíduos com todas as 5 entrevistas:", n_distinct(dados_completos$ID_UNICO), "\n")

# Amostra de até 50 indivíduos
dados_plot <- dados_completos %>%
  group_by(ID_UNICO) %>%
  slice_sample(n = 1) %>% # garante amostra de IDs
  ungroup() %>%
  slice_sample(n = min(50, n_distinct(.$ID_UNICO))) %>%
  pull(ID_UNICO)

dados_plot <- dados_completos %>%
  filter(ID_UNICO %in% dados_plot)
# GRAFICO HEATMAP

cat("Gerando heatmap dos pesos amostrais...\n")

dados_classe1 <- dados_classe1 %>% arrange(ID_UNICO, periodo)

# Selecionar apenas os indivíduos que têm as 5 entrevistas
dados_completos <- dados_classe1 %>%
  group_by(ID_UNICO) %>%
  filter(n() == 5) %>%
  ungroup()

cat("Indivíduos com todas as 5 entrevistas:", n_distinct(dados_completos$ID_UNICO), "\n")

# --- Preparação dos dados para o Heatmap ---

# 1. Definir faixas (bins) para o Peso Amostral (V1028)
# O número de bins pode ser ajustado. Aqui, usamos 10 faixas iguais.
dados_heatmap <- dados_completos %>%
  mutate(
    faixa_peso = cut(V1028, 
                    breaks = unique(quantile(V1028, probs = seq(0, 1, length.out = 6), na.rm = TRUE)), # Decis de V1028
                    include.lowest = TRUE, 
                    dig.lab = 5,
                    labels = NULL)
  )

# 2. Contar a frequência de indivíduos por Faixa de Peso e Período
contagem_heatmap <- dados_heatmap %>%
  group_by(Ano, Trimestre, periodo) %>% # 'periodo' já é sequencial (e.g., 1 a 5)
  count(faixa_peso, name = "Frequencia") %>%
  ungroup() %>%
  mutate(
    periodo_label = paste0(Ano, "_T", Trimestre),
    # Garante a ordenação: primeiro por Ano, depois por Trimestre.
    periodo_label = factor(periodo_label, levels = unique(periodo_label[order(Ano, Trimestre)])),
    faixa_peso = as.factor(faixa_peso)
  )

# 3. Gráfico Heatmap
grafico_heatmap <- ggplot(contagem_heatmap, 
                        aes(x = periodo_label, 
                            y = faixa_peso, 
                            fill = Frequencia)) +
  geom_tile(color = "white", linewidth = 0.5) + # Adiciona bordas brancas para separar as células
  scale_fill_viridis_c(name = "Contagem de Indivíduos", option = "magma", direction = -1) + # Escala de cor para a frequência
  labs(
    title = paste0("Distribuição de Frequência do Peso Amostral (V1028) - ", ano, "T", tri),
    subtitle = "Indivíduos de Classe 1 com 5 Entrevistas (Decis de V1028)",
    x = "Período da Entrevista",
    y = "Faixa de Peso Amostral (V1028)"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(face = "bold"),
    axis.text.x = element_text(angle = 45, hjust = 1)
  )

print(grafico_heatmap)
