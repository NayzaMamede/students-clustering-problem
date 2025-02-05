import pyomo.environ as pyo
import numpy as np
import time
import re
import tempfile
import os

def carregar_instancia(caminho_arquivo):
    with open(caminho_arquivo, 'r') as file:
        lines = file.readlines()

    m = int(lines[0].split()[1])
    n = int(lines[1].split()[1])
    p = int(lines[2].split()[1])

    distancias_inicio = lines.index('Distancias:\n') + 1
    distancias_fim = distancias_inicio + m
    distancias = np.loadtxt(lines[distancias_inicio:distancias_fim], dtype=float)
    
    demanda_inicio = lines.index('Demandas:\n') + 1
    demanda_fim = demanda_inicio + m
    demandas = np.loadtxt(lines[demanda_inicio:demanda_fim], dtype=int)

    capacidades_inicio = lines.index('Capacidades:\n') + 1
    capacidades_fim = capacidades_inicio + n
    capacidades = np.loadtxt(lines[capacidades_inicio:capacidades_fim], dtype=int)

    return {
        'm': m,
        'n': n,
        'p': p,
        'distancias': distancias,
        'demandas': demandas,
        'capacidades': capacidades
    }

# Função para salvar resultados em um arquivo .txt
def salvar_resultados(nome_instancia, tempo_execucao, funcao_objetivo, e_otima, vetor_alocacao, gap):
    with open(f'result_{nome_instancia}.txt', 'w') as f:
        f.write(f'Tempo(s): {tempo_execucao:.4f}\n')
        f.write(f'Funcao Objetivo: {funcao_objetivo}\n')
        f.write(f'Solucao Otima: {e_otima}\n')
        f.write(f'Vetor de Alocacao: {vetor_alocacao}\n')
        f.write(f'Gap: {gap}%\n')

# Número total de instâncias
num_total_instancias = 120

for num_instancia in range(61, num_total_instancias + 1):
    caminho_instancia = f'instancias\SCP_inst{num_instancia}.txt'
    instancia = carregar_instancia(caminho_instancia)

    m = instancia['m']
    n = instancia['n']
    p = instancia['p']
    distancias = instancia['distancias']
    demandas = instancia['demandas']
    capacidades = instancia['capacidades']

    # Criação do modelo
    modelo = pyo.ConcreteModel()

    # Conjuntos
    modelo.M = pyo.Set(initialize=range(m))
    modelo.N = pyo.Set(initialize=range(n))
    modelo.P = pyo.Set(initialize=range(p))

    # Parâmetros
    modelo.d = pyo.Param(modelo.M, modelo.N, initialize=lambda modelo, i, j: distancias[i][j])
    modelo.q = pyo.Param(modelo.M, modelo.P, initialize=lambda modelo, i, k: demandas[i][k])
    modelo.w = pyo.Param(modelo.N, modelo.P, initialize=lambda modelo, j, k: capacidades[j][k])
    modelo.f = pyo.Param(modelo.N, initialize=lambda modelo, j: 1000000)

    # Variáveis de decisão
    modelo.x = pyo.Var(modelo.M, modelo.N, within=pyo.Binary)
    modelo.y = pyo.Var(modelo.N, within=pyo.Binary)

    # Função Objetivo
    def funcao_objetivo(modelo):
        return sum(modelo.d[i, j] * modelo.x[i, j] for i in modelo.M for j in modelo.N) +\
               sum(modelo.f[j] * modelo.y[j] for j in modelo.N)

    modelo.objetivo = pyo.Objective(rule=funcao_objetivo, sense=pyo.minimize)

    # Restrições
    def alocar(modelo, i):
        return sum(modelo.x[i, j] for j in modelo.N) == 1

    modelo.alocar = pyo.Constraint(modelo.M, rule=alocar)

    def capacidade(modelo, j, k):
        return sum(modelo.q[i, k] * modelo.x[i, j] for i in modelo.M) <= modelo.w[j, k] * modelo.y[j]

    modelo.capacidade = pyo.Constraint(modelo.N, modelo.P, rule=capacidade)

    def escolas_usadas(modelo, i, j):
        return modelo.x[i, j] <= modelo.y[j]

    modelo.escolas_usadas = pyo.Constraint(modelo.M, modelo.N, rule=escolas_usadas)

    # Solver
    solver = pyo.SolverFactory('cplex')
    solver.options['timelimit'] = 300
    solver.options['threads'] = 1
    # Criar um arquivo temporário para armazenar o log
    with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.log') as log_file:
        log_file_name = log_file.name

    inicio_tempo = time.time()
    result = solver.solve(modelo, tee=True, logfile=log_file_name)
    fim_tempo = time.time()
    tempo_execucao = fim_tempo - inicio_tempo

    # Ler o conteúdo do arquivo de log após a execução do solver
    with open(log_file_name, 'r') as log_file:
        log_conteudo = log_file.read()

    # Analisar o log do solver para encontrar o gap percentual
    match = re.search(r'Current MIP best bound = .+ \(gap = .+, (\d+\.\d+)%\)', log_conteudo)
    gap_percentual = float(match.group(1)) if match else None

    # Verificar se a solução é ótima
    e_otima = result.solver.termination_condition == pyo.TerminationCondition.optimal

    # Capturar o valor da função objetivo
    funcao_objetivo_valor = pyo.value(modelo.objetivo)

    # Capturar o vetor de alocação
    vetor_alocacao = [j for i in modelo.M for j in modelo.N if pyo.value(modelo.x[i, j]) == 1]

    # Salvar os resultados no arquivo
    salvar_resultados(num_instancia, tempo_execucao, funcao_objetivo_valor, e_otima, vetor_alocacao, gap_percentual)

    # Imprimir na tela o gap percentual
    if gap_percentual is not None:
        print(f'Instância {num_instancia} - Gap percentual: {gap_percentual:.4f}%')
    else:
        print(f'Instância {num_instancia} - Gap não encontrado no log.')

    # Remover o arquivo de log temporário
    try:
        os.remove(log_file_name)
    except PermissionError as e:
        print(f"Erro ao remover o arquivo de log: {e}")