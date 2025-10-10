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
  
  dados_sel <- dados_sel %>%
    filter(VD4020 != 0)

  # calcular a mediana
  mediana_renda <- median(dados_sel$VD4020, na.rm = TRUE)
  return(mediana_renda)
}

# ====== FUNCAO PARA IDENTIFICAR SE UM TRABALHADOR É DE APP DE MOTORISTA OU DE ENTREGA ========
classificar_trabalhador_app <- function(df) {
  df <- df %>%
    mutate(
      # trabalhadores em plataformas digitais de transporte de passageiros
      plataforma_transporte = if_else(
       V4013 == 49030 & V4010 %in% c(8321, 8322),
       1, 0
      ),
      
      # trabalhadores em plataformas digitais de entrega
      plataforma_entrega = if_else(
        V4013 %in% c(49040, 53002) & V4010 %in% c(8321, 8322),
        1, 0
      )
      
    #  #trabalhadores em plataformas digitais de transporte de passageiros
    #   plataforma_transporte = if_else(
    #   V4010 %in% c(8321, 8322),
    #   1, 0
    #   ),
    #  
    #   #trabalhadores em plataformas digitais de entrega
    #   plataforma_entrega = if_else(
    #   V4010 %in% c(8321, 8322),
    #   1, 0
    #  )
    )
  
  return(df)
}

calcular_mediana_por_setor <- function(y, t) {
  quarters <- lapply(0:4, function(i) shift_quarter(y, t, -i))
  
  dfs <- lapply(quarters, function(q) {
    path <- here("PNAD_data", "Pareamentos", paste0("pessoas_", q$year, q$tri, "_", q$year + 1, q$tri, "_classificado.parquet"))
    if (file.exists(path)) {
      read_parquet(path) %>%
        # Filtrar para o ano (y) e trimestre (t) de referência
        filter(Ano == y, Trimestre == t, !is.na(VD4020), VD4020 > 0)
    } else {
      warning(paste("Arquivo nao encontrado:", path))
      NULL
    }
  })
  
  dfs <- Filter(Negate(is.null), dfs)
  
  if (length(dfs) == 0) {
    stop("Nenhum arquivo de dados encontrado para o periodo especificado.")
  }
  dados <- bind_rows(dfs)
  
  # Calcular a mediana da renda POR SETOR (V4013)
  mediana_por_setor <- dados %>%
    filter(!is.na(V4013)) %>% 
    group_by(Setor_CNAE = V4013) %>%
    summarise(
      Mediana_Renda = median(VD4020, na.rm = TRUE),
      N_Trabalhadores = n() # numero de trabalhadores
    ) %>%
    ungroup()
  
  return(mediana_por_setor)
}

# uso: passe o df gerado no retorno da funcao calcular_mediana_por_stor, passe
# o df1 como o df inicial de interesse e o df2 como o df final de interesse
maior_crescimento_setor <- function(df1, df2) {
  df1 <- df1 %>%
    rename(Mediana_Renda = Mediana_Inicio, N_Inicio = N_Trabalhadores)
  df2 <- df2 %>%
    rename(Mediana_Renda = Mediana_Fim, N_Fim = N_Trabalhadores)
  
  # juntar os dois dataframes e calcular o crescimento
  analise_crescimento <- left_join(df1, df2, by = "Setor_CNAE") %>%
    # remover setores que nao aparecem no período final
    filter(!is.na(Mediana_Fim)) %>%
    # calcular a variacao percentual
    mutate(
      Crescimento_Percentual = ((Mediana_Fim - Mediana_Inicio) / Mediana_Inicio) * 100
    ) %>%
    # ordenar pelo maior crescimento
    arrange(desc(Crescimento_Percentual))
  
  # o setor com o maior crescimento é o primeiro da lista
  top_setor <- analise_crescimento %>% top_n(1, Crescimento_Percentual)
  
  cat(paste0(
    "\nO setor com o código CNAE '", top_setor$Setor_CNAE,
    "' teve o maior crescimento de renda mediana, com ",
    round(top_setor$Crescimento_Percentual, 2), "%.\n"
  ))
}