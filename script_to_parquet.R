source("utils.R")
source("to_parquet.R")

ano_ini <- as.integer(readline("Ano inicial: "))
tri_ini <- as.integer(readline("Trimestre inicial (1 a 4): "))
ano_end <- as.integer(readline("Ano Final: "))
tri_end <- as.integer(readline("Trimestre final (1 a 4): "))
fim = shift_quarter(ano_end, tri_end, 1)
act_ini = list(year = ano_ini, tri = tri_ini)
while(act_ini$year != fim$year | act_ini$tri != fim$tri) {
    print(paste0("Transformando seguinte trim em parquet: ", act_ini$year, ".", act_ini$tri))
    make_parquet(act_ini$year, act_ini$tri)
    print(paste0(" -> ", act_ini$year, ".", act_ini$tri, " finalizado"))
    act_ini <- shift_quarter(act_ini$year, act_ini$tri, 1)
}