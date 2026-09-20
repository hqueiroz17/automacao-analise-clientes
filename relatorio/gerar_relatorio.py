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

def formatar_moeda(valor):
    """Formata um número no padrão brasileiro: R$ 8.228,30 (ponto no milhar, vírgula no decimal)."""
    texto = f"{valor:,.2f}"  # gera no padrão americano: 8,228.30
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return texto

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

# Limpa os valores numpy do uso de limite por risco
uso_limite_limpo = {chave: limpar_numero(valor) for chave, valor in resumo["uso_limite_por_risco"].items()}

# O top 10 já vem em formato de lista de dicionários, só precisamos limpar os números
top_10_limpo = []
for cliente in resumo["top_10_risco"]:
    top_10_limpo.append({chave: limpar_numero(valor) for chave, valor in cliente.items()})

print(uso_limite_limpo)
print(top_10_limpo[0])

def montar_barras_faixa(faixas, media_geral):
    """Monta o HTML das barras + insights para uma lista de faixas processadas.
    A linha de média fica DENTRO de cada bar-track, usando a mesma referência
    de porcentagem que a barra de preenchimento — isso garante alinhamento correto."""
    html_barras = ""
    for i, f in enumerate(faixas):
        classe = f["classe_barra"]
        linha_media = f'<div class="media-linha" style="left:{media_geral}%;"></div>'
        label_media = f'<div class="media-label" style="left:{media_geral}%;">{media_geral}%</div>' if i == 0 else ""
        html_barras += f'''
        <div class="bar-row">
          <div class="bar-label">{f["nome"]}</div>
          <div class="bar-track">
            {linha_media}
            {label_media}
            <div class="bar-fill {classe}" style="width:{f["pct"]}%;"></div>
          </div>
          <div class="bar-value">{f["pct"]}%</div>
        </div>'''

    html_insights = ""
    for f in faixas:
        classe_insight = "" if f["classe_barra"] == "acima" else "neutro"
        html_insights += f'<div class="insight {classe_insight}">💡 {f["insight"]}</div>'

    return html_barras, html_insights


def montar_linha_top10(clientes):
    """Monta as linhas da tabela de top 10 clientes de maior risco."""
    linhas = ""
    for c in clientes:
        badge_classe = c["classificacao_risco"].lower().replace("é", "e")
        linhas += f'''
        <tr>
          <td>{c["nome"]}</td>
          <td>{c["idade"]}</td>
          <td>{c["estado"]}</td>
          <td>R$ {formatar_moeda(c["renda_mensal"])}</td>
          <td>{c["score"]}</td>
          <td><span class="badge {badge_classe}">{c["classificacao_risco"]}</span></td>
        </tr>'''
    return linhas

def montar_linha_media(media_geral):
    """Monta a linha vertical vermelha que marca a média geral no gráfico."""
    return f'<div class="media-linha" style="left: calc(70px + 10px + {media_geral}%);"><div class="media-label">{media_geral}%</div></div>'

barras_idade, insights_idade = montar_barras_faixa(faixas_idade_processadas, media_geral_risco_alto)
barras_renda, insights_renda = montar_barras_faixa(faixas_renda_processadas, media_geral_risco_alto)
linhas_top10 = montar_linha_top10(top_10_limpo)

contagem = resumo["contagem_risco"]
total = resumo["total_clientes"]

html_final = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatório de Análise de Crédito</title>
<style>
  :root {{
    --bg: #0f1117; --card: #171a23; --border: #2a2e3a; --text: #e6e8ec;
    --muted: #9aa1b0; --baixo: #3ecf8e; --medio: #f5b942; --alto: #ef5b5b;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;
    background:var(--bg); color:var(--text); padding:32px 24px 60px; }}
  .wrap {{ max-width:980px; margin:0 auto; }}
  h1 {{ margin:0 0 6px; font-size:26px; }}
  .subtitle {{ color:var(--muted); font-size:14px; margin-bottom:24px; }}
  .cards {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:32px; }}
  .card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:16px; }}
  .card .label {{ font-size:12px; color:var(--muted); margin-bottom:6px; }}
  .card .value {{ font-size:24px; font-weight:700; }}
  section {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:20px; margin-bottom:24px; }}
  section h2 {{ margin:0 0 4px; font-size:16px; }}
  .desc {{ color:var(--muted); font-size:13px; margin-bottom:16px; }}
  .grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th, td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--border); }}
  th {{ color:var(--muted); font-size:12px; text-transform:uppercase; }}
  .badge {{ padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }}
  .badge.baixo {{ background:rgba(62,207,142,.15); color:var(--baixo); }}
  .badge.medio {{ background:rgba(245,185,66,.15); color:var(--medio); }}
  .badge.alto {{ background:rgba(239,91,91,.15); color:var(--alto); }}
  .chart {{ padding-top:22px; }}
  .bar-row {{ display:flex; align-items:center; gap:10px; margin-bottom:14px; }}
  .bar-label {{ width:70px; font-size:13px; color:var(--muted); }}
  .bar-track {{ flex:1; background:#0f1117; border-radius:6px; height:20px; border:1px solid var(--border); position:relative; }}
  .bar-fill {{ height:100%; border-radius:6px; background:var(--medio); position:relative; z-index:1; }}
  .bar-fill.acima {{ background:var(--alto); }}
  .bar-value {{ width:44px; text-align:right; font-size:12px; color:var(--muted); }}
  .media-linha {{ position:absolute; top:-4px; bottom:-4px; width:2px; background:var(--alto); z-index:2; }}
  .media-label {{ position:absolute; top:-20px; font-size:11px; color:var(--alto); white-space:nowrap; transform:translateX(-50%); }}
  .insight {{ margin-top:8px; padding:10px 14px; background:rgba(239,91,91,.08);
    border:1px solid rgba(239,91,91,.25); border-radius:8px; font-size:13px; }}
  .insight.neutro {{ background:rgba(154,161,176,.08); border-color:var(--border); color:var(--muted); }}
  .recomendacoes {{ margin-top:20px; padding-top:20px; border-top:1px dashed var(--border); }}
  .recomendacoes-header {{ display:flex; align-items:center; gap:8px; font-size:13px; font-weight:600; margin-bottom:4px; }}
  .recomendacoes-disclaimer {{ font-size:11px; color:var(--muted); font-style:italic; margin-bottom:12px; }}
  .recomendacoes ul {{ margin:0; padding-left:18px; font-size:13px; line-height:1.7; }}
  footer {{ color:var(--muted); font-size:12px; text-align:center; margin-top:20px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Relatório de Análise de Crédito — Base de Clientes</h1>
  <div class="subtitle">Dados fictícios (Mockaroo) processados via SQL Server + Python/Pandas</div>

  <div class="cards">
    <div class="card"><div class="label">Total de clientes</div><div class="value">{total}</div></div>
    <div class="card"><div class="label">Risco baixo</div><div class="value" style="color:var(--baixo)">{contagem.get("Baixo",0)}</div></div>
    <div class="card"><div class="label">Risco alto</div><div class="value" style="color:var(--alto)">{contagem.get("Alto",0)}</div></div>
    <div class="card"><div class="label">Renda média</div><div class="value">R$ {formatar_moeda(resumo["renda_media"])}</div></div>
  </div>

  <div class="grid-2">
    <section>
      <h2>% risco Alto, por faixa etária</h2>
      <div class="desc">Média geral: {media_geral_risco_alto}%</div>
      <div class="chart">
        {barras_idade}
      </div>
      {insights_idade}
    </section>

    <section>
      <h2>% risco Alto, por faixa de renda</h2>
      <div class="desc">Média geral: {media_geral_risco_alto}%</div>
      <div class="chart">
        {barras_renda}
      </div>
      {insights_renda}

      <div class="recomendacoes">
        <div class="recomendacoes-header"><span>📋</span><span>Possíveis ações — práticas gerais do setor de crédito</span></div>
        <div class="recomendacoes-disclaimer">Sugestões genéricas de mercado, não conclusões estatísticas deste dataset (sintético).</div>
        <ul>
          <li>Limites iniciais mais conservadores para faixas de renda mais baixa, com revisão gradual</li>
          <li>Monitorar uso do limite com alertas proativos antes de níveis críticos</li>
          <li>Parcelamento mais flexível, reduzindo comprometimento mensal da renda</li>
        </ul>
      </div>
    </section>
  </div>

  <section>
    <h2>Top 10 clientes de maior risco</h2>
    <table>
      <tr><th>Nome</th><th>Idade</th><th>Estado</th><th>Renda</th><th>Score</th><th>Classificação</th></tr>
      {linhas_top10}
    </table>
  </section>

  <footer>Relatório gerado com Python + Pandas + SQL Server · Score é uma fórmula própria, didática</footer>
</div>
</body>
</html>'''

with open("relatorio_final.html", "w", encoding="utf-8") as arquivo:
    arquivo.write(html_final)

print("Relatório gerado: relatorio_final.html")