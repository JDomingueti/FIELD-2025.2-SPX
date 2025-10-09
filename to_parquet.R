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
  columns_to_keep = c("Ano", "Trimestre", "UF", "UPA", "V1008", "V1014", "V2003",
                      "V2005", "V2007", "V2009", "V2008", "V2010", "V1027", "V1028", "V3009A", "V20081", "V20082", "VD4016", "VD4002", "VD4020", 
                      "VD4035", "VD4002", "VD4019", "VD4017", "V4013")

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