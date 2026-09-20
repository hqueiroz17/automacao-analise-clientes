# Automação de Análise e Relatório de Clientes

Pipeline de engenharia de dados que consome uma API de dados sintéticos, carrega em um banco relacional (SQL Server), calcula um score de risco de crédito em Python/Pandas, e gera automaticamente um relatório em HTML publicado como site estático na AWS.

**Relatório publicado:** http://relatorio-analise-clientes-hugoqueiroz.s3-website-sa-east-1.amazonaws.com

## Arquitetura

```
API (Mockaroo)
    ↓
Extração via Python (requests) → clientes.csv / financeiro.csv
    ↓
Carga no SQL Server (pyodbc)
    ↓
JOIN + Window Functions (SQL) → traz resultado consolidado para o Pandas
    ↓
Cálculo de score de risco + classificação (Python)
    ↓
Geração do relatório (HTML, via Python)
    ↓
Publicação como site estático (AWS S3)
```

## Sobre os dados

Os dados são **sintéticos**, gerados via [Mockaroo](https://www.mockaroo.com), simulando duas tabelas relacionadas por `cliente_id`:

- **clientes**: nome, idade, cidade, estado
- **financeiro**: renda mensal, dívida total, atrasos nos últimos 12 meses, limite de crédito atual

Dado real de crédito é informação sensível, protegida por LGPD — dados sintéticos permitem demonstrar a arquitetura e a lógica de análise sem envolver informação real de terceiros.

## Estrutura do repositório

```
automacao-analise-clientes/
├── README.md
├── .env                    (não versionado — credenciais)
├── .gitignore
├── extracao/
│   └── extrai_clientes.py       # consome a API do Mockaroo, salva CSVs
├── carga/
│   └── carrega_sql_server.py    # carrega os CSVs nas tabelas do SQL Server
├── analise/
│   └── analise_risco.py         # JOIN + window functions, cálculo de score
└── relatorio/
    ├── gerar_relatorio.py       # gera o relatório HTML a partir do resumo
    └── publica_s3.py            # publica o relatório no S3
```

## Tecnologias

- **Python** — extração via API, carga no banco, cálculo de score, geração do relatório
- **Pandas** — estruturação e cálculos sobre os dados
- **SQL Server** — armazenamento relacional, JOIN e window functions (`RANK`, `AVG() OVER (PARTITION BY...)`)
- **AWS S3** — hospedagem do relatório final como site estático
- **Git/GitHub** — versionamento
- **python-dotenv** — gerenciamento seguro de credenciais (API key, senha do banco, chaves AWS)

## Por que script Python, em vez de notebook

O projeto foi desenhado como uma **automação de ponta a ponta** (API → banco → análise → relatório → publicação), não como uma exploração interativa de dados. Scripts `.py` são o padrão para esse tipo de pipeline, que roda do início ao fim sem intervenção manual — diferente de notebooks, mais adequados para análise exploratória célula a célula.

## Sobre o cálculo do score de risco

O score é uma fórmula própria e didática (não é um modelo de crédito real), combinando três fatores: relação dívida/renda, quantidade de atrasos nos últimos 12 meses, e uso do limite de crédito disponível.

Como os dados são sintéticos (gerados aleatoriamente via API), os primeiros pesos testados geravam uma distribuição irreal — mais da metade da base caindo em "Alto risco". Para corrigir isso, os pesos foram recalibrados por simulação estatística: testamos a fórmula contra uma amostra com os mesmos ranges de valores do dataset, ajustando os pesos até a distribuição final ficar próxima do que se espera em uma carteira de crédito real (maioria dos clientes em risco baixo/médio, minoria em risco alto).

**Limitação conhecida:** como dívida e limite de crédito foram gerados de forma independente e aleatória, o "uso do limite" pode ultrapassar 100% para alguns clientes — algo raro em uma carteira real, onde o limite normalmente é definido em função da capacidade de pagamento.

## Valor para o negócio

Simulando o cenário real descrito pela equipe (análise de score de clientes para apoiar decisões de crédito/financiamento), este pipeline entregaria:

1. **Padronização da análise de risco** — em vez de avaliar cada cliente manualmente, o score e a classificação são calculados de forma consistente para toda a base, reduzindo variação e viés entre analistas.
2. **Identificação de segmentos prioritários** — a segmentação por faixa de renda e idade permite direcionar políticas de crédito diferenciadas (ex: limites mais conservadores para segmentos de maior risco).
3. **Relatório pronto para decisão, sem trabalho manual** — o relatório HTML é gerado automaticamente a partir do dado bruto, eliminando a necessidade de montar planilhas ou apresentações manualmente a cada análise.
4. **Rastreabilidade** — por rodar em camadas (extração → banco relacional → análise → relatório), cada etapa pode ser auditada e reexecutada de forma independente.
5. **Escalabilidade** — a mesma lógica aplicada a 1.000 clientes fictícios se aplica, sem alteração estrutural, a uma base real de qualquer tamanho.

**Importante:** como os dados são sintéticos, os valores e proporções apresentados não representam uma carteira de crédito real — o valor demonstrado é o do **processo e da arquitetura**, replicável a dados verdadeiros.

## Desafios técnicos e soluções

| Desafio | Solução |
|---|---|
| Tipos `numpy` (`int64`, `float64`) incompatíveis com o driver do SQL Server | Conversão explícita para `int`/`float`/`str` puros do Python antes de cada inserção |
| Transação desfeita após erro de inserção, apagando a tabela recém-criada | Adição de `commit()` logo após o `CREATE TABLE`, garantindo que a criação persista mesmo se a inserção falhar depois |
| Script não podia ser executado mais de uma vez sem duplicar dados | Verificação `COUNT(*) == 0` antes de inserir, tornando a carga idempotente |
| Campo "estado" vindo inconsistente da API (o tipo padrão do Mockaroo gerava siglas de qualquer país do mundo) | Troca para um campo Custom List, com as 27 siglas de estado brasileiras reais |
| Distribuição de risco irreal (mais de 50% da base em "Alto risco") | Recalibração dos pesos da fórmula de score por simulação estatística contra uma amostra representativa |
| Linha de referência (média) desalinhada visualmente das barras no relatório HTML | Reposicionamento da linha para dentro do mesmo elemento de referência da barra, usando a mesma unidade de porcentagem |
| Inconsistência entre a cor de destaque da barra e o texto do insight gerado | Unificação da mesma regra (diferença > 5 pontos percentuais) nos dois lugares do código |

## Possíveis evoluções (fora do escopo atual)

- Substituir a API do Mockaroo por uma fonte de dados de crédito real (respeitando LGPD e contratos de acesso), mantendo a mesma arquitetura
- Migrar o SQL Server local para um serviço gerenciado em nuvem (ex: Azure SQL, Amazon RDS)
- Orquestração automatizada do pipeline completo (extração → carga → análise → relatório → publicação), sem intervenção manual
- Substituir a fórmula didática de score por um modelo estatístico ou de machine learning treinado com dados históricos reais
- Testes automatizados e CI/CD, validando o pipeline a cada mudança de código
- Alertas automáticos quando um cliente ultrapassar um limite de risco crítico

## Autor

Hugo Queiroz