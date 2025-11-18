library(arrow)
library(dplyr)
library(readr)
library(glue)

pasta_base <- "PNAD_data/Pareamentos"
pasta_saida <- "dados_medianas_var"

classes_pareamento_individuos <- function(ano, tri) {
  ###
  ###Conta quantos individuos de cada classe (1 a 5) existem em cada trimestre e em cada ano.
  ###
  
  # constroi path do arquivo
  file_name <- glue("pessoas_{ano}{tri}_{ano+1}{tri}_classificado.parquet")
  file_path <- file.path(pasta_base, file_name)
  
  if (!file.exists(file_path)) {
    message(glue("Arquivo nao encontrado: {file_path}"))
    return(NULL)
  }
  
  # leitura do arquivo
  df <- tryCatch({
    read_parquet(file_path)
  }, error = function(e) {
    message(glue("Erro ao ler o arquivo: {file_path}"))
    return(NULL)
  })
  
  if (is.null(df)) return(NULL)
  
  # conta quantos individuos de cada classe existem
  
  counts <- table(factor(df$classe_individuo, levels=1:5))
  total_individuos <- sum(counts)
  
  if (total_individuos == 0){
    message(glue("Aviso: Total de individuos é zero para {ano}/{trimestre}"))
    return(tibble(
      ano = ano,
      trimestre = trimestre,
      `classe 1` = 0,
      `classe 2` = 0,
      `classe 3` = 0,
      `classe 4` = 0,
      `classe 5` = 0,
      total_individuos = 0
    ))
  }
  
  #proporcoes
  props <- counts / total_individuos
  
  # monta o df de retorno
  row_data <- tibble(
    ano = ano,
    trimestre = tri,
    `classe 1` = as.numeric(props["1"]),
    `classe 2` = as.numeric(props["2"]),
    `classe 3` = as.numeric(props["3"]),
    `classe 4` = as.numeric(props["4"]),
    `classe 5` = as.numeric(props["5"]),
    total_individuos = total_individuos
  )
  
  return(row_data)
  
}


gerar_contagem_classes <- function(ultimo_ano_disponivel, ultimo_tri_disponivel) {
  # Função que itera sobre os anos e trimestres baseado nos limites dinamicos e gera o CSV final.
  
  # Ajustamos para 2012:(ultimo_ano_disponivel - 1)
  anos <- 2012:(ultimo_ano_disponivel - 1)
  trimestres <- 1:4
  
  lista_dados <- list() # Lista para armazenar os resultados
  message("Iniciando geração de contagem de classes...")
  
  break_outer <- FALSE # Flag para quebrar o loop externo
  
  for (ano in anos) {
    for (tri in trimestres) {
      
      # condicao de parada 
      if (ano == (ultimo_ano_disponivel - 1) && tri > ultimo_tri_disponivel) {
        message(glue("Atingido o limite de dados em: {ano}-{tri}"))
        break
      }
      
      message(glue("Processando contagem de classes para: {ano}.{tri}"))
      data_row <- classes_pareamento_individuos(ano, tri)
      
      if (!is.null(data_row)) {
        lista_dados[[length(lista_dados) + 1]] <- data_row
      }
    }
    if (ano == (ultimo_ano_disponivel - 1) && tri > ultimo_tri_disponivel) {
      break
  }
  
  if (length(lista_dados) == 0) {
    message("Nenhum dado processado para contagem de classes.")
  } else {
    # Concatena todos os data frames da lista
    df_final <- bind_rows(lista_dados)
    
    # Cria dir se nao existir
    if (!dir.exists(pasta_saida)) {
      dir.create(pasta_saida, recursive = TRUE)
    }
    
    name <- "contagem_classe_pareamento.csv"
    path_saida <- file.path(pasta_saida, name)
    
    # Salva CSV
    write_csv(df_final, path_saida)
    message(glue("Arquivo de contagem de classes salvo em: {path_saida}"))
  }
 }
}