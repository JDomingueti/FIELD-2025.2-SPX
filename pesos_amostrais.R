library(dplyr)
library(tidyr)
library(ggplot2)
library(arrow)

ano <- as.integer(readline("Ano a ser examinado: "))
tri <- as.integer(readline("Tri a ser examinado: "))

# --- 2. CARREGAMENTO E PREPARAÇÃO DOS DADOS ---
arquivo_entrada <- paste0("pessoas_", ano, tri, "_", ano + 1, tri, "_classificado.rds")

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

# Gráfico de linhas
grafico_evolucao <- ggplot(dados_plot, aes(x = periodo, y = V1028, group = ID_UNICO, color = ID_UNICO)) +
  geom_line(alpha = 0.6) +
  geom_point(size = 2) +
  labs(
    title = paste0("Evolução do Peso Amostral nas 5 Entrevistas - ", ano, "T", tri),
    subtitle = "Indivíduos de Classe 1 (Amostra de até 50 pessoas com todas as 5 entrevistas)",
    x = "Período da Entrevista",
    y = "Peso Amostral (V1028)"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(face = "bold"),
    legend.position = "none"
  )

print(grafico_evolucao)
