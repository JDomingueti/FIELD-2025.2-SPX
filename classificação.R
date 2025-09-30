library(dplyr)
library(tidyr)
library(here)
library(arrow)
source("colunas_id.R")
# ================== AJUSTE DE IDADE ==================
ajustar_idade_estimativa <- function(idade) {
  if (is.na(idade)) return(NA_integer_)
  # se idade termina em 5 ou 0 permitir +-1 ano de toleracia
  if (idade %% 5 == 0) return(idade + sample(c(-1, 0, 1), 1))
  return(idade)
}

# ================== ESTIMAR ANO DE NASCIMENTO ==================
# Estima o ano de nascimento inicial com base na idade e ano do painel
estimar_ano_nascimento_inicial <- function(df, ano_inicio_painel) {
  # Assumindo que V2009 é a idade e que valores como 999 indicam idade ignorada
  df <- df %>%
    mutate(
      idade_ignorada = V2009 >= 999 | is.na(V2009),
      idade_corrigida = if_else(!idade_ignorada, ajustar_idade_estimativa(V2009), NA_real_),
      ano_nascimento = case_when(
        !is.na(V20082) & V20082 > 0 ~ as.numeric(V20082),       # usa direto o ano se disponivel
        !idade_ignorada ~ ano_inicio_painel - idade_corrigida,  # estima pelo ano + idade corrigida
        TRUE ~ NA_real_
      ),
      ano_nascimento_estimado_tmp = if_else(!idade_ignorada, ano_inicio_painel - idade_corrigida, NA_real_)
    )
  
  return(df)
}

# ================== IMPUTAÇÃO DE NASCIMENTO COM DOADORES ==================
# Imputa o ano de nascimento para registros ignorados usando doadores
imputar_ano_nascimento_doador <- function(df_domicilio) {
  doadoras <- df_domicilio %>% filter(!is.na(ano_nascimento))
  recebedoras_indices <- which(is.na(df_domicilio$ano_nascimento))
  
  if (length(recebedoras_indices) == 0 || nrow(doadoras) == 0){
    return(select(df_domicilio, -ano_nascimento_estimado_tmp)) #remove col temp
  }
  
  for (i in recebedoras_indices) {
    pessoa_alvo <- df_domicilio[i,]
    
    # criterios para encontrar doadoras potenciais conforme metodologia do IPEA
    doadoras_potenciais <- doadoras %>%
      filter(
        periodo != pessoa_alvo$periodo, # nao pode ser da mesma entrevista
        V2007 == pessoa_alvo$V2007, # deve ser do mesmo sexo
        # diferenca de ate 3 anos no ano estimado
        abs(ano_nascimento - pessoa_alvo$ano_nascimento_estimado_tmp) <=3
      )
    
    # verificar condicao no domicilio (grupos compativeis)
    if (nrow(doadoras_potenciais) > 0) {
      condicoes_compativeis <- list(
        c(1,2,3), #responsavel, conjuge, uniao estavel
        c(4,5,6), # filho, enteado
        c(8,9) # pai/mae, sogro/sogra
      )
      
      doadoras_filtradas <- doadoras_potenciais %>% 
        rowwise() %>%
        filter ({
          cond_alvo <- as.numeric(pessoa_alvo$V2005)
          cond_doadora <- as.numeric(V2005)
          
          # se a condicao for a mesma
          if (cond_alvo == cond_doadora)return(TRUE)
          
          # verifica se sao do mesmo grupo compativel
          pertencem_mesmo_grupo <- any(sapply(condicoes_compativeis, function(grupo) {
            cond_alvo %in% grupo && cond_doadora %in% grupo
          }))
          
          pertencem_mesmo_grupo
        }) %>%
        ungroup()
      
      # se houver doadoras apos os filtros
      if (nrow(doadoras_filtradas) > 0) {
        # ordena pela menor diff de ano e escolhe a melhor doadora
        melhor_doadora <- doadoras_filtradas %>%
          mutate(diff_ano = abs(ano_nascimento - pessoa_alvo$ano_nascimento_estimado_tmp)) %>%
          arrange(diff_ano) %>%
          slice(1)
        
        # ano de nascimento da mlehor doadora atribuido
        df_domicilio$ano_nascimento[i] <- melhor_doadora$ano_nascimento
      }
    }
    
  }
  # pessoa com data ignorada sem doadora permance NA
  return(select(df_domicilio, -ano_nascimento_estimado_tmp))
}

# Função para criar chaves de identificação
criar_chave_pessoa <- function(sexo, ano_nascimento, condicao, ordem) {
  paste(sexo, ano_nascimento, condicao, ordem, sep = "_")
}

# Função para verificar se duas pessoas são potencialmente a mesma
mesma_pessoa <- function(p1, p2, tolerancia_ano = 3) {
  # Critérios básicos: mesmo sexo
  if (as.character(p1$V2007) != as.character(p2$V2007)) return(FALSE)
  
  # se algum na, nao podemos comparar
  if (is.na(p1$ano_nascimento) || is.na(p2$ano_nascimento)) return(FALSE)
  
  # tolerancia no ano de nascimento
  diff_ano <- abs(p1$ano_nascimento - p2$ano_nascimento)
  if (diff_ano > tolerancia_ano) return(FALSE)
  
  # Converter condições para códigos numéricos para comparação
  cond1 <- as.numeric(p1$V2005)
  cond2 <- as.numeric(p2$V2005)
  
  # Mapear condições textuais para códigos
  #if (is.factor(cond1)) cond1 <- as.numeric(cond1)
  #if (is.factor(cond2)) cond2 <- as.numeric(cond2)
  
  # Verificar condições compatíveis no domicílio
  condicoes_compativeis <- list(
    c(1, 2, 3),  # responsável, cônjuge, união estável
    c(4, 5, 6),  # filho, enteado
    c(8, 9),      # pai/mãe, sogro/sogra
    c(7, 10:19) #conviventes e outros parentes
  )
  
  for (grupo in condicoes_compativeis) {
    if (cond1 %in% grupo && cond2 %in% grupo) {
      return(TRUE)
    }
  }
  
  # Se condições são exatamente iguais
  return(cond1 == cond2)
}

classificar_grupos_domesticos <- function(df_domicilio) {
  # Verificar se o dataframe está vazio ou não tem a coluna necessária
  if (nrow(df_domicilio) == 0 || !"periodo" %in% names(df_domicilio)) {
    return(data.frame(
      grupo_domestico_id = integer(0),
      n_grupos = integer(0),
      tipo_grupo = character(0)
    ))
  }
  
  periodos <- unique(df_domicilio$periodo)
  n_periodos <- length(periodos)
  
  if (n_periodos == 1) {
    return(data.frame(
      grupo_domestico_id = 1,
      n_grupos = 1,
      tipo_grupo = "único_periodo"
    ))
  }
  
  # Separar pessoas por período
  pessoas_por_periodo <- split(df_domicilio, df_domicilio$periodo)
  
  # Identificar pessoas que aparecem em múltiplos períodos
  grupos <- list()
  grupo_id <- 1
  periodos_atribuidos <- character(0)
  
  for (periodo_base in names(pessoas_por_periodo)) {
    if (periodo_base %in% periodos_atribuidos) next
    
    pessoas_base <- pessoas_por_periodo[[periodo_base]]
    grupo_atual <- list(periodo_base)
    
    # Procurar outros períodos com pessoas similares
    for (outro_periodo in names(pessoas_por_periodo)) {
      if (outro_periodo == periodo_base || outro_periodo %in% periodos_atribuidos) next
      
      pessoas_outro <- pessoas_por_periodo[[outro_periodo]]
      
      # Verificar se há pelo menos uma pessoa em comum
      tem_pessoa_comum <- FALSE
      for (i in 1:nrow(pessoas_base)) {
        for (j in 1:nrow(pessoas_outro)) {
          if (mesma_pessoa(pessoas_base[i,], pessoas_outro[j,])) {
            tem_pessoa_comum <- TRUE
            break
          }
        }
        if (tem_pessoa_comum) break
      }
      
      if (tem_pessoa_comum) {
        grupo_atual <- append(grupo_atual, outro_periodo)
      }
    }
    
    grupos[[grupo_id]] <- grupo_atual
    periodos_atribuidos <- c(periodos_atribuidos, unlist(grupo_atual))
    grupo_id <- grupo_id + 1
  }
  
  # Períodos não atribuídos formam grupos separados
  periodos_nao_atribuidos <- setdiff(names(pessoas_por_periodo), periodos_atribuidos)
  for (periodo in periodos_nao_atribuidos) {
    grupos[[grupo_id]] <- list(periodo)
    grupo_id <- grupo_id + 1
  }
  
  return(data.frame(
    grupo_domestico_id = seq_along(grupos),
    n_grupos = length(grupos),
    tipo_grupo = ifelse(length(grupos) == 1, "único", "múltiplos")
  ))
}

# ================== CLASSIFICAÇÃO DE INDIVÍDUOS ==================

classificar_individuos <- function(df_grupo) {
  df_grupo <- df_grupo %>% arrange(periodo)
  periodos <- unique(df_grupo$periodo)
  n_periodos <- length(periodos)
  
  if (n_periodos == 1) {
    df_vazio <- df_grupo[0, ]
    return(
      df_vazio %>% 
        mutate(
          individuo_id = integer(), 
          classe_individuo = integer()
        ) # dropar individuos com apenas uma entrevista
    )
  }
  
  # Agrupar pessoas por características similares
  df_grupo$individuo_id <- NA_real_
  df_grupo$classe_individuo <- NA_real_
  individuo_id <- 1
  
  # Verificar se o grupo tem tamanho constante
  tamanhos_por_periodo <- df_grupo %>%
    count(periodo, name = "n_pessoas")
  
  tamanho_constante <- length(unique(tamanhos_por_periodo$n_pessoas)) == 1
  
  pessoas_processadas <- logical(nrow(df_grupo))
  
  for (i in 1:nrow(df_grupo)) {
    if (pessoas_processadas[i]) next
    
    pessoa_base <- df_grupo[i,]
    indices_grupo <- i
    
    # Procurar pessoas similares nos outros períodos
    for (j in (i+1):nrow(df_grupo)) {
      if (j > nrow(df_grupo) || pessoas_processadas[j]) next
      if (df_grupo$periodo[j] == pessoa_base$periodo) next
      
      if (mesma_pessoa(pessoa_base, df_grupo[j,])) {
        indices_grupo <- c(indices_grupo, j)
      }
    }
    
    # Atribuir ID e classificar
    df_grupo$individuo_id[indices_grupo] <- individuo_id
    
    # Determinar classe baseada na metodologia do documento
    n_periodos_pessoa <- length(unique(df_grupo$periodo[indices_grupo]))
    
    if (tamanho_constante && n_periodos_pessoa == n_periodos) {
      # Verificar se características são idênticas
      pessoa_chars <- df_grupo[indices_grupo, c("V2007", "V2009", "V2005", "V2003")]
      if (nrow(unique(pessoa_chars)) == 1) {
        df_grupo$classe_individuo[indices_grupo] <- 1  # Classe 1
      } else {
        df_grupo$classe_individuo[indices_grupo] <- 2  # Classe 2
      }
    } else if (n_periodos_pessoa == n_periodos) {
      df_grupo$classe_individuo[indices_grupo] <- 3  # Classe 3
    } else {
      df_grupo$classe_individuo[indices_grupo] <- 4  # Classe 4 (inicial)
    }
    
    pessoas_processadas[indices_grupo] <- TRUE
    individuo_id <- individuo_id + 1
  }
  
  # Tratamento adicional para classes 4 (fragmentos potenciais)
  # Simplificado - na prática seria mais complexo conforme o documento
  individuos_classe4 <- df_grupo[df_grupo$classe_individuo == 4 & !is.na(df_grupo$classe_individuo),]
  if (nrow(individuos_classe4) > 1) {
    # Lógica simplificada para reclassificação
    df_grupo$classe_individuo[df_grupo$classe_individuo == 4] <- 5  # Reclassificar como classe 5
  }
  
  return(df_grupo)
}

# ================== FUNÇÃO PRINCIPAL ==================

classificar_painel_pnadc <- function(arquivo_pqt) {
  # Carregar dados
  cat("Carregando dados do arquivo:", arquivo_pqt, "\n")
  if (!file.exists(arquivo_pqt)) {
    stop("Arquivo não encontrado: ", arquivo_pqt)
  }
  
  #pessoas_long <- readRDS(arquivo_rds)
  pessoas_long <- read_parquet(arquivo_pqt)
  
  # Verificar estrutura dos dados
  colunas_necessarias <- c("domicilio_id", "V2003", "V2007", "V2009", "V2005", "periodo")
  colunas_faltando <- setdiff(colunas_necessarias, names(pessoas_long))
  
  if (length(colunas_faltando) > 0) {
    stop("Colunas faltando nos dados: ", paste(colunas_faltando, collapse = ", "))
  }
  
  if (nrow(pessoas_long) == 0) {
    stop("Dataset está vazio")
  }
  
  cat("Dados carregados:", nrow(pessoas_long), "registros de", 
      length(unique(pessoas_long$domicilio_id)), "domicílios\n")
  
  # filtrar apenas domicilios presentes em todos os 5 trimestres (esperado ~20%)
  domicilios_completos <- pessoas_long %>%
    count(domicilio_id, periodo) %>%
    count(domicilio_id, name = "n_periodos") %>%
    filter(n_periodos == 5) %>%
    pull(domicilio_id)
  
  pessoas_long <- pessoas_long %>%
    filter(domicilio_id %in% domicilios_completos)
  
  cat("Mantidos", length(unique(pessoas_long$domicilio_id)), 
      "domicílios completos em 5 entrevistas\n")
  
  # determinar o ano de inicio do painel a partir dos dados
  #ano_inicio_painel <- min(as.numeric(substr(pessoas_long$periodo, 1, 4)))
  ano_inicio_painel <- min(as.numeric(substr(pessoas_long$periodo, nchar(pessoas_long$periodo) - 3, nchar(pessoas_long$periodo))), na.rm = TRUE)
  cat("Ano de início do painel detectado:", ano_inicio_painel, "\n")
  
  # estimar o ano de nascimento inicial para todos
  cat("Estimando o ano de nascimento inicial...\n")
  pessoas_long <- estimar_ano_nascimento_inicial(pessoas_long, ano_inicio_painel)
  
  # imputar o ano de nascimento usando a logica de doadores por domicilio
  cat("Imputando anos de nascimento ignorados com base em doadores...\n")
  pessoas_long <- pessoas_long %>%
    group_by(domicilio_id) %>%
    group_modify(~imputar_ano_nascimento_doador(.x)) %>%
    ungroup()
  
  # Classificar grupos domésticos
  cat("Classificando grupos domésticos...\n")
  grupos_domesticos <- pessoas_long %>%
    group_by(domicilio_id) %>%
    do({
      df_domicilio <- .
      domicilio_atual <- unique(df_domicilio$domicilio_id)[1]
      resultado <- classificar_grupos_domesticos(df_domicilio)
      resultado$domicilio_id <- domicilio_atual
      resultado
    }) %>%
    ungroup()
  
  # Reorganizar colunas
  grupos_domesticos <- grupos_domesticos %>%
    select(domicilio_id, everything())
  
  # Juntar informação de grupos aos dados originais
  pessoas_com_grupos <- pessoas_long %>%
    left_join(grupos_domesticos, by = "domicilio_id")
  
  # Classificar indivíduos por grupo doméstico
  cat("Classificando indivíduos...\n")
  resultado_final <- pessoas_com_grupos %>%
    filter(n_grupos == 1) %>%  # Manter apenas domicílios com um grupo
    group_by(domicilio_id, grupo_domestico_id) %>%
    group_modify(~classificar_individuos(.x)) %>%
    ungroup() %>%
    
    # Criar ID Global
    mutate(ID_UNICO = paste(domicilio_id, grupo_domestico_id, individuo_id, sep = '-'))
  
  # Estatísticas resumo
  cat("\n=== RESULTADOS DA CLASSIFICAÇÃO ===\n")
  
  # Estatísticas de domicílios
  resumo_domicilios <- grupos_domesticos %>%
    count(n_grupos, name = "freq") %>%
    mutate(prop = round(freq / sum(freq) * 100, 2))
  
  cat("Distribuição de grupos domésticos por domicílio:\n")
  print(resumo_domicilios)
  
  # Estatísticas de indivíduos (apenas domicílios com 1 grupo)
  if (nrow(resultado_final) > 0) {
    resumo_individuos <- resultado_final %>%
      count(classe_individuo, name = "freq") %>%
      mutate(prop = round(freq / sum(freq) * 100, 2))
    
    cat("\nDistribuição de classes de indivíduos:\n")
    print(resumo_individuos)
    
    # Proporção de domicílios utilizáveis para painel
    domicilios_painel <- length(unique(resultado_final$domicilio_id))
    total_domicilios <- length(unique(pessoas_long$domicilio_id))
    
    cat(sprintf("\nDomicílios utilizáveis para análise em painel: %d de %d (%.2f%%)\n", 
                domicilios_painel, total_domicilios, 
                domicilios_painel/total_domicilios*100))
  }
  
  # Salvar resultados
  
  #arquivo_saida <- gsub("\\.rds$", "_classificado.rds", arquivo_rds)
  arquivo_saida <- gsub("\\.parquet$", "_classificado.parquet", arquivo_pqt)
  #saveRDS(resultado_final, arquivo_saida)
  write_parquet(resultado_final, arquivo_saida)
  cat("\nResultados salvos em:", arquivo_saida, "\n")
  
  # Salvar também resumo de grupos domésticos
  #arquivo_grupos <- gsub("\\.rds$", "_grupos_domesticos.rds", arquivo_rds)
  arquivo_grupos <- gsub("\\.parquet$", "_grupos_domesticos.parquet", arquivo_pqt)
  #saveRDS(grupos_domesticos, arquivo_grupos)
  write_parquet(grupos_domesticos, arquivo_grupos)
  cat("Classificação de grupos domésticos salva em:", arquivo_grupos, "\n")
  
  return(list(
    dados_classificados = resultado_final,
    grupos_domesticos = grupos_domesticos,
    resumo_domicilios = resumo_domicilios,
    resumo_individuos = if(nrow(resultado_final) > 0) resumo_individuos else NULL
  ))
}

#resultado <- classificar_painel_pnadc(paste0("pessoas_", 
#                                             periodos_analise$ano_inicio, periodos_analise$tri_inicio,
#                                             "_", periodos_analise$ano_fim, periodos_analise$tri_fim,
#                                             ".rds"))
resultado <- classificar_painel_pnadc(here(getwd(), "PNAD_data", "Pareamentos", paste0("pessoas_", 
                                                                                       periodos_analise$ano_inicio, periodos_analise$tri_inicio,
                                                                                       "_", periodos_analise$ano_fim, periodos_analise$tri_fim,
                                                                                       ".parquet")))

str(resultado$dados_classificados)
print(resultado$resumo_domicilios)
if(!is.null(resultado$resumo_individuos)) print(resultado$resumo_individuos)