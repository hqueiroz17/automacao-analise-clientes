"""
Script de extração de dados de clientes (fictícios) via API do Mockaroo.
Busca duas tabelas — clientes e financeiro — e salva localmente como CSV.
"""

import requests
import pandas as pd

import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("MOCKAROO_API_KEY")

url_clientes = f"https://api.mockaroo.com/api/generate.csv?key={API_KEY}&schema=clientes&count=1000"
url_financeiro = f"https://api.mockaroo.com/api/generate.csv?key={API_KEY}&schema=financeiro&count=1000"

# Busca os dados de clientes
resposta_clientes = requests.get(url_clientes)
with open("clientes.csv", "w", encoding="utf-8") as arquivo:
    arquivo.write(resposta_clientes.text)
print("Salvo: clientes.csv")

# Busca os dados financeiros
resposta_financeiro = requests.get(url_financeiro)
with open("financeiro.csv", "w", encoding="utf-8") as arquivo:
    arquivo.write(resposta_financeiro.text)
print("Salvo: financeiro.csv")