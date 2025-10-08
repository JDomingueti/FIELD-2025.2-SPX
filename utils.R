library(here)
library(dplyr)
library(arrow)

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

# funcao para andar n trimestres para frente ou para trás
shift_quarter <- function(year, tri, n) {
  # converte para um numero abs de trimestres desde o ano "0"
  q_abs <- (year * 4) + (tri - 1) + n
  new_year <- q_abs %/% 4
  new_tri <- (q_abs %% 4) + 1
  return(list(year = new_year, tri = new_tri))
}

# ====== FUNCAO PARA PEGAR A MEDIANA DA RENDA DE UM TRI E ANO PARA 100% DOS INDIVIDUOS ======
catch_median_renda <- function(y, t) {
  # gerar lista de tris (alvo + 4 tri anteriores)
  quarters <- lapply(0:4, function(i) shift_quarter(y, t, -i))
  
  # ler os 5 parquets correspondentes
  dfs <- lapply(quarters, function(q) {
    path <- here("PNAD_data", "Pareamentos", paste0("pessoas_", q$year, q$tri, "_", q$year + 1, q$tri, "_classificado.parquet"))
    if (file.exists(path)) {
      read_parquet(path) %>%
      #filtrar apenas para o ano (y) e trimestre (t)
        filter(Ano == y, Trimestre == t, classe_individuo %in% 1:3) %>%
        mutate(ano_arquivo = q$year, tri_arquivo = q$tri)
      
    } else {
      warning(pate("Arquivo nao encontrado:", path))
      NULL
    }
  })
  # caso algum arquivo nao exista
  dfs <- Filter(Negate(is.null), dfs)
  
  # concatenar os dados
  dados <- bind_rows(dfs)
  
  # selecionar cols relevantes
  dados_sel <- dados %>%
    select(ID_UNICO, VD4020, Ano, Trimestre) # renda efetiva total
  
  # calcular a mediana
  mediana_renda <- median(dados_sel$VD4020, na.rm = TRUE)
  return(mediana_renda)
}