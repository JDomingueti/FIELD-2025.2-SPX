
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
  
}
