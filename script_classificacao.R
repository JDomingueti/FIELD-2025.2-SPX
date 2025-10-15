source("classificação.R")
library(here)

is_parquet <- as.integer(readline(" -> Os arquivos já está em formato parquet. 1 para TRUE: ")) == 1
ano_ini <- as.integer(readline("Ano inicial: "))
tri_ini <- as.integer(readline("Trimestre inicial (1 a 4): "))
ano_end <- as.integer(readline("Ano Final: "))
tri_end <- as.integer(readline("Trimestre final (1 a 4): "))
fim = shift_quarter(ano_end, tri_end, 1)
act_ini = list(year=ano_ini, tri=tri_ini)
act_end <- shift_quarter(act_ini$year, act_ini$tri, 4)
while(act_ini$year != fim$year | act_ini$tri != fim$tri) {
    print(paste0("Identificando linhas para: [", act_ini$year, ".", act_ini$tri, "] -> [", act_end$year, ".", act_end$tri, "]"))
    colunas_id_func( list( ano_inicio = act_ini$year,tri_inicio = act_ini$tri,
                           ano_fim = act_end$year, tri_fim = act_end$tri), is_parquet)
    print(paste0("Classificando para: [", act_ini$year, ".", act_ini$tri, "] -> [", act_end$year, ".", act_end$tri, "]"))
    classificar_painel_pnadc(here(getwd(), "PNAD_data", "Pareamentos", paste0("pessoas_", 
                                                                            act_ini$year, act_ini$tri,
                                                                            "_", act_end$year, act_end$tri,
                                                                            ".parquet")))
    print(paste0("Finalizado para: [", act_ini$year, ".", act_ini$tri, "] -> [", act_end$year, ".", act_end$tri, "]"))
    act_ini <- shift_quarter(act_ini$year, act_ini$tri, 1)
    act_end <- shift_quarter(act_ini$year, act_ini$tri, 4)
}