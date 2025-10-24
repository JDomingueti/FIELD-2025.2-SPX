library(dplyr)

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
      
    )
  
  return(df)
}

# ===== FUNCAO PARA ACHAR QUEM SAO JOB SWITCHERS ENTRE OS TRABALHADORES ====== 
filtrar_job_switcher <- function(df) {
  df <- df %>%
    arrange(ID_UNICO, Ano, Trimestre) %>%
    group_by(ID_UNICO) %>%
    mutate(
      VD4001_lag = lag(VD4001),
      V4010_lag = lag(V4010),
      V4013_lag = lag(V4013),
      VD4009_lag = lag(VD4009),
      V4040_lag = lag(V4040),
      
      # Criar col job_switch_event
      job_switch_event = case_when(
        # Caso 1 -> segue ocupado e mudou ocupacao/setor/posicao
        VD4001 == 1 & VD4001_lag == 1 &
          (V4010 != V4010_lag | V4013 != V4013_lag | VD4009 != VD4009_lag) ~ 1,
        
        # Caso 2 -> mesma ocupacao/setor/posicao , mas mudou emprego (tempo de emprego zerou)
        VD4001 == 1 & VD4001_lag == 1 &
          V4010 == V4010_lag & V4013 == V4013_lag & VD4009 == VD4009_lag &
          V4040_lag %in% c(2, 3, 4) & V4040 == 1 ~ 1,
        
        # C.C
        TRUE ~ 0
      )
    ) %>%
    # Se trocou de emprego em algum dos 5 trimestres
    mutate(job_switcher = as.integer(max(job_switch_event))) %>%
    ungroup()
  
  return(df)
}

filtrar_carteira_assinada <- function(df) {
  df <- df %>%
    mutate(
      carteira_assinada = if_else(
        V4029 == 1 , 1, 0
      )
    )
  return(df)
}

filtrar_salario_minimo <- function(df) {
 anos <- 2012:2025
  salarios_minimos <- c(
    "2012" = ,
    "2013" = ,
    "2014" = ,
    "2015" = ,
    "2016" = ,
    "2017" = ,
    "2018" = ,
    "2019" = ,
    "2020" = ,
    "2021" = ,
    "2022" = ,
    "2023" = ,
    "2024" = ,
    "2025" =  
  )


}