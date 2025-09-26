library(PNADcIBGE)
library(dplyr)
library(purrr)
library(here)
library(arrow)
source("utils.R")

std_path <- getwd()
lpath <- here(std_path, "PNAD_data", "input_PNADC_trimestral.txt")

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
                 "VD4020", # Rend. efetivo qq trab.
                 "VD4016", # Rend. habitual trab. princ.
                 "VD4017", # Rend. efetivo trab. princ.
                 "V4010",  # Codigo Ocupacao princ.
                 "V4041",  # Codigo Ocupacao sec.
                 "V4012",  #  Posicao da Ocupacao princ.
                 "V4043",   #  Porsicao da Ocupacao sec.
                 "V20082"   # Ano de nascimento
)

t0 <- shift_quarter(ano_t, tri_t, 0)
t1 <- shift_quarter(ano_t, tri_t, 1)
t2 <- shift_quarter(ano_t, tri_t, 2)
t3 <- shift_quarter(ano_t, tri_t, 3)
t4 <- shift_quarter(ano_t, tri_t, 4)


pnadc_t0_survey <- read_pnadc(make_path(t0$year, t0$tri)[1], lpath, vars=vars_needed)
pnadc_t1_survey <- read_pnadc(make_path(t1$year, t1$tri)[1], lpath, vars=vars_needed)
pnadc_t2_survey <- read_pnadc(make_path(t2$year, t2$tri)[1], lpath, vars=vars_needed)
pnadc_t3_survey <- read_pnadc(make_path(t3$year, t3$tri)[1], lpath, vars=vars_needed)
pnadc_t4_survey <- read_pnadc(make_path(t4$year, t4$tri)[1], lpath, vars=vars_needed)


#pnadc_t_survey  <- get_pnadc(year=ano_t,  quarter=tri_t,  vars=vars_needed)
#pnadc_t4_survey <- get_pnadc(year=ano_t4, quarter=tri_t4, vars=vars_needed)

# Extrair os dados dos objetos survey
#pnadc_t0 <- pnadc_t0_survey$variables
#pnadc_t1 <- pnadc_t1_survey$variables
#pnadc_t2 <- pnadc_t2_survey$variables
#pnadc_t3 <- pnadc_t3_survey$variables
#pnadc_t4 <- pnadc_t4_survey$variables

pessoas_long_bruto <- bind_rows(pnadc_t0_survey, pnadc_t1_survey, pnadc_t2_survey, pnadc_t3_survey, pnadc_t4_survey)
#pessoas_long_bruto <- bind_rows(pnadc_t0, pnadc_t1, pnadc_t2, pnadc_t3, pnadc_t4)

# realiza transformacoes no ds combinado
pessoas_long <- pessoas_long_bruto %>% mutate(domicilio_id = paste(UF, UPA, V1008, V1014, sep = "_"),periodo = paste0("T", Trimestre, "_", Ano)) %>% select(domicilio_id, periodo, all_of(vars_needed))  

write_parquet(pessoas_long, here(std_path, "PNAD_data", "Pareamentos", paste0("pessoas_", ano_t, tri_t, "_", ano_t4, tri_t4, ".parquet")))
#saveRDS(pessoas_long, file = paste0("pessoas_", ano_t, tri_t, "_", ano_t4, tri_t4, ".rds"))

rm(pessoas_long_bruto) #liberar espaco

#prints para verificar
print(head(pessoas_long, 10))
print(paste("Total de registros:", nrow(pessoas_long)))
print(paste(paste0("Registros:","T", tri_t, "_", ano_t), sum(pessoas_long$periodo == paste0("T", tri_t, "_", ano_t))))
print(paste(paste0("Registros:","T", tri_t4, "_", ano_t4), sum(pessoas_long$periodo == paste0("T", tri_t4, "_", ano_t4))))


# Verificar exemplos de IDs criados
print("Exemplos de domicilio_id:")
print(head(unique(pessoas_long$domicilio_id), 5))
