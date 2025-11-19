library(arrow)
library(dplyr)
library(readr)
library(glue)
library(tidyr)

pasta_base <- "PNAD_data/Pareamentos"
pasta_saida <- "dados_medianas_var"

#' @title Calcula a Proporção de Indivíduos por Classe de Pareamento
#'
#' @description
#' Carrega os dados de painel classificados da PNAD Contínua para um determinado
#' período de transição (T1 para T5) e calcula a proporção de indivíduos
#' pertencentes a cada uma das 5 classes de pareamento (confiabilidade).
#'
#' @param ano O ano inicial (T1) do período de pareamento (e.g., 2012).
#' @param tri O trimestre inicial (T1) do período de pareamento (e.g., 1).
#'
#' @return
#' Um \code{tibble} com uma linha contendo:
#' \itemize{
#'   \item \code{ano}, \code{trimestre}: O período inicial.
#'   \item \code{classe 1} a \code{classe 5}: A proporção de indivíduos em cada classe (0 a 1).
#'   \item \code{total_individuos}: O número total de indivíduos pareados na amostra.
#' }
#' Retorna \code{NULL} se o arquivo não for encontrado ou houver erro de leitura.
#'
#' @importFrom arrow read_parquet
#' @importFrom dplyr tibble
#' @importFrom glue glue
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

#' @title Calcula a Proporção de Domicílios com Apenas 1 Grupo Doméstico
#'
#' @description
#' Carrega os dados de pareamento e calcula a proporção de domicílios que contêm
#' apenas um grupo doméstico (\code{n_grupos == 1}). Este é um indicador da
#' estabilidade da composição familiar/domiciliar ao longo das 5 entrevistas.
#' O cálculo é feito a nível de domicílio, usando a coluna \code{domicilio_id}
#' para garantir unicidade.
#'
#' @param ano O ano inicial do período de pareamento.
#' @param tri O trimestre inicial do período de pareamento.
#'
#' @return
#' Um \code{tibble} com uma linha contendo:
#' \itemize{
#'   \item \code{ano}, \code{trimestre}: O período inicial.
#'   \item \code{proporcao_1_grupo}: A proporção de domicílios com \code{n_grupos == 1} (0 a 1).
#'   \item \code{total_domicilios}: O número total de domicílios únicos na amostra.
#' }
#' Retorna \code{NULL} se o arquivo não for encontrado ou houver erro de leitura.
#'
#' @importFrom arrow read_parquet
#' @importFrom dplyr tibble distinct
#' @importFrom glue glue
prop_grupos_domesticos <- function(ano, tri) {
  ###
  ###Calcula a proporção de domicilios com 1 grupo doméstico (coluna n_grupos == 1).
  ###
  
  # constroi path do arquivo 
  file_name <- glue("pessoas_{ano}{tri}_{ano+1}{tri}_grupos_domesticos.parquet")
  file_path <- file.path(pasta_base, file_name)
  
  if (!file.exists(file_path)) {
    message(glue("Arquivo nao encontrado: {file_path}"))
    return(NULL)
  }
  
  # leitura do arquivo (
  df <- tryCatch({
    read_parquet(file_path, col_select = c("n_grupos", "domicilio_id")) 
  }, error = function(e) {
    message(glue("Erro ao ler o arquivo: {file_path}"))
    return(NULL)
  })
  
  if (is.null(df)) return(NULL)
  
  df_domicilios <- df %>% 
  distinct(domicilio_id, .keep_all = TRUE) 
  
  total_domicilios <- nrow(df_domicilios)
  
  if (total_domicilios == 0) {
    message(glue("Aviso: Total de domicilios é zero para {ano}.{tri}"))
    return(tibble(
      ano = ano,
      trimestre = tri,
      proporcao_1_grupo = 0,
      total_domicilios = 0
    ))
  }
  
  # contar a prop de numeros de domicilios com grupo_domestic igual a 1 
  contagem_1_grupo <- sum(df_domicilios$n_grupos == 1, na.rm = TRUE)
  proporcao <- contagem_1_grupo / total_domicilios
  
  # monta o df de retorno
  row_data <- tibble(
    ano = ano,
    trimestre = tri,
    proporcao_1_grupo = proporcao,
    total_domicilios = total_domicilios
  )
  
  return(row_data)
}

#' @title Gera Arquivos CSV de Estatísticas de Qualidade do Pareamento
#'
#' @description
#' Itera sobre todos os anos e trimestres disponíveis (de 2012 até o limite
#' definido pelos argumentos) para gerar duas métricas de qualidade do pareamento:
#' 1. Proporção das classes de indivíduos (\code{classes_pareamento_individuos}).
#' 2. Proporção de domicílios com 1 grupo doméstico (\code{prop_grupos_domesticos}).
#' Os resultados são agregados e salvos em arquivos CSV na pasta de saída.
#'
#' @param ultimo_ano_disponivel O ano mais recente (T5) para o qual existem dados
#'   completos (e.g., 2024 para painéis terminando em 2023.4).
#' @param ultimo_tri_disponivel O trimestre mais recente (T5) para o qual existem
#'   dados completos.
#'
#' @return
#' Invisível. Cria ou atualiza dois arquivos CSV na pasta \code{pasta_saida}:
#' \itemize{
#'   \item \code{contagem_classe_pareamento.csv}
#'   \item \code{contagem_grupos_domesticos.csv}
#' }
#'
#' @seealso \code{\link{classes_pareamento_individuos}}, \code{\link{prop_grupos_domesticos}}
#'
#' @importFrom dplyr bind_rows
#' @importFrom readr write_csv
#' @importFrom glue glu
gerar_estatisticas_pareamento <- function(ultimo_ano_disponivel, ultimo_tri_disponivel) {
  # Função que itera sobre os anos e trimestres baseado nos limites dinamicos e gera o CSV final.
  
  # Ajustamos para 2012:(ultimo_ano_disponivel - 1)
  anos <- 2012:(ultimo_ano_disponivel - 1)
  trimestres <- 1:4
  
  lista_dados_classes <- list() # Lista para armazenar os resultados
  lista_dados_grupos <- list()
  message("Iniciando geração de estatisticas de pareamento...")
  
  
  for (ano in anos) {
    for (tri in trimestres) {
      
      # condicao de parada 
      if (ano == (ultimo_ano_disponivel - 1) && tri > ultimo_tri_disponivel) {
        message(glue("Atingido o limite de dados em: {ano}-{tri}"))
        break
      }
      
      # condicao de parada do loop externo
      if (ano == ultimo_ano_disponivel) {
        break
      }
      
      message(glue("Processando dados para {ano}-{tri}"))
      
      # PROCESSAMENTO DAS CLASSES DE INDIVIDUOS
      data_classes <- classes_pareamento_individuos(ano, tri)
      if (!is.null(data_classes)) {
        lista_dados_classes[[length(lista_dados_classes) + 1]] <- data_classes
      }
      
      # PROCESSAMENTO DA PROP DE GRUPOS DOMESTICOS
      data_grupos <- prop_grupos_domesticos(ano, tri)
      if (!is.null(data_grupos)) {
        lista_dados_grupos[[length(lista_dados_grupos) + 1]] <- data_grupos
      }           
    }
    # condicao de parada do loop externo apos o interno
    if (ano == (ultimo_ano_disponivel - 1) && tri > ultimo_tri_disponivel) {
      break
    }
  }
  # --- GERAÇÃO DO ARQUIVO CSV DE CLASSES DE INDIVÍDUOS ---
  if (length(lista_dados_classes) > 0) {
    df_classes_final <- bind_rows(lista_dados_classes)
    name_classes <- "contagem_classe_pareamento.csv"
    path_saida_classes <- file.path(pasta_saida, name_classes)
    write_csv(df_classes_final, path_saida_classes)
    message(glue("Arquivo de contagem de classes salvo em: {path_saida_classes}"))
  } else {
    message("Nenhum dado processado para contagem de classes de indivíduos.")
  }
  
  # --- GERAÇÃO DO ARQUIVO CSV DE GRUPOS DOMÉSTICOS ---
  if (length(lista_dados_grupos) > 0) {
    df_grupos_final <- bind_rows(lista_dados_grupos)
    name_grupos <- "contagem_grupos_domesticos.csv"
    path_saida_grupos <- file.path(pasta_saida, name_grupos)
    write_csv(df_grupos_final, path_saida_grupos)
    message(glue("Arquivo de grupos domésticos salvo em: {path_saida_grupos}"))
  } else {
    message("Nenhum dado processado para contagem de classes de indivíduos.")
  }

}