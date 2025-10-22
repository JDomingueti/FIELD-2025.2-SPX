library(PNADcIBGE)
library(dplyr)
library(arrow)
library(readxl)
library(dplyr)

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

# Função que aplica o deflator (path para o parquet ou o parquet) em um dataframe
# (path para o dataframe ou o datafrane)
apply_deflator_parquet <- function(df, deflator) {
  if (is.character(df)) {
    dat <- read_parquet(df)
  } else dat <- df
  if (is.character(deflator)) {
    def <- read_parquet(deflator)
  } else def <- deflator
  dfm <- merge(dat, def, by=c("Ano", "UF", "Trimestre"))
  dfm$VD4016 <- dfm$VD4016 * dfm$Habitual
  dfm$VD4017 <- dfm$VD4017 * dfm$Efetivo
  dfm$VD4019 <- dfm$VD4019 * dfm$Habitual
  dfm$VD4020 <- dfm$VD4020 * dfm$Efetivo
  dfm[c("Habitual", "Efetivo")] <- list(NULL)
  return(dfm)
}