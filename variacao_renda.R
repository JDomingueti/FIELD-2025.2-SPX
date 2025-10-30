library(dplyr)
library(tidyr)
library(ggplot2)
library(arrow)
library(here)
library(scales)

regioes <- c(
  c(11, 12, 13, 14, 15, 16, 17), #Norte
  c(21, 22, 23, 24, 25, 26, 27, 28, 29), #Nordeste
  c(31, 32, 33, 34, 35), #Sudeste
  c(41, 42, 43), #Sul
  c(50, 51, 52, 53) #Centro-Oeste
)

# Escolha de filtro para calcular a mediana
repeat {
  filtro <- readline("Escolha o filtro:\n 0 = Sem filtro\n 1 = Trab de App\n 2 = Job Switcher\n 3 = Masculino\n 4 = Feminino\n 5 = Norte\n 6 = Nordeste\n 7 = Centro-Oeste\n 8 = Sul\n 9 = Sudeste
  10 = Carteira Assinada\n 11 = Média \n 12 = Percentil 25\n 13 = Percentil 75\n 14 = 14-24 anos\n 15 = 25-54 anos\n 16 = 55+ anos\n Caso queira adicionar deflator basta colocar o codigo seguido de 'D' (exemplo: 0D)")
  if (filtro %in% c("0", "1", "2", "3","4","5", "6", "7", "8", "9","10","11", "12", "13","14", "15", "16", "0D", "1D", "2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "10D", "11D", '12D', "13D", "14D", "15D", "16D")) break
  cat("FIltro Inválido")
}
paste0("Filtro escolhido:", filtro)
std_path <- getwd()

nome_pasta_saida <- "dados_medianas_var"
pasta_saida <- here(std_path, nome_pasta_saida)

# Caminho base onde estão os arquivos parquet
pasta_base <- here(std_path,"PNAD_data", "Pareamentos")

# Arquivo onde os resultados serão salvos
arquivo_saida_texto <- here(pasta_saida, paste0("medianas_variacao_renda_", filtro, ".txt"))

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
  obs = integer(),
  stringsAsFactors = FALSE
)

estatisticas_var_zero <- data.frame(
  ano_final = integer(),
  trimestre = integer(),
  percentual_zero = numeric(),
  percentual_menor_igual_zero = numeric(),
  stringsAsFactors = FALSE
)

if (grepl("D", filtro)){
  coluna_renda <- "VD4019_deflat"
  cat("\nUsando renda deflacionada")
} else {
   coluna_renda <- "VD4019"
   cat("\nUsando renda nominal")
}

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
    if (filtro == "1" || filtro == "1D"){
      dados_classificados <- dados_classificados %>%
        filter(plataforma_transporte == 1 | plataforma_entrega == 1)
      
    } else if (filtro == "2" || filtro == "2D"){
      dados_classificados <- dados_classificados %>%
        filter(job_switcher == 1)
      
    } else if (filtro == "3" || filtro == "3D") { # Masculino
      dados_classificados <- dados_classificados %>%
        filter(V2007 == 1)

    } else if (filtro == "4" || filtro == "4D"){ # Feminino
      dados_classificados <- dados_classificados %>%
        filter(V2007 == 2) 
    } 
    else if (filtro == "0" || filtro == "0D"){
      # mantem todos os dados

    } else if (filtro == "5" || filtro == "5D"){ 
      dados_classificados <- dados_classificados %>%
        filter(UF %in% regioes[1])

    } else if (filtro == "6" || filtro == "6D"){
      dados_classificados <- dados_classificados %>%
        filter(UF %in% regioes[2])

    } else if (filtro == '7' || filtro == '7D'){
      dados_classificados <- dados_classificados %>%
        filter(UF %in% regioes[3])

    } else if (filtro == '8' || filtro == '8D'){
      dados_classificados <- dados_classificados %>%
        filter(UF %in% regioes[4])

    } else if (filtro == '9' || filtro == '9D'){
      dados_classificados <- dados_classificados %>%
        filter(UF %in% regioes[5])
    } else if (filtro == '10' || filtro == '10D'){ # carteira assinada
      dados_classificados <- dados_classificados %>%
        filter(V4029 == 1)
    } else if (filtro == '14' || filtro == '14D'){ 
      dados_classificados <- dados_classificados %>%
        filter(V2009 >= 14 & V2009 <=24)
    } else if (filtro == '15' || filtro == '15D'){ 
      dados_classificados <- dados_classificados %>%
        filter(V2009 >= 25 & V2009 <=54)
    }  else if (filtro == '16' || filtro == '16D'){ 
      dados_classificados <- dados_classificados %>%
        filter(V2009 >= 55)
    }
    
    dados_variacao <- dados_classificados %>%
      mutate(periodo_label = paste0(Ano, "_", Trimestre)) %>%
      filter(classe_individuo %in% 1:3) %>% # Filtrando individuos de classe 1 a 3
      filter(periodo_label %in% c(rotulo_primeiro, rotulo_ultimo)) %>%
      group_by(ID_UNICO, periodo_label) %>%
      summarise(Renda = median(.data[[coluna_renda]], na.rm = TRUE), .groups = 'drop') %>% 
      pivot_wider(
        id_cols = ID_UNICO,
        names_from = periodo_label,
        values_from = Renda,
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
    
    # Numero de observacoes de individuos
    num_obs <- nrow(dados_variacao)

    # calcula estatistica desejada de acordo com o filtro
    if (filtro == "11" || filtro == "11D") {
      estatistica_variacao <- mean(dados_variacao$variacao_renda, na.rm = TRUE)
    } else if (filtro == "12" || filtro == "12D") {
      estatistica_variacao <- quantile(dados_variacao$variacao_renda, 0.25, na.rm = TRUE)
    } else if (filtro == "13" || filtro == "13D") {
      estatistica_variacao <- quantile(dados_variacao$variacao_renda, 0.75, na.rm = TRUE)
    } else {
      # Calcula mediana da variação
      estatistica_variacao <- median(dados_variacao$variacao_renda, na.rm = TRUE)
    }
    
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
      mediana_variacao = estatistica_variacao,
      obs = num_obs
    ))
    
    # Escreve no arquivo de texto
    resultado_texto <- paste0(
      "Mediana da variação de renda (", rotulo_primeiro, " -> ", rotulo_ultimo, "): ",
      scales::percent(estatistica_variacao, accuracy = 0.1), "\n"
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
write.csv(resultados, here(pasta_saida, paste0("medianas_variacao_renda_", filtro, ".csv")), row.names = FALSE)

cat("\n Loop concluído! Resultados salvos em:", arquivo_saida_texto, "\n")
