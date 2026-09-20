"""
Gera o relatório HTML de análise de risco de crédito,
a partir dos resultados calculados em analise_risco.py.
"""

import json

# Converte valores numpy (np.float64, np.int64) para tipos Python puros,
# evitando problemas de formatação no HTML
def limpar_numero(valor):
    if hasattr(valor, "item"):
        return valor.item()
    return valor


def gerar_insight_faixa(nome_faixa, pct_risco_alto, media_geral_pct):
    """
    Gera um texto comparando a proporção de clientes de risco Alto em uma
    faixa específica com a média geral, de forma automática.
    """
    diferenca = pct_risco_alto - media_geral_pct

    if diferenca > 5:
        return f"{nome_faixa}: risco Alto {diferenca:.1f} pontos percentuais acima da média."
    elif diferenca < -5:
        return f"{nome_faixa}: risco Alto {abs(diferenca):.1f} pontos percentuais abaixo da média."
    else:
        return f"{nome_faixa}: risco Alto próximo da média."


def calcular_pct_risco_alto(contagem_faixa):
    """
    Recebe um dicionário tipo {'Alto': 10, 'Médio': 50, 'Baixo': 20}
    e devolve a porcentagem de clientes 'Alto' dentro desse grupo.
    """
    total_faixa = sum(contagem_faixa.values())
    qtd_alto = contagem_faixa.get("Alto", 0)
    return round((qtd_alto / total_faixa) * 100, 1) if total_faixa > 0 else 0

def definir_classe_barra(diferenca):
    """
    Decide se a barra deve ficar destacada (vermelha) ou neutra,
    usando a MESMA regra de 5 pontos que o texto do insight usa —
    garantindo que cor e texto sempre concordem entre si.
    """
    if diferenca > 5:
        return "acima"
    return ""

# Lê o resumo já calculado pelo script de análise
with open("resumo_analise.json", "r", encoding="utf-8") as arquivo:
    resumo = json.load(arquivo)

print(resumo.keys())

media_geral_risco_alto = calcular_pct_risco_alto(resumo["contagem_risco"])

faixas_idade_processadas = []
for faixa, contagem in resumo["risco_por_idade"].items():
    pct = calcular_pct_risco_alto(contagem)
    diferenca = round(pct - media_geral_risco_alto, 1)
    faixas_idade_processadas.append({
        "nome": faixa,
        "pct": pct,
        "classe_barra": definir_classe_barra(diferenca),
        "insight": gerar_insight_faixa(faixa, pct, media_geral_risco_alto)
    })

print(faixas_idade_processadas)

faixas_renda_processadas = []
for faixa, contagem in resumo["risco_por_renda"].items():
    pct = calcular_pct_risco_alto(contagem)
    diferenca = round(pct - media_geral_risco_alto, 1)
    faixas_renda_processadas.append({
        "nome": faixa,
        "pct": pct,
        "classe_barra": definir_classe_barra(diferenca),
        "insight": gerar_insight_faixa(faixa, pct, media_geral_risco_alto)
    })

print(faixas_renda_processadas)
