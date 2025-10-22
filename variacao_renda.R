library(dplyr)
library(tidyr)
library(ggplot2)
library(arrow)
library(here)
library(scales)

# Escolha de filtro para calcular a mediana
repeat {
  filtro <- readline("Escolha o filtro (0 = Sem filtro | 1 = Trab de App | 2 = Job Switcher | 3 = Trab de App - Deflator | 4 = Job Switcher - Deflator):")
  if (filtro %in% c("0", "1", "2")) break
  cat("FIltro Inválido")
}
std_path <- getwd()
# Caminho base onde estão os arquivos parquet
pasta_base <- here(std_path,"PNAD_data", "Pareamentos")

# Arquivo onde os resultados serão salvos
arquivo_saida_texto <- here(std_path, paste0("medianas_variacao_renda_", filtro, ".txt"))

# Limpa o arquivo antes de começar
cat("", file = arquivo_saida_texto)

# Lista de trimestres a processar
anos <- 2012:2025
trimestres <- 1:4

# Data frame para armazenar todos os resultados
resultados <- data.frame(
  ano_final = integer(),
  trimestre = integer(),
  mediana_variacao = numeric(),
  stringsAsFactors = FALSE
)

estatisticas_var_zero <- data.frame(
  ano_final = integer(),
  trimestre = integer(),
  percentual_zero = numeric(),
  percentual_menor_igual_zero = numeric(),
  stringsAsFactors = FALSE
)

# Loop principal
for (ano in anos) {
  for (tri in trimestres) {
    
    start_ano <- ano
    start_tri <- tri
    end_ano <- ano + 1
    end_tri <- tri
    
    rotulo_primeiro <- paste0(start_ano, "_", start_tri)
    rotulo_ultimo <- paste0(end_ano, "_", end_tri)
    arquivo_entrada <- file.path(pasta_base, paste0("pessoas_", start_ano, start_tri, "_", end_ano, end_tri, "_classificado.parquet"))
    
    if (!file.exists(arquivo_entrada)) {
      cat("Arquivo não encontrado:", arquivo_entrada, "\n")
      next
    }
    
    cat("Processando:", rotulo_primeiro, "→", rotulo_ultimo, "\n")
    
    dados_classificados <- read_parquet(arquivo_entrada)
    
    #Filtrando por tipo de trabalhador
    if (filtro == "1"){
      dados_classificados <- dados_classificados %>%
        filter(plataforma_transporte == 1 | plataforma_entrega == 1)
      
    } else if (filtro == "2"){
      dados_classificados <- dados_classificados %>%
        filter(job_switcher == 1)
      
    } else if (filtro == "0"){
      # mantem todos os dados
    }
    
    dados_variacao <- dados_classificados %>%
      mutate(periodo_label = paste0(Ano, "_", Trimestre)) %>%
      filter(classe_individuo %in% 1:3) %>% # Filtrando individuos de classe 1 a 3
      filter(periodo_label %in% c(rotulo_primeiro, rotulo_ultimo)) %>%
      group_by(ID_UNICO, periodo_label) %>%
      summarise(VD4020 = median(VD4020, na.rm = TRUE), .groups = 'drop') %>% # usando renda efetiva
      pivot_wider(
        id_cols = ID_UNICO,
        names_from = periodo_label,
        values_from = VD4020,
        names_prefix = "renda_"
      ) %>%
      rename(
        renda_primeiro = !!paste0("renda_", rotulo_primeiro),
        renda_ultimo = !!paste0("renda_", rotulo_ultimo)
      ) %>%
      mutate(
        variacao_renda = case_when(
          is.na(renda_primeiro) | is.na(renda_ultimo) ~ NA_real_,
          renda_primeiro == 0 | renda_ultimo == 0 ~ NA_real_,
          TRUE ~ (renda_ultimo - renda_primeiro) / renda_primeiro
        )
      ) %>%
      filter(is.finite(variacao_renda))
    
    # Calcula mediana da variação
    mediana_variacao <- median(dados_variacao$variacao_renda, na.rm = TRUE)
    
    # Estatisticas de variacao nula e menor que 0 no caso sem filtro
    if (filtro == "0"){
      # DEBUG
      contagens <- dados_variacao %>%
        summarise(
          total_obs = n(),
          obs_variacao_zero = sum(variacao_renda == 0, na.rm = TRUE),
          obs_variacao_menor_igual_zero = sum(variacao_renda <= 0, na.rm = TRUE)
        ) %>%
        mutate(
          percentual_zero = obs_variacao_zero / total_obs,
          percentual_menor_igual_zero = obs_variacao_menor_igual_zero / total_obs 
        )
      
      # adiciona ao df de estatisticas
      estatisticas_var_zero <- rbind(estatisticas_var_zero, data.frame(
        ano_final = end_ano,
        trimestre = start_tri,
        percentual_zero = contagens$percentual_zero,
        percentual_menor_igual_zero = contagens$percentual_menor_igual_zero
      ))
      cat("Proporção de variação <= 0:", scales::percent(contagens$percentual_menor_igual_zero), "\n")
    }
    
    # Adiciona ao dataframe de resultados
    resultados <- rbind(resultados, data.frame(
      ano_final = end_ano,
      trimestre = start_tri,
      mediana_variacao = mediana_variacao
    ))
    
    # Escreve no arquivo de texto
    resultado_texto <- paste0(
      "Mediana da variação de renda (", rotulo_primeiro, " -> ", rotulo_ultimo, "): ",
      scales::percent(mediana_variacao, accuracy = 0.1), "\n"
    )
    
    cat(resultado_texto, file = arquivo_saida_texto, append = TRUE)
    cat(resultado_texto)
  }
}

# Exibe tabela final de resultados
print(resultados)

# salva o df de estatisticas de var zero 
if (filtro == "0" && nrow(estatisticas_var_zero) > 0) {
  write.csv(estatisticas_var_zero, here(std_path, "estatisticas_variacao_nula.csv"), row.names = FALSE)
}

# (Opcional) salva como CSV para análise posterior
write.csv(resultados, here(std_path, paste0("medianas_variacao_renda_", filtro, ".csv")), row.names = FALSE)

cat("\n Loop concluído! Resultados salvos em:", arquivo_saida_texto, "\n")
