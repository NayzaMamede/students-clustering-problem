import numpy as np
import random
import time
from itertools import combinations

#### GERAR SOLUÇÃO INICIAL #######

def contar_alunos_por_serie(demandas):
    # Soma a quantidade de alunos em cada série
    alunos_por_serie = np.sum(demandas, axis=0)
    return alunos_por_serie

def selecionar_escolas(n, p_series, capacidades_escolas, alunos_por_serie):
    escolas_selecionadas = []
    capacidade_acumulada = np.zeros(p_series)  # Capacidade acumulada por série
        
    escolas = list(range(n))
    random.shuffle(escolas)

    for escola in escolas:
        escolas_selecionadas.append(escola)
        capacidade_acumulada += capacidades_escolas[escola]
        if all(capacidade_acumulada >= alunos_por_serie):
            break

    return escolas_selecionadas


def calcular_capacidade_total(p_series, escolas_selecionadas, capacidades_escolas):

    capacidade_total = np.zeros(p_series)
    for escola in escolas_selecionadas:
        capacidade_total += capacidades_escolas[escola]
    return capacidade_total



def selecionar_escolas(n, p_series, capacidades_escolas, alunos_por_serie, alpha):
    escolas_selecionadas = []
    capacidade_acumulada = np.zeros(p_series)

    # Garantir que a capacidade original nunca seja modificada
    capacidades_escolas_copia = np.array(capacidades_escolas)  # Faz uma cópia da matriz de capacidades

    # Lista de escolas não selecionadas
    escolas_nao_selecionadas = list(range(n))

    while True:
        # Calcular a capacidade total das escolas não selecionadas
        capacidades_totais_nao_selecionadas = [sum(capacidades_escolas_copia[e]) for e in escolas_nao_selecionadas]

        if not capacidades_totais_nao_selecionadas:
            # Não há mais escolas para selecionar
            break

        # Encontrar a capacidade máxima e mínima entre as escolas não selecionadas
        max_capacidade = max(capacidades_totais_nao_selecionadas)
        min_capacidade = min(capacidades_totais_nao_selecionadas)

        # Calcular o limiar usando o parâmetro alpha
        limiar = min_capacidade + alpha * (max_capacidade - min_capacidade)

        # Criar a lista restrita de escolas com capacidade acima ou igual ao limiar
        escolas_rcl = [escola for escola in escolas_nao_selecionadas 
                       if sum(capacidades_escolas_copia[escola]) >= limiar]

        # Se a RCL estiver vazia, incluir todas as escolas não selecionadas
        if not escolas_rcl:
            escolas_rcl = escolas_nao_selecionadas[:]

        # Escolher uma escola aleatoriamente da lista restrita
        escola_escolhida = random.choice(escolas_rcl)
        escolas_selecionadas.append(escola_escolhida)
        capacidade_acumulada += capacidades_escolas_copia[escola_escolhida]
        escolas_nao_selecionadas.remove(escola_escolhida)

        # Verificar se a capacidade acumulada para cada série é suficiente
        if all(capacidade_acumulada >= alunos_por_serie):
            break
    return escolas_selecionadas


def alocar_alunos(m, distancias, demandas, capacidades_escolas, escolas_selecionadas, alpha):
    alocacao = [-1] * m
    capacidade_restante = {escola: capacidades_escolas[escola].copy() for escola in escolas_selecionadas}

    alunos = list(range(m))
    random.shuffle(alunos)

    for aluno_idx in alunos:
        serie_aluno = np.argmax(demandas[aluno_idx])
        
        # Criar uma lista de escolas aptas a alocação (com capacidade disponível)
        escolas_aptas = []
        distancias_escolas = []

        for escola in escolas_selecionadas:
            if capacidade_restante[escola][serie_aluno] > 0:
                escolas_aptas.append(escola)
                distancias_escolas.append(distancias[aluno_idx][escola])

        # Se houver escolas aptas
        if escolas_aptas:
            # Encontrar a menor e maior distância entre o aluno e as escolas aptas
            menor_distancia = min(distancias_escolas)
            maior_distancia = max(distancias_escolas)

            # Calcular o limiar
            limiar = menor_distancia + alpha * (maior_distancia - menor_distancia)

            # Criar a lista restrita de escolas com distância até o limiar
            lista_restrita = [escola for escola in escolas_aptas if distancias[aluno_idx][escola] <= limiar]

            # Escolher uma escola aleatoriamente da lista restrita
            escola_escolhida = random.choice(lista_restrita)

            # Alocar o aluno e atualizar a capacidade restante da escola escolhida
            alocacao[aluno_idx] = escola_escolhida
            capacidade_restante[escola_escolhida][serie_aluno] -= 1

    return alocacao


def executar(m, n, p_series, distancias, demandas, capacidades_escolas, alpha):
    
    alunos_por_serie = contar_alunos_por_serie(demandas)
    escolas_selecionadas = selecionar_escolas(n, p_series, capacidades_escolas, alunos_por_serie, alpha)
    alocacao = alocar_alunos(m, distancias, demandas, capacidades_escolas, escolas_selecionadas, alpha)
    
    return alocacao


##### CALCULAR FITNESS ###########

# Função para calcular o fitness de uma solução
def fitness(individuo, distancias, custo_escola):
    total_distancia = 0
    escolas_utilizadas = set()

    for aluno, escola in enumerate(individuo):
        distancia = distancias[aluno, escola]
        total_distancia += distancia
        escolas_utilizadas.add(escola)
        
    # Calcular o custo fixo de instalação para cada escola utilizada
    custo_instalacao = custo_escola * len(escolas_utilizadas)

    # Calcular o fitness (custo total)
    fitness = total_distancia + custo_instalacao
    return fitness

##### BUSCA LOCAL ######

def contar_alunos_por_serie(demandas):
    # Soma a quantidade de alunos em cada série
    alunos_por_serie = np.sum(demandas, axis=0)
    return alunos_por_serie

def alocar_aluno_proximidade(m, distancias, demandas, capacidades_escolas, escolas_selecionadas):
    #Aloca alunos na escola mais proxima a partir de um conjunto de escolas selecionadas
    alocacao = [-1] * m
    capacidade_restante = {escola: capacidades_escolas[escola].copy() for escola in escolas_selecionadas}

    # Escolha de alunos aleatoriamente
    alunos = list(range(m))
    np.random.shuffle(alunos)

    for aluno_idx in alunos:
        serie_aluno = np.argmax(demandas[aluno_idx])
        
        # Criar uma lista de escolas aptas a alocação (com capacidade disponível)
        escola_mais_proxima = None
        menor_distancia = float('inf')

        for escola in escolas_selecionadas:
            if capacidade_restante[escola][serie_aluno] > 0:
                distancia = distancias[aluno_idx][escola]
                if distancia < menor_distancia:
                    menor_distancia = distancia
                    escola_mais_proxima = escola

        # Se houver uma escola apta, alocar o aluno
        if escola_mais_proxima is not None:
            alocacao[aluno_idx] = escola_mais_proxima
            capacidade_restante[escola_mais_proxima][serie_aluno] -= 1

    return alocacao

def calcular_capacidade_total(p_series, escolas_selecionadas, capacidades_escolas):
    #Calcula a capacidade total disponivel por serie
    capacidade_total = np.zeros(p_series)
    for escola in escolas_selecionadas:
        capacidade_total += capacidades_escolas[escola]
    return capacidade_total

def desativar_escolas(m, n, p_series, distancias, demandas, capacidades_escolas, alocacao):
    #Função que tentar trocar duas escolas por uma

    # Vetor 1: somatório do número de alunos por série
    alunos_por_serie = contar_alunos_por_serie(demandas)
     
    escolas_selecionadas = list(set([escola for escola in alocacao if escola != -1]))
    
    # Inicializa a melhor solução
    melhor_alocacao = alocacao[:]
    melhor_escolas_selecionadas = escolas_selecionadas[:]
    
    while True:
        # Vetor 2: somatório da capacidade das escolas selecionadas por série
        capacidade_total = calcular_capacidade_total(p_series, melhor_escolas_selecionadas, capacidades_escolas)
        
        # Escolas não participantes (escolas que não estão em escolas_selecionadas)
        escolas_nao_participantes = list(set(range(n)) - set(melhor_escolas_selecionadas))

        encontrou_melhoria = False  # Sinalizador para saber se houve melhoria
        
        # Testar todas as combinações de duas escolas para remover
        for escolas_remover in combinations(melhor_escolas_selecionadas, 2):
            # Subtrair as capacidades das duas escolas escolhidas do vetor de capacidade total
            capacidade_total_removida = capacidade_total.copy()
            for escola in escolas_remover:
                capacidade_total_removida -= capacidades_escolas[escola]
            
            # Testar todas as escolas não participantes
            for escola_adicionar in escolas_nao_participantes:
                # Adicionar a capacidade da nova escola
                capacidade_total_atualizada = capacidade_total_removida + capacidades_escolas[escola_adicionar]

                # Verificar se a nova capacidade é suficiente
                if np.all(capacidade_total_atualizada >= alunos_por_serie):
                    # Se for suficiente, criar uma nova solução trocando as escolas
                    nova_escolas_selecionadas = melhor_escolas_selecionadas[:]
                    
                    for escola in escolas_remover:
                        nova_escolas_selecionadas.remove(escola)
                    
                    nova_escolas_selecionadas.append(escola_adicionar)

                    # Marcar os alunos das escolas removidas como não alocados (-1)
                    nova_alocacao = melhor_alocacao[:]
                    for aluno_idx in range(m):
                        if melhor_alocacao[aluno_idx] in escolas_remover:
                            nova_alocacao[aluno_idx] = -1

                    # Recalcular a alocação dos alunos
                    nova_alocacao = alocar_aluno_proximidade(m, distancias, demandas, capacidades_escolas, nova_escolas_selecionadas)
                    

                    # Atualizar a melhor solução encontrada até agora
                    melhor_alocacao = nova_alocacao[:]
                    melhor_escolas_selecionadas = nova_escolas_selecionadas[:]
                    encontrou_melhoria = True
                    break  # Saia para aplicar a nova solução

            if encontrou_melhoria:
                break  
        
        # Se nenhuma melhoria foi encontrada, interromper o processo
        if not encontrou_melhoria:
            break

    # Retornar a melhor solução encontrada
    return melhor_alocacao

def realocacao_alunos(m, distancias, demandas, alocacao_inicial, inicio, max_time):
     #Função que tenta trocar a alocação de dois alunos entre si
    
    # Inicializa o vetor de alocação atual e o fitness da solução inicial
    alocacao = alocacao_inicial[:]
    melhor_fitness = fitness(alocacao, distancias, 1000000)

    while True:
        # Verifica o tempo restante
        if time.time() - inicio >= max_time:
            
            return alocacao, melhor_fitness

        encontrou_melhoria = False
        alunos_testados = set()

        while len(alunos_testados) < m:
            # Verifica o tempo restante
            if time.time() - inicio >= max_time:
                return alocacao, melhor_fitness

            # Seleciona um aluno 'a' aleatoriamente que ainda não foi testado
            aluno_a = random.choice([i for i in range(m) if i not in alunos_testados])
            alunos_testados.add(aluno_a)

            serie_a = np.argmax(demandas[aluno_a])

            # Filtra os alunos da mesma série
            alunos_mesma_serie = [i for i in range(m) if np.argmax(demandas[i]) == serie_a and alocacao[i] != alocacao[aluno_a]]

            for aluno_b in alunos_mesma_serie:
                if time.time() - inicio >= max_time:
                    return alocacao, melhor_fitness

                escola_q = alocacao[aluno_a]
                escola_p = alocacao[aluno_b]

                #Expressao de Economia
                expressao = (distancias[aluno_a][escola_q] + distancias[aluno_b][escola_p]) - \
                                  (distancias[aluno_a][escola_p] + distancias[aluno_b][escola_q])

                if expressao > 0:
                    alocacao[aluno_a], alocacao[aluno_b] = escola_p, escola_q
                    novo_fitness = fitness(alocacao, distancias, 1000000)

                    if novo_fitness < melhor_fitness:
                        melhor_fitness = novo_fitness
                        encontrou_melhoria = True
                        break
                    else:
                        alocacao[aluno_a], alocacao[aluno_b] = escola_q, escola_p

                if encontrou_melhoria:
                    break

            if encontrou_melhoria:
                break

        if not encontrou_melhoria:
            break

    return alocacao, melhor_fitness


def realocar_aluno(m, distancias, demandas, capacidades_escolas, alocacao, inicio, max_time):
    
    #Função que tenta trocar a alocação de 1 aluno
    capacidades_atualizadas = np.copy(capacidades_escolas)
    for aluno_idx in range(m):
        escola_alocada = alocacao[aluno_idx]
        if escola_alocada != -1:
            serie_aluno = np.argmax(demandas[aluno_idx])
            capacidades_atualizadas[escola_alocada][serie_aluno] -= 1

    escolas_selecionadas = {escola for escola in alocacao if escola != -1}
    melhor_alocacao = alocacao[:]
    melhor_fitness = fitness(alocacao, distancias, 1000000)

    while True:
        if time.time() - inicio >= max_time:
           
            return melhor_alocacao, melhor_fitness

        encontrou_melhoria = False
        alunos_aleatorios = list(range(m))
        random.shuffle(alunos_aleatorios)

        for aluno_a in alunos_aleatorios:
            if time.time() - inicio >= max_time:
                
                return melhor_alocacao, melhor_fitness

            escola_p = alocacao[aluno_a]
            serie_aluno_a = np.argmax(demandas[aluno_a])

            escolas_com_capacidade = [
                escola for escola in escolas_selecionadas
                if capacidades_atualizadas[escola][serie_aluno_a] > 0 and escola != escola_p
            ]

            for escola_q in escolas_com_capacidade:
                if time.time() - inicio >= max_time:
                    return melhor_alocacao, melhor_fitness

                dap = distancias[aluno_a][escola_p] if escola_p != -1 else float('inf')
                daq = distancias[aluno_a][escola_q]
                #Expressao de Economia
                diferenca = dap - daq

                if diferenca > 0:
                    nova_alocacao = melhor_alocacao[:]
                    nova_alocacao[aluno_a] = escola_q

                    if escola_p != -1:
                        capacidades_atualizadas[escola_p][serie_aluno_a] += 1
                    capacidades_atualizadas[escola_q][serie_aluno_a] -= 1

                    novo_fitness = fitness(nova_alocacao, distancias, 1000000)

                    if novo_fitness < melhor_fitness:
                        melhor_alocacao = nova_alocacao
                        melhor_fitness = novo_fitness
                        encontrou_melhoria = True
                        break

                    if escola_p != -1:
                        capacidades_atualizadas[escola_p][serie_aluno_a] -= 1
                    capacidades_atualizadas[escola_q][serie_aluno_a] += 1

            if encontrou_melhoria:
                break

        if not encontrou_melhoria:
            break

    return melhor_alocacao, melhor_fitness


#### EXECUÇÃO DO ALGORITMO #####

def grasp_reativo(m, n, p_series, distancias, demandas, capacidades_escolas, max_time=300, update_interval=20):
    # Discretização de alpha
    alphas = np.linspace(0.1, 1.0, 10) 
    probabilidades = np.ones(len(alphas)) / len(alphas)  # Inicialmente, probabilidades iguais
    desempenho = np.zeros(len(alphas))  # Para acumular o desempenho (fitness) de cada alpha
    uso_alpha = np.zeros(len(alphas))  # Contador de quantas vezes cada alpha foi usado
    media_fitness = np.ones(len(alphas)) * float('inf')  # Média do fitness para cada alpha

    melhor_solucao = None
    melhor_fitness = float('inf')
    inicio = time.time()
    iteracao = 0

    while True:
        # Verifica se o tempo limite foi atingido
        if time.time() - inicio >= max_time:
            break

        # Escolha do alpha probabilisticamente
        indice_alpha = np.random.choice(range(len(alphas)), p=probabilidades)
        alpha = alphas[indice_alpha]
        uso_alpha[indice_alpha] += 1

        # Geração da solução inicial
        alocacao = executar(m, n, p_series, distancias, demandas, capacidades_escolas, alpha)

        # Primeiro movimento de melhoria
        nova_solucao = desativar_escolas(m, n, p_series, distancias, demandas, capacidades_escolas, alocacao)

        # Loop entre segundo e terceiro movimento de melhoria
        while True:
            # Segundo movimento de melhoria
            busca_local, fitness_local = realocacao_alunos(m, distancias, demandas, nova_solucao, inicio, max_time)

            # Terceiro movimento de melhoria
            nova_solucao, fitness_atualizado = realocar_aluno(m, distancias, demandas, capacidades_escolas, busca_local, inicio, max_time)

            if fitness_atualizado >= fitness_local:
                break  # Se não houver melhora, saia do loop

            fitness_local = fitness_atualizado

        if fitness_local < melhor_fitness:
            melhor_solucao = nova_solucao
            melhor_fitness = fitness_local

        # Atualiza a média do fitness para o alpha escolhido
        if uso_alpha[indice_alpha] > 1:
            media_fitness[indice_alpha] = (media_fitness[indice_alpha] * (uso_alpha[indice_alpha] - 1) + fitness_local) / uso_alpha[indice_alpha]
        else:
            media_fitness[indice_alpha] = fitness_local

        # Atualiza o desempenho do alpha escolhido
        desempenho[indice_alpha] = (fitness_local / media_fitness[indice_alpha])

        iteracao += 1
        # Atualiza as probabilidades a cada 'update_interval' iterações
        if iteracao % update_interval == 0:
            if desempenho.sum() > 0:
                probabilidades = desempenho / desempenho.sum()
            else:
                probabilidades = np.ones(len(alphas)) / len(alphas)

    return melhor_solucao, melhor_fitness

