from pathlib import Path
import pandas as pd
# import matplotlib.pyplot as plt
import plotly.express as px
from to_parquet import make_data_paths

est = {
    "11": "Rondônia",
    "12": "Acre",
    "13": "Amazonas",
    "14": "Roraima",
    "15": "Pará",
    "16": "Amapá",
    "17": "Tocantins",
    "21": "Maranhão",
    "22": "Piauí",
    "23": "Ceará",
    "24": "Rio Grande do Norte",
    "25": "Paraíba",
    "26": "Pernambuco",
    "27": "Alagoas",
    "28": "Sergipe",
    "29": "Bahia",
    "31": "Minas Gerais",
    "32": "Espírito Santo",
    "33": "Rio de Janeiro",
    "35": "São Paulo",
    "41": "Paraná",
    "42": "Santa Catarina",
    "43": "Rio Grande do Sul",
    "50": "Mato Grosso do Sul",
    "51": "Mato Grosso",
    "52": "Goiás",
    "53": "Distrito Federal"
}

reg = {
    "11": "Norte",
    "12": "Norte",
    "13": "Norte",
    "14": "Norte",
    "15": "Norte",
    "16": "Norte",
    "17": "Norte",
    "21": "Nordeste",
    "22": "Nordeste",
    "23": "Nordeste",
    "24": "Nordeste",
    "25": "Nordeste",
    "26": "Nordeste",
    "27": "Nordeste",
    "28": "Nordeste",
    "29": "Nordeste",
    "31": "Sudeste",
    "32": "Sudeste",
    "33": "Sudeste",
    "35": "Sudeste",
    "41": "Sul",
    "42": "Sul",
    "43": "Sul",
    "50": "Centro",
    "51": "Centro",
    "52": "Centro",
    "53": "Centro"
    # "Norte" : ["11", "12", "13", "14", "15", "16", "17"],
    # "Nordeste": ["21", "22", "23", "24", "25", "26", "27", "28", "29"],
    # "Centro": ["50", "51", "52", "53"],
    # "Sudeste": ["31", "32", "33", "35"],
    # "Sul": ["41", "42", "43"]
}

esc = {
    "01" : "Creche",
    "02" : "Pré-escola",
    "03" : "Classe de Alfab.",             # Alfab. : Alfabetização
    "04" : "Alfab. Jovens/Adultos",       
    "05" : "Elementar",
    "06" : "Médio 1º ciclo",
    "07" : "Regular do 1º grau",
    "08" : "Supletivo do 1º grau",         # (EJA : Educação de jovens e adultos, entra aqui também)
    "09" : "Ensino ientífico",             # ( Antigo científico, clássico, etc. - médio 2º ciclo )
    "10" : "Regular do 2º grau",
    "11" : "Supletivo do 2º grau",
    "12" : "Superior",
    "13" : "Nível superior",
    "14" : "Mestrado",
    "15" : "Doutorado",
    "#"  : "Sem resposta"
}

rac = {
    "1": "Branca",
    "2": "Preta",
    "3": "Amarela",
    "4": "Parda",
    "5": "Indígena",
    "9": "Ignorado",
    "#": "Sem resposta"
}

sex = {
    "1": "Homem",
    "2": "Mulher",
    "#": "Sem resposta"
}

cols = {
    "1": "UF",
    "2": "UF",
    "3": "V2007",
    "4": "V2010",
    "5": "V3009A",
    }

filt = {
    "1": reg,
    "2": est,
    "3": sex,
    "4": rac,
    "5": esc,
}

titles = {
   "1": "Respostas por Região",
   "2": "Respostas por Estados",
   "3": "Respostas por Sexo",
   "4": "Respostas por Raça",
   "5": "Respostas por Escolarização"
}

def group_columns(path:str, col_names:list[str], filters:list[dict]):
    '''
    Dado um arquivo com formato parquet, uma coluna deste arquivo e um dicionário
    para filtro, produz um dicionário com as colunas agrupadas de acordo com a 
    divisão do filtro passado como parâmetro.

    Parameters:
        path (str): Caminho para um arquivo .parquet
        col_name (str): Nome da coluna do parquet a ser analisada 
        filter (dict): Filtro para agrupamento dos valores da coluna esoclhida

    Returns:
        Retorna um dicionário com as linhas do arquivo agrupadas (em cada divisão 
        do filtro) e um int com o total de linhas analisadas
    '''
    parq = pd.read_parquet(path, columns=col_names)
    total_lines = len(parq)
    parq.fillna("#", inplace=True)
    parq.dropna(inplace=True, ignore_index=True)
    nones = total_lines - len(parq)
    if (nones > 0) : print(f"Found {nones} None's on the colum {col_names}. It",
                        f" corresponds to {nones/total_lines:%} of all the data.")
    pd_dict = parq.to_dict()
    res = {}
    k_filter = []
    if (len(col_names) == 1):
        for val in list(pd_dict[col_names[0]].values()):
            if (filters[0][val] in k_filter):
                res[filters[0][val]] += 1
            else:
                res[filters[0][val]] = 1
                k_filter.append(filters[0][val])
    else:
        for t in zip(*(pair.values() for pair in list(pd_dict.values()))):  # Organiza todas linhas em uma lista onde cada elemento é uma tupla com os elementos de cada coluna e itera nessa lista
            n_key = '/'.join(filters[i][v] for i,v in enumerate(t))
            if (n_key in k_filter):
                res[n_key] += 1
            else:
                res[n_key] = 1
                k_filter.append(n_key)
    return res, total_lines

if __name__ == '__main__':
    run0 = True
    filts = ["1", "2", "3", "4", "5"]
    while (run0):
        run1 = True
        y = input("Ano dos microdados:")
        if (y == "*"):
            run0 = False
            break
        elif (y not in ["2020", "2021", "2022", "2023", "2024", "2025"]):
            continue
        t = input("Trimestre desejado:")
        if (t == "*"):
            run0 = False
            break
        elif (t not in filts):
            continue
        _, parquet_path = make_data_paths(y, t)
        print("Inputs: \n -> \"*\" : Finalizar execução\n -> \"-\" : Mudar ano/trimestre")
        print(" -> \"1\" : Filtrar por região \n -> \"2\" : Filtrar por estado\n -> \"3\" : Filtrar",
            "por sexo\n -> \"4\" : Filtrar por raça\n -> \"5\" : Filtrar por escolaridade\n -> \"6\" : Dois filtros")
        w_filter = []
        while(run1):
            usr_ans = input("Filtro utilizado:")
            if (usr_ans == "*"):
                run0 = False
                run1 = False
                break
            elif (usr_ans == "-"):
                run1 = False
                break
            elif (usr_ans in filts):
                title = titles[usr_ans]
                w_filter, total_ans = group_columns(parquet_path, [cols[usr_ans]], [filt[usr_ans]])
            elif (usr_ans == "6"):
                title = "Respostas com dois filtros"
                print(" -> Digite o número dos dois filtros\n -> Opções: 1; 3; 4; 5 <-\n")
                ans_d = [input(" -> Filtro 1 : "), input(" -> Filtro 2 : ")]
                if ("*" in ans_d):
                    run1 = False
                    run0 = False
                    break
                elif (("2" in ans_d)):
                    print(" -> Não é possível utilizar o filtro de estado em conjunto.\n")
                    break
                elif not ((ans_d[0] in filts) and (ans_d[1] in filts)):
                    print(" -> Ao menos um dos filtros inseridos são inválidos.\n")
                    continue
                w_filter, total_ans = group_columns(parquet_path, [cols[ans] for ans in ans_d], [filt[ans] for ans in ans_d])
            else:
                print("Filtro não definido.")
                continue
            sorted_res = dict([[label, value] for label, value in sorted(w_filter.items(),
                                                                        key = lambda k: k[1],
                                                                        reverse=True)]) # Para ordenar o dicionário
            dump_path = Path(f"PNAD_data/{y}/Dump/{y}_{t}_{usr_ans}.txt")
            dump_path.parent.mkdir(exist_ok=True, parents=True)
            percents = []
            with open(dump_path, "w", encoding="UTF-8") as out:
                out.write(f"Total de respostas: {total_ans}\n\n")
                for label, val in sorted_res.items():
                    out.write(f"{label}: {val} ({(val/total_ans):%})\n")
                    percents.append(f"{(val/total_ans):2.2%}")
            # plt.figure(figsize=(8, 5))        # Plot com Matplotlib
            # plt.barh([str(i) for i in sorted_res.keys()], np.array(list(sorted_res.values())))
            # plt.title(title)
            # plt.show()
            fig = px.bar({"Divisões" : list(sorted_res.keys()), "Respostas": list(sorted_res.values())},
                          x="Respostas", y="Divisões", labels=False, title=title, orientation='h', text=percents) # Plot com Plotly
            fig.update_layout(font_size=(5+round((48*2)/len(w_filter))), margin={"b":120,"t":120,"r":80,"l":80}, title_x=0.5)
            fig.show()
            print("Escolha outro filtro, digite \"-\"  para mudar o ano/trimestre ou digite \"*\" para sair\n")