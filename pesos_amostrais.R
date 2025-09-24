library(dplyr)
library(tidyr)
library(ggplot2)

ano <- as.integer(readline("Ano a ser examinado: "))
tri <- as.integer(readline("Tri a ser examinado: "))

# --- 2. CARREGAMENTO E PREPARAÇÃO DOS DADOS ---
arquivo_entrada <- paste0("pessoas_", ano, tri, "_", ano + 1, tri, "_classificado.rds")

# verificar existencia do arquivo
if (!file.exists(arquivo_entrada)) {
  stop("Arquivo de entrada não encontrado: '", arquivo_entrada, "'. Verifique o nome e o diretório.")
}

cat("Carregando dados de:", arquivo_entrada, "\n")
dados_classificados <- readRDS(arquivo_entrada)

# Filtrar para apenas individuos de classe 1
cat("Filtrando para manter apenas individuos de Classe 1...\n")
dados_classe1 <- dados_classificados %>%
  filter(classe_individuo == 1)

if (nrow(dados_classe1) == 0) {
  stop("Nenhum individuo de Classe 1 encontrado nos dados.")
}

# --- 3. ANÁLISE DA EVOLUÇÃO DOS PESOS ---

cat("Analisando a evolução dos pesos da primeira para a última entrevista...\n")

# Criar um ID único para cada indivíduo para facilitar o agrupamento
dados_classe1 <- dados_classe1 %>%
  mutate(ID_UNICO = paste(domicilio_id, individuo_id, sep = "-"))

# para cada indivíduo, encontrar o peso V1028 da primeira e da ultima entrevista
pesos_evolucao <- dados_classe1 %>%
  group_by(ID_UNICO) %>%
  arrange(periodo) %>% #ordenar por odem cronologica
  # Resumir os dados para cada individuo
  summarise(
    periodo_inicial = first(periodo),
    peso_inicial = first(V1028),      
    periodo_final = last(periodo),    
    peso_final = last(V1028),         
    n_entrevistas = n()               
  ) %>%
  ungroup() 

# calcular a variacao absoluta e percentual
pesos_evolucao <- pesos_evolucao %>%
  mutate(
    variacao_absoluta = peso_final - peso_inicial,
    variacao_percentual = (peso_final - peso_inicial) / peso_inicial * 100
  )

# --- 4. EXIBIÇAO DOS RESULTADOS ---

cat("\n=== RESULTADOS DA ANÁLISE DE PESOS (CLASSE 1) ===\n")

cat("Amostra da tabela de evolução dos pesos:\n")
print(head(pesos_evolucao))

# mostrar um resumo estatistico da var percentual
cat("\nResumo estatístico da variação percentual dos pesos:\n")
summary(pesos_evolucao$variacao_percentual) %>% print()

# Mostrar os individuos com maior aumento e maior reducao percentual
cat("\nTop 5 maiores aumentos percentuais no peso:\n")
pesos_evolucao %>% arrange(desc(variacao_percentual)) %>% head(5) %>% print()

cat("\nTop 5 maiores reduções percentuais no peso:\n")
pesos_evolucao %>% arrange(variacao_percentual) %>% head(5) %>% print()


# --- 5. VISUALIZAÇÃO GRÁFICA ---
# Vamos visualizar para apenas 50 individuos

cat("\nGerando gráfico da evolução dos pesos para uma amostra de 50 indivíduos...\n")

# pegando a amostra
dados_plot <- pesos_evolucao %>%
  slice_sample(n = min(50, nrow(.))) %>% # Pega 50 ou o total se for menor que 50
  arrange(peso_inicial) %>%
  mutate(ID_UNICO = factor(ID_UNICO, levels = ID_UNICO)) 

# grafico de halteres
grafico_evolucao <- ggplot(dados_plot, aes(y = ID_UNICO)) +
  # Linha que conecta os pontos
  geom_segment(aes(x = peso_inicial, xend = peso_final, yend = ID_UNICO), 
               color = "grey", linewidth = 1) +
  # ponto para o peso inicial
  geom_point(aes(x = peso_inicial), color = "blue", size = 3) +
  # ponto para o peso final
  geom_point(aes(x = peso_final), color = "orange", size = 3) +
  labs(
    title = paste0("Evolução do Peso Amostral (Primeira vs. Ultima Entrevista)", "-", ano, tri, "-", ano + 1, "-", tri),
    subtitle = "Análise para indivíduos de Classe 1 (Amostra de 50 pessoas)",
    x = "Peso Amostral (V1028)",
    y = "Indivíduo (ID Único)",
    caption = "Ponto Azul = Peso Inicial  |  Ponto Laranja = Peso Final"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(face = "bold"),
    axis.text.y = element_blank(),
    axis.ticks.y = element_blank()
  )

print(grafico_evolucao)
