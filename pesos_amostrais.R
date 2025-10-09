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

# Preparar dados no formato wide (linhas = indivíduos, colunas = períodos)
dados_heatmap <- dados_completos %>%
  filter(ID_UNICO %in% dados_plot) %>%
  mutate(Periodo = paste0(Ano, "_T", Trimestre)) %>%
  select(ID_UNICO, Periodo, V1028) %>%
  pivot_wider(names_from = Periodo, values_from = V1028)

# Converter para formato longo novamente (para ggplot)
dados_heatmap_long <- dados_heatmap %>%
  pivot_longer(-ID_UNICO, names_to = "Periodo", values_to = "V1028")

# Garantir ordem cronológica dos períodos
dados_heatmap_long$Periodo <- factor(
  dados_heatmap_long$Periodo,
  levels = sort(unique(dados_heatmap_long$Periodo))
)

# Criar heatmap
grafico_heatmap <- ggplot(dados_heatmap_long, aes(x = Periodo, y = factor(ID_UNICO), fill = V1028)) +
  geom_tile(color = "white") +
  scale_fill_viridis_c(option = "plasma", name = "Peso Amostral (V1028)") +
  labs(
    title = paste0("Variação dos Pesos Amostrais nas 5 Entrevistas - ", ano, "T", tri),
    subtitle = "Indivíduos de Classe 1 (Amostra de até 50 pessoas com todas as 5 entrevistas)",
    x = "Período da Entrevista",
    y = "Indivíduo"
  ) +
  theme_minimal() +
  theme(
    axis.text.y = element_blank(),
    axis.ticks.y = element_blank(),
    plot.title = element_text(face = "bold")
  )

print(grafico_heatmap)
