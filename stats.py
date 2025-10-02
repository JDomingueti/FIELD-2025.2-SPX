from pathlib import Path
import pandas as pd
import plotly.express as px
from to_parquet import make_data_paths
import sys

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
    "09" : "Ensino Científico",            # ( Antigo científico, clássico, etc. - médio 2º ciclo )
    "10" : "Regular do 2º grau",
    "11" : "Supletivo do 2º grau",
    "12" : "Superior",
    "13" : "Nível superior",
    "14" : "Mestrado",
    "15" : "Doutorado",
    0: "sem resposta"
}

rac = {
    "1": "Branca",
    "2": "Preta",
    "3": "Amarela",
    "4": "Parda",
    "5": "Indígena",
    "9": "Ignorado",
    0: "Sem resposta"
}

sex = {
    "1": "Homem",
    "2": "Mulher",
    0: "Sem resposta"
}

cols = {
    "1": "UF",
    "2": "UF",
    "3": "V2007", #Sexo
    "4": "V2010", #Cor ou raca
    "5": "V3009A", #Curso mais elevado que frequentou
    "6": "V2009", # Idade na data de referencia
    "7": "VD4019", # Rend.  habitual qq trabalho
    "8": "VD4016", #  Rend. habitual. trab. princ.
    '9': 'VD4017' # Rend. efetivo trab. princic.
    }

filt = {
    "1": reg,
    "2": est,
    "3": sex,
    "4": rac,
    "5": esc,
    "6": None,
    "7": None,
    "8": None,
    '9': None
}

titles = {
   "1": "Respostas por Região",
   "2": "Respostas por Estados",
   "3": "Respostas por Sexo",
   "4": "Respostas por Raça",
   "5": "Respostas por Escolarização",
   "6": "Respostas por Idade",
   "7": "Respostas por Renda Habitual Total",
   "8": "Respostas por Renda Habitual Principal",
   '9': 'Respostas por Renda Efetiva Principal'
}

income_bins_map = {
    "1": "Até R&#36;1.518",
    "2": "R&#36;1.519-R&#36;3.036",
    "3": "R&#36;3.037-R&#36;6.072",
    "4": "R&#36;6.073-R&#36;12.144",
    "5": "R&#36;12.145-R&#36;24.288",
    "6": "R&#36;24.289-R&#36;48.576",
    "7": "R&#36;48.577+",
    "0": "Não aplicável"
}

def age_bin(age:str):
    """
    Dada uma string representando a  idade, retorna uma string do intervalo
    que a idade se encontra.

    Parameters:
        age (str): Idade
    
    Returns:
        Retorna uma string com o intervalo que a idade se encontra
    """
    if age in [0, "0"]: return "Sem Resposta"
    age = int(age)
    if age < 18: return "0-17"
    elif age < 30: return "18-29"
    elif age < 45: return "30-44"
    elif age < 60: return "45-59"
    elif age < 90: return "61-89"
    else: return "90+"

def income_bin(income: str, minimum_income=1518):
    """
    Dada uma string representando a renda, e uma string representando o salario minimo,
    retorna uma string do intervalorque a renda se encontra.

    Parameters: 
        income (str): Renda

    Returns:
        Retorna uma string com o intervalo que a renda se encontra
    """
    if income in [None, 0, "0"]: return "Não aplicável"
    income = int(income)
    if income <=  minimum_income: return "Até R&#36;1.518"
    elif income <= 2 * minimum_income: return "R&#36;1.519-R&#36;3.036" 
    elif income <= 4 * minimum_income: return "R&#36;3.037-R&#36;6.072"
    elif income <= 8 * minimum_income: return "R&#36;6.073-R&#36;12.144"
    elif income <= 16 * minimum_income: return "R&#36;12.145-R&#36;24.288"
    elif income <= 32 * minimum_income: return "R&#36;24.289-R&#36;48.576"
    else: return "R&#36;48.577+"

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
    total_lines = len(parq)         # Número de linhas analisadas
    parq.fillna(0, inplace=True)    # Substitui NA por 0 para facilitar agrupamento
    pd_dict = parq.to_dict()        # Transforma em dict para facilitar a análise dos valores
    res = {}                        # Dicionário de saída
    k_filter = []                   # Lista com as labels já adicionadas à ´res´
    # Caso so uma coluna
    if (len(col_names) == 1):
        col = col_names[0]
        for val in list(pd_dict[col].values()):
            if filters[0] is None:
                if col == "V2009": # Idade
                    key = age_bin(val)
                elif col in ["VD4019", "VD4016", 'VD4017']: # Renda
                    key = income_bin(val)
                else:
                    key = str(val)
            else:
                key = filters[0][val] # Pega no filtro a chave ao qual o valor da linha atual corresponde

            if key in k_filter:
                res[key] += 1
            else:
                res[key] = 1
                k_filter.append(key)

    # Caso mais de uma coluna
    else:
        for t in zip(*(pair.values() for pair in list(pd_dict.values()))):
            new_keys = []
            for i, v in enumerate(t):
                if filters[i] is None:
                    if col_names[i] == "V2009": # idade
                        new_keys.append(age_bin(v))
                    elif col_names[i] in ["VD4019", "VD4016", 'VD4017']: #renda
                        new_keys.append(income_bin(v))
                    else:
                        new_keys.append(str(v))
                else:
                    new_keys.append(filters[i][v]) # Pega no filtro correspondente à coluna a chave ao qual o valor da linha atual corresponde
            n_key = '/'.join(new_keys)

            if n_key in k_filter:       # Caso o valor já tenha sido adicionado à saída soma 1 ao seu valor
                res[n_key] += 1
            else:                       # Caso o valor não tenha sido adicionado à saída o adiciona com valor 1
                res[n_key] = 1
                k_filter.append(n_key) 

    return res, total_lines

def group_columns_weighted(path: str, col_names: list[str], filters: list[dict]):
    """
    Igual a group_columns, mas usa V1028 como peso amostral.
    """
    # Comentários mais detalhados em group_columns

    parq = pd.read_parquet(path, columns=col_names + ["V1028"])
    parq.fillna({'V1028': 0}, inplace=True)
    total_weight = parq["V1028"].sum()
    parq.fillna(0, inplace=True)

    res = {}
    k_filter = []

    if len(col_names) == 1:
        col = col_names[0]
        for val, peso in zip(parq[col], parq["V1028"]):
            if filters[0] is None:
                if col == "V2009":  # idade
                    key = age_bin(val)
                elif col in ["VD4019", "VD4016", "VD4017"]:  # renda
                    key = income_bin(val)
                else:
                    key = str(val)
            else:
                key = filters[0].get(val, "Outro")

            res[key] = res.get(key, 0) + peso
            if key not in k_filter:
                k_filter.append(key)

    else:
        for *vals, peso in zip(*(parq[c] for c in col_names), parq["V1028"]):
            new_keys = []
            for i, v in enumerate(vals):
                if filters[i] is None:
                    if col_names[i] == "V2009":
                        new_keys.append(age_bin(v))
                    elif col_names[i] in ["VD4019", "VD4016", "VD4017"]:
                        new_keys.append(income_bin(v))
                    else:
                        new_keys.append(str(v))
                else:
                    new_keys.append(filters[i].get(v, "Outro"))

            n_key = "/".join(new_keys)
            res[n_key] = res.get(n_key, 0) + peso
            if n_key not in k_filter:
                k_filter.append(n_key)

    return res, total_weight

def group_columns_income(path:str, col_name:str, filter_dict: dict, income_col: str, income_range: str ):
    """
    """
    parq = pd.read_parquet(path, columns=[col_name, income_col])
    parq.fillna(0, inplace=True)
    
    income_col_mapped = parq[income_col].apply(income_bin)
    parq_filtered = parq[income_col_mapped == income_range]

    res = {}
    k_filter = []
    
    total_lines = len(parq_filtered)
    
    col_vals = parq_filtered[col_name]
    for val in col_vals:
        if filter_dict is None:
            if col_name == "V2009":
                key = age_bin(val)
            elif col_name in ["VD4019", "VD4016", 'VD4017']:
                key = income_bin(val)
            else:
                key = str(val)
        else:
            key = filter_dict.get(val, "Outro")

        res[key] = res.get(key, 0) + 1
        if key not in k_filter:
            k_filter.append(key)
            
    return res, total_lines

def group_columns_weighted_income(path: str, col_name: str, filter_dict: dict, income_col: str, income_range: str):
    """
    """
    parq = pd.read_parquet(path, columns=[col_name, income_col, "V1028"])
    parq.fillna({'V1028': 0}, inplace=True)
    parq.fillna(0, inplace=True)
    
    income_col_mapped = parq[income_col].apply(income_bin)
    parq_filtered = parq[income_col_mapped == income_range]

    res = {}
    k_filter = []
    
    total_weight = parq_filtered["V1028"].sum()

    for val, peso in zip(parq_filtered[col_name], parq_filtered["V1028"]):
        if filter_dict is None:
            if col_name == "V2009":
                key = age_bin(val)
            elif col_name in ["VD4019", "VD4016", 'VD4017']:
                key = income_bin(val)
            else:
                key = str(val)
        else:
            key = filter_dict.get(val, "Outro")

        res[key] = res.get(key, 0) + peso
        if key not in k_filter:
            k_filter.append(key)
    
    return res, total_weight

if __name__ == '__main__':
    args = sys.argv                                                     # Verifica se algum dos argumentos principais
    y = args[1] if (len(args) >= 2) else "0"                            # foi passado pela linha de comando e se foi
    t = args[2] if (len(args) >= 3) else "0"                            # utiliza-os ao menos na primeira iteração.
    uw = (args[3] == 's') if (len(args) >= 4) else "0"                  # Pode-se passar nenhum, 1, 2 ou 3.
    run0 = True                                                         # Variável para ser possível alterar o ano em uma mesma execução
    filts = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]               # Possíveis valores para filtros
    income_filts = ['7', '8', '9']
    while (run0):
        run1 = True                                                     # Variável para alterar apenas o filtro na mesma execução
        if y == "0":                                                    # Caso o ano não seja passado pelo terminal
            y = input("Ano dos microdados:")
        if (y == "*"):                                                  # Caractere que sai do programa
            run0 = False
            break
        elif y not in ["2020", "2021", "2022", "2023", "2024", "2025"]: # Anos que podem ser escolhidos
            continue
        if t == "0":                                                    # Caso o trimestre não seja passado pelo terminal
            t = input("Trimestre desejado:")
        if (t == "*"):                                                  # Caractere que sai do programa
            run0 = False
            break
        elif (t not in ['1', '2', '3', '4']):                           # Caso o trimestre selecionado não tenha sido pré-definido reinicia o loop
            continue
        _, parquet_path = make_data_paths(y, t)
        # aplicar pesos amostrais
        use_weights = (input("Aplicar pesos ? [s/n]: ").lower() == 's') if (uw == '0') else uw
        weight_txt = " (com pesos amostrais)" if use_weights else ""

        print("Inputs: \n -> \"*\" : Finalizar execução\n -> \"-\" : Mudar ano/trimestre")
        print(" -> \"1\" : Filtrar por região \n -> \"2\" : Filtrar por estado\n -> \"3\" : Filtrar",
            "por sexo\n -> \"4\" : Filtrar por raça\n -> \"5\" : Filtrar por escolaridade\n -> \"6\" : Filtrar por idade\n",
            "-> \"7\" : Filtrar por renda habitual total\n -> \"8\" : Filtrar por renda habitual principal\n",
            " -> \"9\" : Filtrar por renda efetiva principal\n -> \'10\' : Dois Filtros\n -> \'11\' : Dois Filtros com Faixa de renda")
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
                base_title = titles[usr_ans] 
                title = f'{base_title} - {y} - T{t}{weight_txt}' #titulo personalizado
                if use_weights:
                    w_filter, total_ans = group_columns_weighted(parquet_path, [cols[usr_ans]], [filt[usr_ans]])
                else:
                    w_filter, total_ans = group_columns(parquet_path, [cols[usr_ans]], [filt[usr_ans]])
            elif (usr_ans == "10"):
                print(" -> Digite o número dos dois filtros\n -> Opções: 1; 3; 4; 5; 6; 7; 8; 9 <-\n")
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
                base_title = f'{titles[ans_d[0]]} + {titles[ans_d[1]]}' # titulo duplo
                title = f'{base_title} - {y} - T{t}{weight_txt}'
                if use_weights:
                    w_filter, total_ans = group_columns_weighted(parquet_path, [cols[ans] for ans in ans_d], [filt[ans] for ans in ans_d])
                else:
                    w_filter, total_ans = group_columns(parquet_path, [cols[ans] for ans in ans_d], [filt[ans] for ans in ans_d])
            elif (usr_ans == "11"):
                print(" -> Digite o número dos dois filtros (um deve ser de renda)\n -> Opções: 1; 3; 4; 5; 6 junto com 7; 8; 9 <-\n")
                ans_d = [input(" -> Filtro de Renda : "), input(" -> Segundo Filtro : ")]
                
                income_ans = ans_d[0] if ans_d[0] in income_filts else ans_d[1]
                second_ans = ans_d[1] if ans_d[0] in income_filts else ans_d[0]

                if not (income_ans in income_filts and second_ans in filts and second_ans not in income_filts and second_ans != "2"):
                    print(" -> Combinação de filtros inválida. Escolha um filtro de renda (7, 8 ou 9) e outro filtro (1, 3, 4, 5, 6).\n")
                    continue
                
                print("Escolha a faixa de renda:")
                for key, val in income_bins_map.items():
                    print(f" -> '{key}' : {val}")
                income_range_choice = input(" -> Faixa de Renda: ")
                if income_range_choice not in income_bins_map:
                    print("Faixa de renda inválida.")
                    continue
                
                income_range_str = income_bins_map[income_range_choice]
                
                base_title = f'{titles[second_ans]} dentro da faixa de Renda: {income_range_str}'
                title = f'{base_title} - {y} - T{t}{weight_txt}'
                
                if use_weights:
                    w_filter, total_ans = group_columns_weighted_income(parquet_path, cols[second_ans], filt[second_ans], cols[income_ans], income_range_str)
                else:
                    w_filter, total_ans = group_columns_income(parquet_path, cols[second_ans], filt[second_ans], cols[income_ans], income_range_str)
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

            fig = px.bar({"Divisões" : list(sorted_res.keys()), "Respostas": list(sorted_res.values())},
                         x="Respostas", y="Divisões", labels=False, title=title, orientation='h', text=percents)
            fig.update_layout(font_size=(5+round((48*2)/len(w_filter))), margin={"b":120,"t":120,"r":80,"l":220}, title_x=0.5)
            fig.show()
            print("Escolha outro filtro, digite \"-\"  para mudar o ano/trimestre ou digite \"*\" para sair\n")
        y = "0"
        t = "0"
        uw = "0"