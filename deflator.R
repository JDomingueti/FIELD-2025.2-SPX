library(PNADcIBGE)
library(dplyr)
library(arrow)
library(readxl)
library(tidyr)

#' @title Aplica o Deflator de Renda Usando Funções da PNADcIBGE
#'
#' @description
#' Carrega os microdados brutos da PNAD Contínua, aplica os rótulos de variáveis
#' (labeller) e em seguida aplica o deflator utilizando as funções do pacote
#' \code{PNADcIBGE}. Finalmente, calcula as colunas de renda real (\code{_real}).
#'
#' @param df_path Caminho para o arquivo de microdados brutos da PNADc (.txt ou .zip).
#' @param input_txt_path Caminho para o arquivo de layout/dicionário da PNADc.
#' @param vars_needed Vetor de strings com os nomes das variáveis a serem lidas.
#' @param dict.path Caminho para o arquivo do dicionário de rótulos de variáveis.
#' @param deflator.path Caminho para o arquivo Excel ou similar contendo os deflatores.
#'
#' @return
#' Um dataframe da PNADc com as colunas de deflator (Habitual e Efetivo) e novas
#' colunas de renda real (\code{VD4019_real}, \code{VD4020_real}, etc.).
#'
#' @import PNADcIBGE
#' @importFrom dplyr mutate
#'
#' @seealso \code{\link[PNADcIBGE]{read_pnadc}}, \code{\link[PNADcIBGE]{pnadc_labeller}}, \code{\link[PNADcIBGE]{pnadc_deflator}}
apply_deflator <- function(df_path, input_txt_path, vars_needed, dict.path, deflator.path) {
  
  pnadc.df <- read_pnadc(microdata=df_path, input_txt=input_txt_path, vars=vars_needed)
  pnadc.df <- pnadc_labeller(data_pnadc = pnadc.df, dictionary.file = dict.path)
  pnadc.df <- pnadc_deflator(data_pnadc = pnadc.df, deflator.file = deflator.path)
  
  pnadc.df <- pnadc.df %>%
    mutate(
      VD4019_real = VD4019 * Habitual,
      VD4020_real = VD4020 * Efetivo,
      VD4016_real = VD4016 * Habitual,
      VD4017_real = VD4017 * Efetivo
    )
  
  return(pnadc.df)
}

#' @title Cria o Arquivo Parquet Consolidado de Deflatores
#'
#' @description
#' Lê o arquivo de deflatores da PNADc (geralmente um Excel), converte o formato
#' de trimestre (e.g., "01-02-03" para 1) e salva os dados limpos (colunas UF, Ano,
#' Trimestre, Habitual, Efetivo) em formato Parquet para uso eficiente.
#'
#' @param deflator_path Caminho para o arquivo original de deflatores (.xls ou .xlsx).
#' @param save_path Caminho completo onde o arquivo Parquet de deflatores será salvo.
#'
#' @return
#' Invisível. Cria um arquivo Parquet no caminho especificado.
#'
#' @importFrom readxl read_excel
#' @importFrom dplyr mutate if_else drop_na select
#' @importFrom arrow write_parquet
create_deflator_df <- function(deflator_path, save_path) {
  def <- read_excel(deflator_path) %>%
    mutate(Trimestre = if_else(trim == "01-02-03", 1, 
                               if_else(trim == "04-05-06", 2,
                                       if_else(trim == "07-08-09", 3, 
                                               if_else(trim == "10-11-12", 4, NA_integer_))))) %>%
    drop_na() %>% select(-trim)
  write_parquet(def, save_path)
}

#' @title Baixa, Descompacta e Prepara o Arquivo de Deflatores da PNADc
#'
#' @description
#' Função adaptada da lógica da biblioteca PNADcIBGE para automatizar o download
#' do arquivo ZIP de deflatores do servidor FTP do IBGE. Descompacta o arquivo,
#' identifica o arquivo Excel de deflatores e chama \code{create_deflator_df}
#' para criar o arquivo Parquet final, removendo os arquivos temporários.
#' Esta função é uma adaptação criada à partir de linhas do código get_pnadc da
#' biblioteca PNADcIBGE criada por Gabriel Assunção
#' (https://github.com/Gabriel-Assuncao/PNADcIBGE/blob/master/R/get_pnadc.R)
#'
#' @param savedir Diretório base onde o arquivo ZIP será baixado e descompactado (e.g., "PNAD_data").
#'
#' @return
#' Invisível. Baixa, processa e salva o arquivo \code{deflator.parquet}.
#'
#' @importFrom utils download.file unzip
#' @importFrom RCurl getURL
#' @importFrom here here
#'
#' @seealso \code{\link{create_deflator_df}}
baixar_deflator <- function(savedir) {
  library(utils)
  library(RCurl)
  library(here)
  ftpdir <- "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados/"
  docfiles <- unlist(strsplit(unlist(strsplit(unlist(strsplit(gsub("\r\n", "\n", RCurl::getURL(paste0(ftpdir, "Documentacao/"), dirlistonly=TRUE, .opts=list())), "\n")), "<a href=[[:punct:]]")), ".zip"))
  defzip <- paste0(docfiles[which(startsWith(docfiles, "Deflatores"))], ".zip")
  utils::download.file(url=paste0(ftpdir, "Documentacao/", defzip), destfile=paste0(savedir, "/Deflatores.zip"), mode="wb")
  utils::unzip(zipfile=paste0(savedir, "/Deflatores.zip"), exdir=savedir)
  defname <- dir(savedir, pattern=paste0("^deflator_PNADC_.*\\_trimestral_.*\\.xls$"), ignore.case=FALSE)
  deffile <- paste0(savedir, "/", defname)
  deffile <- rownames(file.info(deffile)[order(file.info(deffile)$mtime),])[length(deffile)]
  create_deflator_df(deffile, here("PNAD_data", "deflator.parquet"))
  file.remove(here("PNAD_data", "Deflatores.zip"))
  file.remove(deffile)
}

#' @title Aplica Deflatores de Renda Usando Arquivos Parquet
#'
#' @description
#' Aplica os deflatores \code{Habitual} e \code{Efetivo} (lidos de um Parquet) a um
#' dataframe de microdados da PNADc. A função verifica se o deflator está atualizado;
#' caso contrário, chama \code{baixar_deflator}. Adiciona novas colunas
#' de renda deflacionada (e.g., \code{VD4019_deflat}) e remove as colunas temporárias
#' de deflator (\code{Habitual} e \code{Efetivo}) antes de retornar o dataframe.
#'
#' @param df O dataframe de microdados da PNADc (ou caminho para o arquivo Parquet).
#' @param deflator O dataframe de deflatores (ou caminho para o arquivo Parquet).
#'
#' @return
#' O dataframe original com quatro colunas de renda deflacionada (e.g., \code{VD4019_deflat}).
#'
#' @importFrom arrow read_parquet
#' @importFrom dplyr filter
#' @importFrom here here
#'
#' @seealso \code{\link{baixar_deflator}}
apply_deflator_parquet <- function(df, deflator) {
  if (is.character(df)) {
    dat <- read_parquet(df)
  } else dat <- df
  if (length(setdiff(c("Habitual", "Efetivo"), names(dat))) > 0) {
    if (is.character(deflator)) {
      if (!file.exists(deflator)) baixar_deflator(here("PNAD_data"))
      def <- read_parquet(deflator)
    } else def <- deflator
    last_year <- max(dat$Ano)
    last_trim <- max(dat[dat$Ano == last_year,]$Trimestre)
    if (nrow(filter(def, Ano == last_year, Trimestre == last_trim)) == 0) {
      cat("Dados para deflação desatualizados. Baixando nova base de deflatores.\n")
      baixar_deflator(here("PNAD_data"))
      cat("Realizando nova tentativa de aplicar deflatores...\n")
      return(apply_deflator_parquet(dat, here("PNAD_data", "deflator.parquet")))
    }
    dfm <- merge(dat, def, by=c("Ano", "UF", "Trimestre"))
  } else dfm <- dat
  dfm$VD4016_deflat <- dfm$VD4016 * dfm$Habitual
  dfm$VD4017_deflat <- dfm$VD4017 * dfm$Efetivo
  dfm$VD4019_deflat <- dfm$VD4019 * dfm$Habitual
  dfm$VD4020_deflat <- dfm$VD4020 * dfm$Efetivo
  dfm[c("Habitual", "Efetivo")] <- list(NULL)
  return(dfm)
}