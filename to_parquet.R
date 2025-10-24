library(arrow)
library(PNADcIBGE)
library(here)

std_path <- getwd()

layout_path <- paste(std_path, "/PNAD_data/input_PNADC_trimestral.txt", sep="")
lpath <- here(std_path, "PNAD_data", "input_PNADC_trimestral.txt")

make_path <- function(year, trimester) {
  raw_path <- here("PNAD_data", year, paste("PNADC_0", trimester, year, ".txt", sep=""))
  parquet_path <- here(std_path, "PNAD_data", year, paste("PNADC_0", trimester, year, ".parquet", sep=""))
  paths <- c(raw_path, parquet_path)
  paths
}

make_parquet <- function(year, trimester) {
  columns_to_keep = c("Ano", "Trimestre", "UF", "UPA",
                      "V1008",  # Número de seleção do domicílio
                      "V1014",  # Painel
                      "V1027",  # Peso do domicílio e das pessoas (sem calibração)
                      "V1028",  # Peso do domicílio e das pessoas (com calibração)
                      "V2003",  # Número de ordem
                      "V2005",  # Condição no domicílio
                      "V2007",  # Sexo
                      "V2008",  # Dia de nascimento
                      "V20081", # Mês de nascimento
                      "V20082", # Ano de nascimento 
                      "V2009",  # Idade do morador na data de referência
                      "V2010",  # Cor ou raça
                      "V3009A", # Qual foi o curso mais elevado que ... frequentou anteriormente?
                      "V4010",  # Código da ocupação (cargo ou função) (COD) -> Ver  "Composição dos Grupamentos Ocupacionais" e "Classificação de Ocupações para as Pesquisas Domiciliares – COD" em ANEXO de Notas Metodológicas
                      "V4012",  # Nesse trabalho, ... era: 
                      "V4013",  # Código da principal atividade desse negócio/empresa (CNAE)
                      "V4029",  # Nesse trabalho, ... tinha carteira de trabalho assinada ?
                      "V4040",  # Até o dia ... (último dia da semana de referência) fazia quanto tempo que ... estava nesse trabalho ?
                      "V4041",  # Código da ocupação (cargo ou função) (COD) -> Ver "Classificação nacional de ocupações para pesquisas domiciliares (COD) 2010"
                      "V4043",  # Nesse trabalho secundário, ... era 
                      "VD4001", # Condição em relação à força de trabalho na semana de referência para pessoas de 14 anos ou mais de idade
                      "VD4002", # Condição de ocupação na semana de referência para pessoas de 14 anos ou mais de idade
                      "VD4009", # Posição na ocupação e categoria do emprego do trabalho principal da semana de referência para pessoas de 14 anos ou mais de idade
                      "VD4016", # Rendimento mensal habitual do trabalho principal para pessoas de 14 anos ou mais de idade (apenas para pessoas que receberam em dinheiro, produtos ou mercadorias no trabalho principal)
                      "VD4017", # Rendimento mensal efetivo do trabalho principal para pessoas de 14 anos ou mais de idade (apenas para pessoas que receberam em dinheiro, produtos ou mercadorias no trabalho principal)
                      "VD4019", # Rendimento mensal habitual de todos os trabalhos para pessoas de 14 anos ou mais de idade (apenas para pessoas que receberam em dinheiro, produtos ou mercadorias em qualquer trabalho) 
                      "VD4020", # Rendimento mensal efetivo de todos os trabalhos para pessoas de 14 anos ou mais de idade (apenas para pessoas que receberam em dinheiro, produtos ou mercadorias em qualquer trabalho)
                      "VD4035", # Horas efetivamente trabalhadas na semana de referência em todos os trabalhos para pessoas de 14 anos ou mais de idade
                      ) 

  paths = make_path(year, trimester)

  df <- read_pnadc(paths[1], layout_path, columns_to_keep)
  print("Arquivo txt lido.")
  print("Escrevendo parquet")
  write_parquet(df, paths[2], compression = "snappy")
}

if ((sys.nframe() == 0) | (interactive() & sys.nframe() %/% 4 == 1)) {
  year <- as.integer(readline("Ano dos microdados : "))
  trimester <- as.integer(readline("Trimestre desejado: "))
  make_parquet(year, trimester)
}