import pyomo.environ as pyo
import numpy as np
import time
import re
import tempfile
import os


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
   
