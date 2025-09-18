library(PNADcIBGE)
library(dplyr)

# Defina os trimestres que você quer comparar
ano_t  <- 2023; tri_t  <- 4   # trimestre inicial
ano_t4 <- 2024; tri_t4 <- 4  # trimestre +4

# Variáveis necessárias segundo o documento
vars_needed <- c("Ano", "Trimestre", "UF", "UPA", "V1008", "V1014",
                 "V2003",  # ordem da pessoa
                 "V2007",  # sexo
                 "V2009",  # idade
                 "V2005"   # condição no domicílio
)

pnadc_t_survey  <- get_pnadc(year=ano_t,  quarter=tri_t,  vars=vars_needed)
pnadc_t4_survey <- get_pnadc(year=ano_t4, quarter=tri_t4, vars=vars_needed)

# Extrair os dados dos objetos survey
pnadc_t  <- pnadc_t_survey$variables
pnadc_t4 <- pnadc_t4_survey$variables

# Usar paste simples sem formatação numérica
pnadc_t <- pnadc_t %>%
  mutate(domicilio_id = paste(UF, UPA, V1008, V1014, sep = "_"))

pnadc_t4 <- pnadc_t4 %>%
  mutate(domicilio_id = paste(UF, UPA, V1008, V1014, sep = "_"))

# ---------------- PREPARAR NÍVEL DE PESSOA ----------------
# Mantemos cada morador identificado por sexo, idade, condição
pessoas_t <- pnadc_t %>%
  select(domicilio_id, V2003, V2007, V2009, V2005) %>%
  mutate(periodo = paste0("T", tri_t, "_", ano_t))

pessoas_t4 <- pnadc_t4 %>%
  select(domicilio_id, V2003, V2007, V2009, V2005) %>%
  mutate(periodo = paste0("T", tri_t4, "_", ano_t4))

pessoas_long <- bind_rows(pessoas_t, pessoas_t4)

saveRDS(pessoas_long, file = paste0("pessoas_", ano_t, tri_t, "_", ano_t4, tri_t4, ".rds"))

print(head(pessoas_long, 10))
print(paste("Total de registros:", nrow(pessoas_long)))
print(paste("Registros T1_2022:", sum(pessoas_long$periodo == "T4_2023")))
print(paste("Registros T1_2023:", sum(pessoas_long$periodo == "T4_2024")))

# Verificar exemplos de IDs criados
print("Exemplos de domicilio_id:")
print(head(unique(pessoas_long$domicilio_id), 5))