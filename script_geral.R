# Preparação do ambiente local para todos os códigos
R_packages <- c("arrow",
                        "dplyr",
                        "ggplot2",
                        "here",
                        "httr",
                        "PNADcIBGE",
                        "projmgr",
                        "purrr",
                        "RCurl",
                        "readxl",
                        "reticulate",
                        "scales",
                        "tidyr")
suppressMessages(install_packages(setdfiff(R_packages, rownames(installed.packages()))))
suppressMessages(library(reticulate))
if (reticulate::py_available()) {
  py_packages <- c("altair==5.5.0",
                   "matplotlib==3.10.7",
                   "numpy==2.3.4",
                   "pandas==2.3.3",
                   "pathlib",
                   "plotly",
                   "pyarrow==21.0.0",
                   "scikit-learn",
                   "seaborn",
                   "streamlit==1.51.0")
  env_path <- file.path(getwd(), "venv")
  if (!dir.exists(env_path)) {
    cat(" -> Criando ambiente virtual para Python.\n")
    supressMessages(reticulate::virtualenv_create(envname = env_path, 
                                                  packages = py_packages))
  } else {
    suppressMessages(reticulate::virtualenv_install(envname = env_path, 
                                                    packages = py_packages))
  }
} else {
  stop("\n !! Erro: Python não disponível na máquina.\n")
}

# Realizando primeiro a importação dos códigos em python para evitar conflitos
tryCatch({
  library(reticulate)
  suppressWarnings(use_virtualenv("./venv", required = TRUE))
  lr <- reticulate::import_from_path("log_renda", path=getwd())
  fc <- reticulate::import_from_path("fixo_cluster_renda", path=getwd())
  kmc <- reticulate::import_from_path("kmeans_cluster_renda", path=getwd())
  }, 
  error = function(e) {
    stop("\n !! Erro: Não foi possível importar os códigos do python.\n -> Tente reiniciar o R e rode novamente (Conflito em ordem de importação)\n")
  }
)


# Importando bibliotecas do R e códigos em R utilizados

library(here)
library(httr)
library(projmgr)
library(dplyr)
library(RCurl)
source("colunas_id.R")
source("classificação.R")
source("deflator.R")
source("download_parquets.R")
source("variacao_renda.R")
source("filtrar_trabalhadores.R")
source("pareamento_stats.R")

# ========== FUNÇÕES ==========

last_data <- function(act_year, act_tri) {
  last_year <- act_year
  last_tri <- act_tri
  repeat {
  ftpdir <- "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados/"
  if (!projmgr::check_internet()) {
    message("The internet connection is unavailable.\n")
    return(NULL)
  }
  if (httr::http_error(httr::GET(ftpdir, httr::timeout(60)))) {
    message("The microdata server is unavailable.\n")
    return(NULL)
  }
  restime <- getOption("timeout")
  on.exit(options(timeout=restime))
  options(timeout=max(600, restime))
  ftpdata <- paste0(ftpdir, last_year, "/")
  datayear <- unlist(strsplit(unlist(strsplit(unlist(strsplit(gsub("\r\n", "\n", RCurl::getURL(ftpdata, dirlistonly=TRUE, .opts=list())), "\n")), "<a href=[[:punct:]]")), ".zip"))
  dataname <- datayear[which(startsWith(datayear, paste0("PNADC_0", last_tri, last_year)))]
  if (length(dataname) == 0)
    if (last_tri == 1) {
      last_year <- last_year - 1
      last_tri <- 4
    } else last_tri <- last_tri - 1
  else break
  }
  return(c(last_year, last_tri))
}

download_all <- function(act_year, act_tri) {
  std_path <- here(getwd(), "PNAD_data")
  for (year in 2012:act_year) {
    tmp_path <- here(std_path, year)
    if (!dir.exists(tmp_path)) dir.create(tmp_path, recursive = TRUE)
    for (tri in 1:4) {
      if ((tri > act_tri) & year == act_year) break
      else if (file.exists(here(tmp_path, paste0("PNADC_0", tri, year, ".parquet")))) next
      else {
        cat(paste0("Fazendo download dos dados de ", year, ".", tri))
        download_parquet(year, tri, TRUE)
      }
    }
  }
  cat("\n -> Todos os dados estão baixados!\n")
}

pos_processing <- function(ano, tri) {
  path <- here(getwd(), "PNAD_data", "Pareamentos", paste0("pessoas_", ano, tri, '_', ano+1, tri, "_classificado.parquet"))
  df <- read_parquet(path)
  df <- df %>%
    apply_deflator_parquet(here("PNAD_data", "deflator.parquet")) %>%
    classificar_trabalhador_app() %>%
    filtrar_job_switcher %>%
    filtrar_carteira_assinada
  write_parquet(df, path)
  capture.output({
    lr$processar_dados(path) #log_renda
    fc$faixas(as.integer(ano), as.integer(tri)) #fixo_cluster_renda
    kmc$cluster(as.integer(ano), as.integer(tri), as.integer(2)) #kmeans_cluster_renda
  })
}


classify_all <- function(act_year, act_tri) {
  std_path <- here(getwd(), "PNAD_data", "Pareamentos")
  for (year in 2012:(act_year-1)) {
    if (!dir.exists(std_path)) dir.create(std_path, recursive = TRUE)
    for (tri in 1:4) {
      if ((tri > act_tri) & year == (act_year-1)) break
      if (!file.exists(here(std_path, paste0("pessoas_", year, tri, "_", year+1, tri, ".parquet")))) {
        cat(paste0("Agrupando dados do período ", year, ".", tri, " -> ", year+1, ".", tri))
        colunas_id_func(list(ano_inicio = year,tri_inicio = tri,ano_fim = year+1,tri_fim = tri), TRUE)
      }
      if (!file.exists(here(std_path, paste0("pessoas_", year, tri, "_", year+1, tri, "_classificado.parquet")))) {
        cat(paste0("Classificando dados do período ", year, ".", tri, " -> ", year+1, ".", tri))
        capture.output(classificar_painel_pnadc(here(getwd(), "PNAD_data", "Pareamentos", paste0("pessoas_", year, tri, "_", year+1, tri, ".parquet"))))
        pos_processing(year, tri)
      }
    }
  }
  cat(" -> Todos os arquivos completamente atualizados!\n")
}

generate_csvs <- function(ano_final, tri_final) {
  ano_final <- as.integer(ano_final)
  tri_final <- as.integer(tri_final)
  
  filtros <- c(as.character(0:22), paste0(as.character(0:22), "D"))
  std_path <- here(getwd(), "dados_medianas_var")
  all_files <- list.files(std_path, full.names = FALSE)
  
  for (filtro in filtros) {
    file_was_processed <- FALSE # controla se o arquivo foi processado
    
    for (file in all_files) {
      
      # verifica se o nome base esta no dir
      base_match <- grepl(paste0("medianas_variacao_renda_", filtro), file)
      
      if (base_match) {

        # logica para extrair os nomes corretos (sufixos)        
        is_exact_match <- FALSE
        if (filtro == "21D") {
          is_exact_match <- grepl("DD.csv", file)
        } else if (grepl("D", filtro)) {
          # Garante que 'D.csv' não pegue 'DD.csv'
          is_exact_match <- grepl("D.csv", file) && !grepl("DD.csv", file) 
        } else {
          # Garante que '.csv' não pegue 'D.csv'
          is_exact_match <- grepl(".csv", file, fixed = TRUE) && !grepl("D.csv", file)
        }
        
        if (is_exact_match) {
          file_was_processed <- TRUE 
          file_path <- file.path(std_path, file)
          
          df <- tryCatch({
            readr::read_csv(file_path, show_col_types = FALSE)
          }, error = function(e) {
            message(paste("Aviso: Erro ao ler", file, ". Sera regenerado."))
            return(NULL)
          })
          
          # verifica se o file é valido e se esta atualizado
          if (!is.null(df) && nrow(df) > 0) {
            last_row <- nrow(df)
            is_updated <- (df$ano_final[last_row] == ano_final) && (df$trimestre[last_row] == tri_final)
            
            if (isTRUE(is_updated)) {
              message(paste0("Arquivo ", filtro, " Ja atualizado. Pulando."))
            } else {
              cat(paste0("Recalculando e atualizando dados do filtro ", filtro, "\n"))
              capture.output(calcular_variacoes(filtro, ano_final, tri_final))
            }
          } else {
            cat(paste0("Arquivo inválido/vazio para ", filtro, ". Gerando novamente...\n"))
            capture.output(calcular_variacoes(filtro, ano_final, tri_final))
          }
          
          break # quebra o loop para o prox filtro
        }
      }
    }
    
    # Se file_was_processed for FALSE, o arquivo não existe na pasta.
    if (!file_was_processed) {
      cat(paste0("Gerando dados do filtro ", filtro, " (Primeira Criação)\n"))
      capture.output(calcular_variacoes(filtro, ano_final, tri_final))
    }
  }
  
  cat("\n -> Arquivos para plotagem atualizados!\n")
}


if ((sys.nframe() == 0) | (interactive() & sys.nframe() %/% 4 == 1)) {
  ano_atual <- Sys.Date() %>% format("%Y") %>% as.numeric()
  tri_atual <- Sys.Date() %>% format("%m") %>% as.numeric() %>%
              (function(mes) if_else(mes < 4, 1, if_else(mes < 6, 2, if_else(mes < 9, 3, 4)))) # Retorna o trimestre com base no mês
  ultima <- unlist(last_data(ano_atual, tri_atual))  # Retorna uma lista c(year, tri) com o último ano e trimestre com dados disponíveis
  cat("======== SCRIPT PARA ATUALIZAR TODOS OS DADOS ========\n")
  cat(" Processos disponíveis no script.\n")
  cat(" -> [1] Verificar o download dos arquivos base;\n")
  cat(" -> [2] Verificar os dados classificados;\n")
  cat(" -> [3] Verificar os dados para plot;\n")
  cat(" -> [4] Todos os processos;\n")
  cat(" -> [*] Parar execução.\n")
  cat("======================================================\n")
  
  repeat {
    cat("\n -> Escolha o processo a ser realizado:\n")
    proccess <- readline(" --> : ")
    if (proccess == "*") break
    else if (!(proccess %in% c("1", "2", "3", "4"))) {
      cat(" -> Processo inexistente. Escolha novamente.\n")
      next
    }
    if (proccess %in% c("1", "4")) download_all(ultima[1], ultima[2])
    if (proccess %in% c("2", "4")) classify_all(ultima[1], ultima[2])
    if (proccess %in% c("3", "4")) {
      #generate_csvs(ultima[1], ultima[2])
      gerar_estatisticas_pareamento(as.integer(ultima[1]), as.integer(ultima[2]))
    }
  }
}