"""
Análise de risco de crédito: consulta o SQL Server,
calcula o score de risco em Python, e classifica os clientes em faixas.
"""

import os
import pandas as pd
import pyodbc
from dotenv import load_dotenv

load_dotenv()
senha = os.getenv("SQL_SERVER_SENHA")

conexao = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=PC;"
    "DATABASE=analise_clientes;"
    "UID=sa;"
    f"PWD={senha}"
)

consulta = """
    SELECT
        c.cliente_id,
        c.nome,
        c.idade,
        c.estado,
        f.renda_mensal,
        f.divida_total,
        f.qtd_atrasos_12m,
        f.limite_credito_atual,
        RANK() OVER (ORDER BY (CAST(f.divida_total AS FLOAT) / f.renda_mensal) DESC) AS posicao_risco
    FROM clientes c
    INNER JOIN financeiro f ON c.cliente_id = f.cliente_id
"""

df = pd.read_sql(consulta, conexao)
print(df.shape)
print(df.head())

def calcular_score(divida_total, renda_mensal, qtd_atrasos, limite_credito):
    """
    Calcula um score de risco (0 a 100, onde 100 = risco máximo),
    combinando três fatores: relação dívida/renda, atrasos e uso do limite.
    """

    # Quanto o cliente deve, comparado com quanto ele ganha por mês
    razao_divida_renda = divida_total / renda_mensal

    # Quanto do limite de crédito disponível o cliente já está usando
    # (proteção contra divisão por zero, caso o limite seja 0)
    uso_limite = divida_total / limite_credito if limite_credito > 0 else 1

    # Pesos calibrados por simulação (ver seção "Sobre o cálculo do score" no README)
    pontos_divida = min(razao_divida_renda * 2, 22)
    pontos_atraso = min(qtd_atrasos * 5, 20)
    pontos_uso_limite = min(uso_limite * 10, 22)

    score = pontos_divida + pontos_atraso + pontos_uso_limite
    return round(min(score, 100), 1)


def classificar_risco(score):
    """Classifica o score numérico em uma categoria de risco."""
    if score >= 55:
        return "Alto"
    elif score >= 28:
        return "Médio"
    else:
        return "Baixo"

    # Aplica a função calcular_score em cada linha do DataFrame, uma por uma,
# passando os 4 valores daquela linha como "ingredientes" da máquina
df["score"] = df.apply(
    lambda linha: calcular_score(
        linha["divida_total"],
        linha["renda_mensal"],
        linha["qtd_atrasos_12m"],
        linha["limite_credito_atual"]
    ),
    axis=1 #linha por linha
)

# Agora que já temos o score de cada cliente, aplica a segunda função
# para transformar o número em uma categoria (Alto/Médio/Baixo)
df["classificacao_risco"] = df["score"].apply(classificar_risco)

print(df[["nome", "score", "classificacao_risco"]].head(10))
print(df["classificacao_risco"].value_counts())

# Cria faixas de idade, agrupando valores contínuos em categorias
df["faixa_idade"] = pd.cut(
    df["idade"],
    bins=[0, 25, 35, 50, 120],
    labels=["18-25", "26-35", "36-50", "51+"]
)

# Cria faixas de renda
df["faixa_renda"] = pd.cut(
    df["renda_mensal"],
    bins=[0, 3000, 7000, 15000],
    labels=["Até 3k", "3k-7k", "7k-15k"]
)

print(df[["nome", "idade", "faixa_idade", "renda_mensal", "faixa_renda"]].head())

# Agrupa por faixa de idade e conta quantos clientes existem em cada classificação de risco
resumo_idade = df.groupby(["faixa_idade", "classificacao_risco"], observed=True).size().unstack(fill_value=0)
print("Risco por faixa de idade:")
print(resumo_idade)

# Mesmo agrupamento, mas por faixa de renda
resumo_renda = df.groupby(["faixa_renda", "classificacao_risco"], observed=True).size().unstack(fill_value=0)
print("\nRisco por faixa de renda:")
print(resumo_renda)

df["uso_limite_pct"] = (df["divida_total"] / df["limite_credito_atual"]) * 100

resumo_uso_limite = df.groupby("classificacao_risco", observed=True)["uso_limite_pct"].mean().round(1)
print("Uso médio do limite de crédito, por faixa de risco:")
print(resumo_uso_limite)

# Calcula, para cada cliente, o percentual do limite de crédito que já está
# sendo usado pela dívida atual. Multiplicamos por 100 para ficar em formato
# de porcentagem (ex: 0.8 vira 80.0)
df["uso_limite_pct"] = (df["divida_total"] / df["limite_credito_atual"]) * 100

# Agrupa os clientes pela classificação de risco (Alto/Médio/Baixo) e calcula
# a média do uso do limite dentro de cada grupo — ou seja, "em média, quanto
# do limite os clientes de risco Alto estão usando, comparado com Baixo?"
# .round(1) arredonda o resultado para 1 casa decimal, só para ficar mais legível
resumo_uso_limite = df.groupby("classificacao_risco", observed=True)["uso_limite_pct"].mean().round(1)

print("Uso médio do limite de crédito, por faixa de risco:")
print(resumo_uso_limite)

top_risco = df.nlargest(10, "score")[["nome", "idade", "estado", "renda_mensal", "score", "classificacao_risco"]]
print("\nTop 10 clientes de maior risco:")
print(top_risco)

# Organiza um resumo geral, reunindo os principais números em um só lugar.
# Isso vai facilitar a geração do relatório HTML depois, já que teremos
# tudo pronto para "encaixar" no template.
resumo_geral = {

    # Quantos clientes existem no total 
    "total_clientes": len(df),

    # Média de renda mensal de todos os clientes, arredondada para 2 casas decimais
    "renda_media": round(df["renda_mensal"].mean(), 2),

    # Quantos clientes existem em cada classificação de risco
    # (Alto, Médio, Baixo), transformado em dicionário simples
    "contagem_risco": df["classificacao_risco"].value_counts().to_dict(),

    "uso_limite_por_risco": resumo_uso_limite.to_dict(),

    # Distribuição de risco (Alto/Médio/Baixo) dentro de cada idade e renda.
    "risco_por_idade": resumo_idade.to_dict(orient="index"),
    "risco_por_renda": resumo_renda.to_dict(orient="index"),

    # Os 10 clientes de maior risco
    "top_10_risco": top_risco.to_dict(orient="records")
}

print(resumo_geral)