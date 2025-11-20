library(arrow)
library(here)
source("deflator.R")

y_start <- 2012
t_start <- 1
y_end <- as.integer(readline("Ano Final: "))
t_end <- as.integer(readline("Trimestre final (1 a 4): "))

tri <- t_start
deflator_path <- here("PNAD_data", "deflator.parquet")
deflator <- read_parquet(deflator_path)
for (year in y_start:y_end) {
  for (trim in tri:4) {
    print(paste0(" -> ", year, ".", trim))
    path <- here("PNAD_data", "Pareamentos", paste0("pessoas_", year, trim, "_", year+1, trim, "_classificado.parquet"))
    dados <- apply_deflator_parquet(path, deflator)
    write_parquet(dados, path)
    if (year == y_end & trim == t_end) break
  }
  tri <- 1
}