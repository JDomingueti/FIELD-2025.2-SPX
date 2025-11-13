library(dplyr)
library(tidyr)
library(ggplot2)
library(arrow)
library(here)
library(scales)

regioes <- list(
  c(11, 12, 13, 14, 15, 16, 17), #Norte
  c(21, 22, 23, 24, 25, 26, 27, 28, 29), #Nordeste
  c(31, 32, 33, 34, 35), #Sudeste
  c(41, 42, 43), #Sul
  c(50, 51, 52, 53) #Centro-Oeste
)

grupo_ocupacoes <- list(
  "1" = c(0,1),  # 0 MEMBROS DAS FORÇAS ARMADAS, POLICIAIS E BOMBEIROS MILITARES ; 1 DIRETORES E GERENTES
  "2" = c(2,3),   # 2 PROFISSIONAIS DAS CIÊNCIAS E INTELECTUAIS ; 3 TÉCNICOS E PROFISSIONAIS DE NÍVEL MÉDIO
  "3" = c(4,5,8), # 4 TRABALHADORES DE APOIO ADMINISTRATIVO ; 5 TRABALHADORES DOS SERVIÇOS, VENDEDORES DOS COMÉRCIOS E MERCADOS ; 8 OPERADORES DE INSTALAÇÕES E MÁQUINAS E MONTADORES
  "4" = c(6,7),   # 6 TRABALHADORES QUALIFICADOS DA AGROPECUÁRIA, FLORESTAIS, DA CAÇA E DA PESCA ; 7 TRABALHADORES QUALIFICADOS, OPERÁRIOS E ARTESÃOS DA CONSTRUÇÃO, DAS ARTES MECÂNICAS E OUTROS OFÍCIOS
  "5" = c(9)     # 9 OCUPAÇÕES ELEMENTARES
)

grupo_ocp <- list(
  "1" = c(45, 48),  # Comércio
  "2" = c(1, 2, 3, 41, 42, 43, 49, 50, 51, 52, 53, 55, 56, 58, 59, 60, 61, 62, 63, 64, 64, 66, 68, 69, 70, 71, 72, 73, 74, 75, 77, 78, 79, 80, 81, 82, 84, 85, 86, 87, 88, 90, 91, 92, 93, 94, 95, 96, 97, 99), # Serviços
  "3" = c(5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 35, 36, 37, 38, 39) # Indústria
)

calcular_variacoes <- function(filtro) {
  paste0("Filtro escolhido:", filtro)
  std_path <- getwd()
  
  nome_pasta_saida <- "dados_medianas_var"
  pasta_saida <- here(std_path, nome_pasta_saida)
  
  # Caminho base onde estão os arquivos parquet
  pasta_base <- here(std_path,"PNAD_data", "Pareamentos")
  
  # Lista de trimestres a processar
  anos <- 2012:2025
  trimestres <- 1:4
  
  if (grepl("D", filtro)){
    coluna_renda <- "VD4019_deflat"
    cat("\nUsando renda deflacionada\n")
    is_deflated = TRUE
  } else {
     coluna_renda <- "VD4019"
     cat("\nUsando renda nominal\n")
     is_deflated = FALSE
  }
  
  if (!(filtro %in% c("17", "17D", "18", "18D", "19", "19D", "20", "20D", "21", "21D", "22", "22D"))) {
    filt <- c(filtro)
  } else {
    if (is_deflated){
      if (grepl("17", filtro)) filt <- c("171D", "172D", "173D", "174D", "175D")
      else if (grepl("18", filtro)) filt <- c("181D", "182D", "183D", "184D", "185D", "186D", "187D")
      else if (grepl("19", filtro)) filt <- c("190D", "191D", "192D", "193D", "194D", "195D", "196D", "197D", "198D", "199D")
      else if (grepl("20", filtro)) filt <- c("201D", "202D", "203D")
      else if (grepl("21", filtro)) filt <- c("21AD", "21BD", "21CD", "21DD", "21ED")
      else if (grepl("22", filtro)) filt <- c("22_0D", "22_1D")
    } else {
      if (grepl("17", filtro)) filt <- c("171", "172", "173", "174", "175")
      else if (grepl("18", filtro)) filt <- c("181", "182", "183", "184", "185", "186", "187")
      else if (grepl("19", filtro)) filt <- c("190", "191", "192", "193", "194", "195", "196", "197", "198", "199")
      else if (grepl("20", filtro)) filt <- c("201", "202", "203")
      else if (grepl("21", filtro)) filt <- c("21A", "21B", "21C", "21D", "21D", "21E")
      else if (grepl("22", filtro)) filt <- c("22_0", "22_1")

    }
    l <- nchar(filt[1])
  }
  
  # Loop principal
  for (filtro in filt) {
    
    # Arquivo onde os resultados serão salvos
    arquivo_saida_texto <- here(pasta_saida, paste0("medianas_variacao_renda_", filtro, ".txt"))
    
    # Limpa o arquivo antes de começar
    cat("", file = arquivo_saida_texto)
    
    estatisticas_var_zero <- data.frame(
      ano_final = integer(),
      trimestre = integer(),
      percentual_zero = numeric(),
      percentual_menor_igual_zero = numeric(),
      stringsAsFactors = FALSE
    )
    
    # Data frame para armazenar todos os resultados
    resultados <- data.frame(
      ano_final = integer(),
      trimestre = integer(),
      mediana_variacao = numeric(),
      obs = integer(),
      stringsAsFactors = FALSE
    )
    
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
        
        cat("Processando:", rotulo_primeiro, "->", rotulo_ultimo, "\n")
        
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
            filter(UF %in% regioes[[1]])
  
        } else if (filtro == "6" || filtro == "6D"){
          dados_classificados <- dados_classificados %>%
            filter(UF %in% regioes[[2]])
  
        } else if (filtro == '7' || filtro == '7D'){
          dados_classificados <- dados_classificados %>%
            filter(UF %in% regioes[[3]])
  
        } else if (filtro == '8' || filtro == '8D'){
          dados_classificados <- dados_classificados %>%
            filter(UF %in% regioes[[4]])
  
        } else if (filtro == '9' || filtro == '9D'){
          dados_classificados <- dados_classificados %>%
            filter(UF %in% regioes[[5]])
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
        } else if (grepl("17", filtro)) {  # Cor ou raça
          if (is_deflated) rac <- as.numeric(substring(filtro, l-1, l-1))
          else rac <- as.numeric(substring(filtro, l, l)) 
          #cat("Código atual de raça:", rac, "\n")
          dados_classificados <- dados_classificados[as.numeric(dados_classificados$V2010) == rac,]
        } else if (grepl("18", filtro)) {  # Nível educacional
          if (is_deflated) ed <- as.numeric(substring(filtro, l-1, l-1))
          else ed <- as.numeric(substring(filtro, l, l)) 
          #cat("Código atual de educação:", ed, "\n")
          dados_classificados <- dados_classificados[as.numeric(dados_classificados$VD3004) == ed,]
        } else if (grepl("19", filtro)) {  # Ocupações separadas
          if (is_deflated) ocp <- as.numeric(substring(filtro, l-1, l-1))
          else ocp <- as.numeric(substring(filtro, l, l))
          #cat("Codigo atual de ocupação:", ocp, "\n")
          # Divide-se o código de ocupação para analisar os "Grandes Grupos"
          dados_classificados <- dados_classificados[as.numeric(dados_classificados$V4010) %/% 1000 == ocp,]
        } else if (grepl("20", filtro)) {  # Divisões em Serviço, comércio e Industria
          if (is_deflated) ocp <- substring(filtro, l-1, l-1)
          else ocp <- substring(filtro, l, l)
          #cat("Código atual de divisão:", ocp, "\n")
          dados_classificados <- dados_classificados[as.numeric(dados_classificados$V4013) %/% 1000 %in% grupo_ocp[[ocp]],]
        
        } else if (grepl("21", filtro)) { # Classes de Renda
          if (is_deflated) classe <- substring(filtro, l-1, l-1)
          else classe <- substring(filtro, l, l)
          dados_classificados <- dados_classificados %>%
            filter(grupo_renda == classe)

        } else if (grepl("22", filtro )) { #Clusters de Renda
          if (is_deflated) cluster <- as.numeric(substring(filtro, l-1, l-1))
          else cluster <- as.numeric(substring(filtro, l, l))
          dados_classificados <- dados_classificados %>%
            filter(grupo_renda_kmeans == cluster) 
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
        #cat("Número de observações:", num_obs, "\n")
        
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
      write.csv(estatisticas_var_zero, here(pasta_saida, "estatisticas_variacao_nula.csv"), row.names = FALSE)
    }
  
    # (Opcional) salva como CSV para análise posterior
    write.csv(resultados, here(pasta_saida, paste0("medianas_variacao_renda_", filtro, ".csv")), row.names = FALSE)
  
    cat("\n Loop concluído! Resultados salvos em:", arquivo_saida_texto, "\n")
    
  }
}


if ((sys.nframe() == 0) | (interactive() & sys.nframe() %/% 4 == 1)) {
  # Escolha de filtro para calcular a mediana
  repeat {
    cat("Escolha o filtro:\n 0 = Sem filtro\n 1 = Trab de App\n 2 = Job Switcher\n 3 = Masculino\n 4 = Feminino\n 5 = Norte\n 6 = Nordeste\n 7 = Centro-Oeste\n 8 = Sul\n 9 = Sudeste\n ")
    cat("10 = Carteira Assinada\n 11 = Média \n 12 = Percentil 25\n 13 = Percentil 75\n 14 = 14-24 anos\n 15 = 25-54 anos\n 16 = 55+ anos\n 17 = Raças\n 18 = Educação\n 19 = Ocupações\n 20 = Com. / Ind. / Serv.\n 21 = Classes de Renda\n 22 = Cluster de Renda\n Caso queira adicionar deflator basta colocar o codigo seguido de 'D' (exemplo: 0D)\n")
    filtro <- readline(" -> ")
    if (filtro %in% c("0", "1", "2", "3","4","5", "6", "7", "8", "9", "10","11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "0D", "1D", "2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "10D", "11D", '12D', "13D", "14D", "15D", "16D", "17D", "18D", "19D", "20D", "21D", "22D")) break
    cat("FIltro Inválido")
  }
  calcular_variacoes(filtro)
}