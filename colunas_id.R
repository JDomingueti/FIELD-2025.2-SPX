library(PNADcIBGE)
library(dplyr)
library(purrr) 
source("utils.R")

periodos_analise = obter_periodos() # obtendo periodos desejados pelo usuario

# Defina os trimestres que você quer comparar
ano_t  <- periodos_analise$ano_inicio; tri_t  <- periodos_analise$tri_inicio   # trimestre inicial
ano_t4 <- periodos_analise$ano_fim; tri_t4 <- periodos_analise$tri_fim  # trimestre +4

# Variáveis necessárias segundo o documento
vars_needed <- c("Ano", "Trimestre", "UF", "UPA", "V1008", "V1014",
                 "V2003",  # ordem da pessoa
                 "V2007",  # sexo
                 "V2009",  # idade
                 "V2005",   # condição no domicílio
                 "V1028", # peso amostral
                 "VD4019", # Rend. habitual qq trab.
                 "VD4016", # Rend. habitual trab. princ.
                 "VD4017", # Rend. efetivo trab. princ.
                 "V4010",  # Codigo Ocupacao princ.
                 "V4041",  # Codigo Ocupacao sec.
                 "V4012",  #  Posicao da Ocupacao princ.
                 "V4043",   #  Porsicao da Ocupacao sec.
                 "V20082"   # Ano de nascimento
)

pnadc_t_survey  <- get_pnadc(year=ano_t,  quarter=tri_t,  vars=vars_needed)
pnadc_t4_survey <- get_pnadc(year=ano_t4, quarter=tri_t4, vars=vars_needed)

# Extrair os dados dos objetos survey
pnadc_t  <- pnadc_t_survey$variables
pnadc_t4 <- pnadc_t4_survey$variables

pessoas_long_bruto <- bind_rows(pnadc_t, pnadc_t4)

# realiza transformacoes no ds combinado
pessoas_long <- pessoas_long_bruto %>%
  mutate(
    # Cria o ID do domicilio
    domicilio_id = paste(UF, UPA, V1008, V1014, sep = "_"),
    
    periodo = paste0("T", Trimestre, "_", Ano)
  ) %>%

select(domicilio_id, periodo, all_of(vars_needed))  
  
saveRDS(pessoas_long, file = paste0("pessoas_", ano_t, tri_t, "_", ano_t4, tri_t4, ".rds"))

rm(pessoas_long_bruto) #liberar espaco

#prints para verificar
print(head(pessoas_long, 10))
print(paste("Total de registros:", nrow(pessoas_long)))
print(paste(paste0("Registros:","T", tri_t, "_", ano_t), sum(pessoas_long$periodo == paste0("T", tri_t, "_", ano_t))))
print(paste(paste0("Registros:","T", tri_t4, "_", ano_t4), sum(pessoas_long$periodo == paste0("T", tri_t4, "_", ano_t4))))


# Verificar exemplos de IDs criados
print("Exemplos de domicilio_id:")
print(head(unique(pessoas_long$domicilio_id), 5))