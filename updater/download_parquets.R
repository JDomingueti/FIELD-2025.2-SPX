library(arrow)
library(PNADcIBGE)
source("utils.R")

std_path <- getwd()

download_parquet <- function(year, trimester, deflator) {
  print(paste0("Arquivo atual: ", year, ".", trimester))
  columns_to_keep = c("Ano", "Trimestre", "UF", "UPA", "V1008", "V1014", "V1022", "V1023", "V1027", "V1028", 
                      "V2003", "V2005", "V2007", "V2008", "V20081", "V20082", "V2009", "V2010",
                      "VD3004", "V4010", "V4012", "V4013", "V4029", "V4040", "V4041", "V4043", #"V3009", "V3009A"
                      "VD4001", "VD4002", "VD4009", "VD4016", "VD4017", "VD4019", "VD4020", "VD4035")
  dir_path <- here(std_path, "PNAD_data", year)
  temp_path <- here(std_path, "Temp")
  if (!dir.exists(dir_path)) dir.create(dir_path, recursive = TRUE)
  if (!dir.exists(temp_path)) dir.create(temp_path)
  if (deflator) columns_to_keep <- append(columns_to_keep, c("Habitual", "Efetivo"))
  df <- get_pnadc(year, trimester, deflator = deflator, labels = FALSE, design = FALSE, savedir = temp_path)[columns_to_keep]
  write_parquet(df, file.path(dir_path, paste0("PNADC_0", trimester, year, ".parquet")), compression = "snappy")
  file.remove(list.files(temp_path, full.names = TRUE))
}

if ((sys.nframe() == 0) | (interactive() & sys.nframe() %/% 4 == 1)) {
  defl <- as.integer(readline(" -> Usar deflatores? 1 para TRUE: "))
  lote <- as.integer(readline(" -> Download em lote? 1 para TRUE: "))
  if (lote == 1) {
    ystart <- as.integer(readline(" -> Ano de início: "))
    trim <- as.integer(readline(" -> Período de início: "))
    yend <- as.integer(readline(" -> Ano de término: "))
    tend <- as.integer(readline(" -> Período de término: "))
    for (year in ystart:yend) {
      for (t in trim:4) {
        download_parquet(year, t, defl == 1)
        if ((year == yend) & (t == tend)) break
      }
      trim <- 1
    }
  } else download_parquet(as.integer(readline(" -> Ano a ser baixado: ")),
                          as.integer(readline(" -> Trimestre a ser baixado: ")),
                          defl == 1)
}