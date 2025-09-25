library(here)

# funcao para obter periodos de entrevista de acordo com o usuario
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

make_path <- function(year, trimester) {
  raw_path <- here("PNAD_data", year, paste("PNADC_0", trimester, year, ".txt", sep=""))
  parquet_path <- here(std_path, "PNAD_data", year, paste("PNADC_0", trimester, year, ".parquet", sep=""))
  paths <- c(raw_path, parquet_path)
  paths
}