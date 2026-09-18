"""
Carrega os dados extraídos (clientes e financeiro) do CSV para o SQL Server.
"""

import os
import pandas as pd
import pyodbc
from dotenv import load_dotenv

load_dotenv()
senha = os.getenv("SQL_SERVER_SENHA")

# Monta a string de conexão com o SQL Server
conexao = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=PC;"
    "DATABASE=analise_clientes;"
    "UID=sa;"
    f"PWD={senha}"
)

print("Conectado ao SQL Server com sucesso!")

# Lê os CSVs extraídos
clientes = pd.read_csv("clientes.csv")
financeiro = pd.read_csv("financeiro.csv")

cursor = conexao.cursor()

# Cria a tabela clientes (se não existir) e insere os dados
cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='clientes' AND xtype='U')
    CREATE TABLE clientes (
        cliente_id INT PRIMARY KEY,
        nome VARCHAR(100),
        idade INT,
        cidade VARCHAR(100),
        estado VARCHAR(50)
    )
""")
conexao.commit()   

cursor.execute("SELECT COUNT(*) FROM clientes")
if cursor.fetchone()[0] == 0:
    for _, linha in clientes.iterrows():
        cursor.execute(
            "INSERT INTO clientes (cliente_id, nome, idade, cidade, estado) VALUES (?, ?, ?, ?, ?)",
            int(linha["cliente_id"]), str(linha["nome"]), int(linha["idade"]),
            str(linha["cidade"]), str(linha["estado"])
        )
    conexao.commit()
    print(f"{len(clientes)} registros inseridos em 'clientes'")
else:
    print("Tabela 'clientes' já possui dados, inserção ignorada")
#Os ? são "placeholders", substitui cada um pelos valores que vêm depois, na mesma ordem. Isso é mais seguro do que colar os valores direto no texto do SQL (evita um problema clássico de segurança chamado "SQL injection")

#Cria a tabela financeiro (se não existir) e insere os dados
cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='financeiro' AND xtype='U')
    CREATE TABLE financeiro (
        cliente_id INT PRIMARY KEY,
        renda_mensal FLOAT,
        divida_total FLOAT,
        qtd_atrasos_12m INT,
        limite_credito_atual FLOAT
    )
""")
conexao.commit()

cursor.execute("SELECT COUNT(*) FROM financeiro")
if cursor.fetchone()[0] == 0:
    for _, linha in financeiro.iterrows():
        cursor.execute(
            "INSERT INTO financeiro (cliente_id, renda_mensal, divida_total, qtd_atrasos_12m, limite_credito_atual) VALUES (?, ?, ?, ?, ?)",
            int(linha["cliente_id"]), float(linha["renda_mensal"]), float(linha["divida_total"]),
            int(linha["qtd_atrasos_12m"]), float(linha["limite_credito_atual"])
        )
    conexao.commit()
    print(f"{len(financeiro)} registros inseridos em 'financeiro'")
else:
    print("Tabela 'financeiro' já possui dados, inserção ignorada")
