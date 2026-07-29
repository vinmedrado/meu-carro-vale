# mcv-data-engine

Motor de dados do Meu Carro Vale.

## Visão geral

Este módulo recebe, normaliza, valida, deduplica e exporta dados automotivos para alimentar valuation, comparáveis, liquidez e inteligência regional.

## Papel no ecossistema

- o produto principal continua sendo o Meu Carro Vale;
- este diretório concentra a infraestrutura de dados;
- o foco aqui é ingestão estruturada, qualidade, snapshots e exportação.

## Capacidades

- ingestão via CSV, JSON e lotes;
- normalização automotiva com aliases e heurísticas;
- detecção de duplicidade com `duplicate_confidence_score`;
- cálculo de liquidez e indicadores de mercado;
- Comparable Intelligence Engine com explicação e impacto no preço;
- API FastAPI;
- painel operacional interno em Streamlit;
- exportação em CSV e Parquet quando disponível.

## Estrutura

```text
mcv-data-engine/
  api/
  collectors/
  comparables/
  config/
  dashboard/
  deduplication/
  ingestion/
  liquidity/
  normalizers/
  snapshots/
  storage/
  tests/
```

## Execução local

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python cli.py init-db
```

### API

```bash
uvicorn api.main:app --reload --port 8020
```

### Painel operacional

```bash
streamlit run dashboard/operational_dashboard.py
```

## TODO

- documentar os endpoints e payloads finais;
- registrar exemplos reais de entrada e saída;
- definir licença e guia de contribuição.
