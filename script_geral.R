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
R_missing <- setdiff(R_packages, rownames(installed.packages()))
if (length(R_missing) > 0) {
  cat(" -> Instalando pacotes do R que estão em falta...\n")
  capture.output(install.packages(R_missing))
}

library(reticulate)
tryCatch({
  capture.output(py_config())
}, error = function(e) {
  stop(" -> Não foi encontrada uma versão de Python devidamente instalada. Por favor, instale o Python antes de prosseguir.\n")
})
py_packages <- c("altair",
                 "matplotlib",
                 "numpy",
                 "pandas",
                 "pathlib",
                 "plotly",
                 "pyarrow",
                 "scikit-learn",
                 "seaborn",
                 "streamlit")
env_path <- file.path(getwd(), "venv")
if (!dir.exists(env_path)) {
  cat(" -> Criando ambiente virtual para Python.\n")
  reticulate::virtualenv_create(envname = env_path, 
                                packages = py_packages)
} else {
  python_missing <- setdiff(py_packages, reticulate::py_list_packages()$package)
  if (length(python_missing) > 0) {
    cat(" -> Instalando pacotes do Python em falta...\n")
    reticulate::virtualenv_install(envname = env_path, 
                                   packages = python_missing)
  }
}
capture.output(reticulate::use_virtualenv(virtualenv = env_path, 
                                          required = TRUE))

# Realizando primeiro a importação dos códigos em python para evitar conflitos
tryCatch({
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
#' @title Obtém a data mais recente dos microdados da PNAD Contínua
#'
#' @description
#' Verifica o servidor FTP do IBGE para identificar o último ano e trimestre
#' para o qual os microdados da PNAD Contínua estão disponíveis.
#' A busca é feita iterativamente, voltando um trimestre/ano até encontrar
#' o último arquivo disponível.
#'
#' @param act_year Ano atual (usado como ponto de partida para a busca).
#' @param act_tri Trimestre atual (usado como ponto de partida para a busca).
#'
#' @return
#' Um vetor numérico de dois elementos: \code{c(ultimo_ano, ultimo_trimestre)}.
#' Retorna \code{NULL} se não houver conexão com a internet ou se o servidor do IBGE
#' estiver indisponível.
#'
#' @examples
#' # last_available <- last_data(2025, 1)
#' # print(last_available) # Exemplo: c(2024, 4)
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

#' @title Baixa todos os microdados da PNAD Contínua (2012 ao atual)
#'
#' @description
#' Itera sobre todos os anos de 2012 até o ano e trimestre mais recente disponível
#' e baixa os arquivos Parquet correspondentes.
#' Se o arquivo já existir na pasta 'PNAD_data/[ano]', o download é ignorado.
#' A função depende da função interna 'download_parquet' (definida em 'download_parquets.R').
#'
#' @param act_year O ano mais recente com dados disponíveis (retornado por \code{last_data}).
#' @param act_tri O trimestre mais recente com dados disponíveis (retornado por \code{last_data}).
#'
#' @return
#' Invisível. Cria a estrutura de diretórios e salva os arquivos Parquet.
#'
#' @seealso \code{\link{download_parquet}}
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

#' @title Aplica Pós-Processamento e Classificação Final aos Dados Pareados
#'
#' @description
#' Realiza uma série de etapas de pós-processamento e classificação nos dados
#' de painel de pessoas recém-pareados e classificados.
#' As etapas incluem: aplicação do deflator, classificação de trabalhadores de
#' aplicativo e filtragem de 'job switchers' e 'carteira assinada'.
#' Em seguida, chama scripts Python para clustering e log de renda.
#'
#' @param ano Ano inicial do painel (e.g., 2012 para o painel 2012.1 - 2013.1).
#' @param tri Trimestre inicial do painel.
#'
#' @return
#' Invisível. Sobrescreve o arquivo Parquet classificado com as colunas
#' de deflator e indicadores de filtros/clusters adicionais. Executa side-effects
#' dos scripts Python.
#'
#' @seealso \code{\link{apply_deflator_parquet}}, \code{\link{classificar_trabalhador_app}},
#'   \code{\link{filtrar_job_switcher}}, \code{\link{filtrar_carteira_assinada}}
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

#' @title Processa e Classifica Todos os Painéis de Pareamento
#'
#' @description
#' Itera sobre todos os trimestres de 2012 até o último trimestre disponível
#' (ano_fim = act_year, tri_fim = act_tri) para garantir que todos os painéis
#' de pessoas:
#' 1. Sejam agrupados ('colunas_id_func').
#' 2. Sejam classificados ('classificar_painel_pnadc').
#' 3. Recebam o pós-processamento ('pos_processing').
#'
#' @param act_year O ano mais recente com dados disponíveis (usado como limite superior).
#' @param act_tri O trimestre mais recente com dados disponíveis (usado como limite superior).
#'
#' @return
#' Invisível. Cria e/ou atualiza todos os arquivos Parquet na pasta
#' 'PNAD_data/Pareamentos'.
#'
#' @seealso \code{\link{colunas_id_func}}, \code{\link{classificar_painel_pnadc}},
#'   \code{\link{pos_processing}}
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

#' @title Gera e Atualiza Arquivos CSV de Variação de Renda por Filtro
#'
#' @description
#' Itera sobre uma lista de filtros (e.g., "_0", "_1D", etc.) e verifica se
#' o arquivo CSV correspondente na pasta 'dados_medianas_var' está atualizado.
#' Se o arquivo não existir, estiver desatualizado ou for inválido,
#' a função \code{calcular_variacoes} é chamada para gerar ou recalcular o CSV.
#'
#' @param ano_final O ano do último trimestre a ser incluído no cálculo
#'   da variação de renda (ano_fim do painel).
#' @param tri_final O trimestre do último trimestre a ser incluído no cálculo
#'   da variação de renda (tri_fim do painel).
#'
#' @return
#' Invisível. Cria ou atualiza os arquivos CSV de variação de renda.
#'
#' @seealso \code{\link{calcular_variacoes}}
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
  gerar_estatisticas_pareamento(ano_final, tri_final)
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
    proccess <- readline(" --> ")
    if (proccess == "*") break
    else if (!(proccess %in% c("1", "2", "3", "4"))) {
      cat(" -> Processo inexistente. Escolha novamente.\n")
      next
    }
    if (proccess %in% c("1", "4")) download_all(ultima[1], ultima[2])
    if (proccess %in% c("2", "4")) classify_all(ultima[1], ultima[2])
    if (proccess %in% c("3", "4")) generate_csvs(ultima[1], ultima[2])
  }
}