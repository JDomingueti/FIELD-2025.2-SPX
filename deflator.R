library(PNADcIBGE)
library(dplyr)
library(arrow)
library(readxl)
library(tidyr)

# funcao para aplicar o deflator na renda
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

# Função que cria um parquet com os deflatores para cada conjunto (UF, Ano, Trimestre)
create_deflator_df <- function(deflator_path, save_path) {
  def <- read_excel(deflator_path) %>%
    mutate(Trimestre = if_else(trim == "01-02-03", 1, 
                               if_else(trim == "04-05-06", 2,
                                       if_else(trim == "07-08-09", 3, 
                                               if_else(trim == "10-11-12", 4, NA_integer_))))) %>%
    drop_na() %>% select(-trim)
  write_parquet(def, save_path)
}

# Esta função é uma adaptação criada à partir de linhas do código get_pnadc da
# biblioteca PNADcIBGE criada por Gabriel Assunção
# (https://github.com/Gabriel-Assuncao/PNADcIBGE/blob/master/R/get_pnadc.R)
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

# Função que aplica o deflator (path para o parquet ou o parquet) em um dataframe
# (path para o dataframe ou o dataframe)
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