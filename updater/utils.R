library(here)
library(dplyr)
library(arrow)

#' @title Solicita e Retorna os Períodos de Pareamento ao Usuário
#'
#' @description
#' Solicita interativamente ao usuário o ano e trimestre inicial (T1) de um painel.
#' Calcula automaticamente o ano e trimestre final (T5), assumindo um painel de 5 trimestres.
#'
#' @return
#' Uma lista contendo:
#' \itemize{
#'   \item \code{ano_inicio}: Ano da primeira entrevista (T1).
#'   \item \code{tri_inicio}: Trimestre da primeira entrevista (T1).
#'   \item \code{ano_fim}: Ano da quinta entrevista (T5).
#'   \item \code{tri_fim}: Trimestre da quinta entrevista (T5).
#' }
obter_periodos <- function() {
  ano_ini <- as.integer(readline("Ano inicial: "))
  tri_ini <- as.integer(readline("Trimestre inicial (1 a 4): "))
  ano_fim <- ano_ini + 1
  tri_fim <- tri_ini
  
  return(list(
    ano_inicio = ano_ini,
    tri_inicio = tri_ini,
    ano_fim = ano_fim,
    tri_fim = tri_fim
  ))
}

#' @title Constrói Caminhos de Arquivo para Dados PNADC
#'
#' @description
#' Constrói os caminhos esperados para os arquivos TXT (dados brutos) e Parquet
#' (dados processados) da PNAD Contínua para um dado ano e trimestre.
#'
#' @param year O ano do arquivo.
#' @param trimester O trimestre do arquivo (1 a 4).
#'
#' @return
#' Um vetor de strings contendo dois caminhos:
#' \itemize{
#'   \item [1] Caminho para o arquivo TXT (bruto).
#'   \item [2] Caminho para o arquivo Parquet (processado).
#' }
#'
#' @importFrom here here
make_path <- function(year, trimester) {
  raw_path <- here("PNAD_data", year, paste("PNADC_0", trimester, year, ".txt", sep=""))
  parquet_path <- here(std_path, "PNAD_data", year, paste("PNADC_0", trimester, year, ".parquet", sep=""))
  paths <- c(raw_path, parquet_path)
  paths
}


#' @title Calcula Ano e Trimestre Após um Deslocamento Temporal
#'
#' @description
#' Função utilitária para calcular o novo ano e trimestre após somar (ou subtrair, se n for negativo)
#' um número 'n' de trimestres ao período de início (\code{year}, \code{tri}).
#'
#' @param year Ano inicial.
#' @param tri Trimestre inicial (1 a 4).
#' @param n Número de trimestres a avançar (pode ser negativo para retroceder).
#'
#' @return
#' Uma lista contendo:
#' \itemize{
#'   \item \code{year}: O novo ano.
#'   \item \code{tri}: O novo trimestre.
#' }
shift_quarter <- function(year, tri, n) {
  # converte para um numero abs de trimestres desde o ano "0"
  q_abs <- (year * 4) + (tri - 1) + n
  new_year <- q_abs %/% 4
  new_tri <- (q_abs %% 4) + 1
  return(list(year = new_year, tri = new_tri))
}

