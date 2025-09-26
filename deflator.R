library(PNADcIBGE)
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

